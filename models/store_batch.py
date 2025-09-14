from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
import logging
import re


_logger = logging.getLogger(__name__)

class StoreBatch(models.Model):
    _name = 'store.batch'
    _description = 'Store Batch in Store'
    _rec_name = 'name'
# default=lambda self: self.env['ir.sequence'].next_by_code('store.batch.name')
    name = fields.Char(string="Batch Name", 
                        copy=False,
                        index=True,
                        required=True)
    product_ids = fields.Many2many(
        'product.product',
        'store_batch_product_rel',
        'batch_id',
        'product_id',
        string="Products",
        required=True
    )

    location_ids = fields.Many2many(
        'store.location',
        'store_batch_location_rel',
        'batch_id',
        'location_id',
        string="Locations",
        required=True,
        domain="[('branch_id', '=', branch_id)]"
    )

    branch_id = fields.Many2one('store.branch', string="Branch", required=True)
    start_time = fields.Datetime(
        string="Start Time",
        default=fields.Datetime.now,
        readonly=True
    )
    end_time = fields.Datetime(string="End Time", readonly=True)

    consumed_qty = fields.Float(
        string="Total Consumed Quantity",
        compute="_compute_totals",
        store=True
    )

    earned_amount = fields.Float(
        string="Total Earned Amount",
        compute="_compute_totals",
        store=True
    )
    
    active = fields.Boolean(string="Active", default=True, required=True)

     # Add this field
    processed_order_ids = fields.Many2many(
        'pos.order',
        'store_batch_pos_order_rel',  # relation table name
        'batch_id',
        'order_id',
        string='Processed Orders'
    )




    batch_line_ids = fields.One2many(
        'store.batch.line',
        'batch_id',
        string="Batch Lines"
    )

    

 
    @api.onchange('branch_id')
    def _onchange_batch_name(self):
        if self.branch_id:
            count = self.env['store.batch'].search_count([('branch_id', '=', self.branch_id.id)])
            next_number = str(count + 1).zfill(6)
            self.name = f"{self.branch_id.batch_prefix}{next_number}"







    

    @api.depends('batch_line_ids.consumed_qty', 'batch_line_ids.earned_amount', 'product_ids')
    def _compute_totals(self):
        for batch in self:
            batch.consumed_qty = sum(batch.batch_line_ids.mapped('consumed_qty'))
            batch.earned_amount = sum(batch.batch_line_ids.mapped('earned_amount'))


    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.location_ids = [(5, 0, 0)]



    
    
    @api.model
    def run_batch_consumption_tracker(self):
        print("Starting batch consumption tracker...")

        active_batches = self.search([('active', '=', True)])
        print("Found %d active batches" % len(active_batches))

        for batch in active_batches:
            print("Processing batch: %s (ID: %s)" % (batch.name, batch.id))

            branch = batch.branch_id
            if not branch:
                print("Batch %s has no branch assigned. Skipping." % batch.name)
                continue

            pos_ids = branch.pos_ids
            print("Branch %s has %d POS configs" % (branch.name, len(pos_ids)))

            start_time = batch.start_time

            # Filter only active lines
            lines = batch.batch_line_ids
            if not lines:
                print("Batch %s has no active batch lines. Skipping." % batch.name)
                continue

            print("************************")
            print("Already processed order IDs:", batch.processed_order_ids.ids)
            print("*****************************")
            print("POS Configs:", pos_ids.ids)

            # Get all sessions for those POS configs
            sessions = self.env['pos.session'].search([
                ('config_id', 'in', pos_ids.ids)
            ])
            session_ids = sessions.ids

            # Get relevant orders
            relevant_orders = self.env['pos.order'].search([
                ('session_id', 'in', session_ids),
                ('date_order', '>=', start_time),
                ('state', '=', 'invoiced'),
                ('id', 'not in', batch.processed_order_ids.ids),
            ])
            print("Found %d relevant POS orders for batch %s" % (len(relevant_orders), batch.name))

            # Accumulate per-line totals
            line_map = {}

            for order in relevant_orders:
                print("Processing order ID: %s" % order.id)

                for line in order.lines:
                    for batch_line in lines:
                        if batch_line.counted:
                            print("inide active working on it ")
                            print(batch_line.product_id)
                            print(line.product_id)
                            print(line.product_id == batch_line.product_id)
                            if line.product_id == batch_line.product_id:
                                key = batch_line.id
                                if key not in line_map:
                                    line_map[key] = {'qty': 0.0, 'amount': 0.0, 'order_ids': set()}

                                line_map[key]['qty'] += line.qty
                                line_map[key]['amount'] += line.price_subtotal
                                line_map[key]['order_ids'].add(order.id)
                                batch_line.log_daily_consumption(line.qty, line.price_subtotal)

                                print(
                                    "BatchLine %s matched product %s: +%s qty, +%s amount" % (
                                        batch_line.id,
                                        line.product_id.display_name,
                                        line.qty,
                                        line.price_subtotal
                                    )
                                )

            # Apply updates
            for line_id, data in line_map.items():
                line = self.env['store.batch.line'].browse(line_id)
                print(
                    "Updating BatchLine ID %s: +%s qty, +%s amount (before: %s qty, %s amount)" % (
                        line_id, data['qty'], data['amount'], line.consumed_qty, line.earned_amount
                    )
                )
                line.consumed_qty += data['qty']
                line.earned_amount += data['amount']

            # Mark processed orders
            all_processed_ids = set()
            for data in line_map.values():
                all_processed_ids.update(data['order_ids'])

            if all_processed_ids:
                batch.processed_order_ids = [(4, oid) for oid in all_processed_ids]
                print("Marked %d orders as processed for batch %s" % (len(all_processed_ids), batch.name))

        print("Batch consumption tracker completed.")


    @api.model
    def create(self, vals):
        # Generate batch name if not provided
        if not vals.get('name') and vals.get('branch_id'):
            branch = self.env['store.branch'].browse(vals['branch_id'])
            count = self.env['store.batch'].search_count([('branch_id', '=', branch.id)])
            next_number = str(count + 1).zfill(6)
            vals['name'] = f"{branch.batch_prefix}{next_number}"

        # Create the batch record
        batch = super().create(vals)

        # Auto-generate batch lines for each product
        product_ids = batch.product_ids
        lines = []
        for product in product_ids:
            lines.append((0, 0, {
                'product_id': product.id,
                'batch_id': batch.id,
                'consumed_qty': 0.0,
                'earned_amount': 0.0,
                'counted': True,
            }))

        if lines:
            batch.write({'batch_line_ids': lines})

        return batch


    # @api.model
    # def create(self, vals):
    #     batch = super().create(vals)

    #     product_ids = batch.product_ids
    #     # location_ids = batch.location_ids
          
    #     lines = []
    #     for product in product_ids:
    #         lines.append((0, 0, {
    #                 'product_id': product.id,
    #                 'batch_id': batch.id,
    #                 'consumed_qty': 0.0,
    #                 'earned_amount': 0.0,
    #                 'counted':True,
    #             }))
                

    #     if lines:
    #         batch.write({'batch_line_ids': lines})

    #     return batch

    # @api.model
    # def create(self, vals):
    #     location_id = vals.get('location_id')
    #     product_id = vals.get('product_id')
    
    #     if location_id and product_id:
    #         location = self.env['store.location'].browse(location_id)
    #         branch_id = location.branch_id.id
    #         vals['consumed_qty'] = 0
    #         vals['earned_amount'] = 0
    #         # Deactivate conflicting batches in the same branch
    #         conflicting_batches = self.search([
    #             ('active', '=', True),
    #             ('location_id.branch_id', '=', branch_id),
    #             '|',
    #             ('location_id', '=', location_id),
    #             ('product_id', '=', product_id),
    #         ])
    #         conflicting_batches.write({'active': False})

    #     return super(StoreBatch, self).create(vals)
    
    
   
    # @api.model
    # def create(self, vals):
    #     product_ids = vals.get('product_ids', [(6, 0, [])])[0][2] if vals.get('product_ids') else []
    #     location_ids = vals.get('location_ids', [(6, 0, [])])[0][2] if vals.get('location_ids') else []

    #     vals['consumed_qty'] = 0
    #     vals['earned_amount'] = 0

    #     if product_ids and location_ids:
    #         conflicting_batches = self.search([
    #             ('active', '=', True),
    #             '|',
    #             ('product_ids', 'in', product_ids),
    #             ('location_ids', 'in', location_ids),
    #         ])
    #         conflicting_batches.write({'active': False})

    #     return super(StoreBatch, self).create(vals)

    # def write(self, vals):
    #     if self.env.context.get('skip_conflict_check'):
    #         return super(StoreBatch, self).write(vals)

    #     for record in self:
    #         location_id = vals.get('location_id') or record.location_id.id
    #         product_id = vals.get('product_id') or record.product_id.id

    #         if 'active' in vals and vals['active'] is False and not record.end_time:
    #             record.end_time = datetime.now()

    #         location = self.env['store.location'].browse(location_id)
    #         branch_id = location.branch_id.id

    #         conflicting_batches = self.search([
    #             ('id', '!=', record.id),
    #             ('active', '=', True),
    #             ('location_id.branch_id', '=', branch_id),
    #             '|',
    #             ('location_id', '=', location_id),
    #             ('product_id', '=', product_id),
    #         ])
    #         conflicting_batches.with_context(skip_conflict_check=True).write({
    #             'active': False,
    #             'end_time': datetime.now()
    #         })

    #     return super(StoreBatch, self).write(vals)

    # def write(self, vals):
    #     if self.env.context.get('skip_conflict_check'):
    #         return super(StoreBatch, self).write(vals)

    #     for record in self:
    #         product_ids = vals.get('product_ids') or record.product_ids.ids
    #         location_ids = vals.get('location_ids') or record.location_ids.ids

    #         if 'active' in vals and vals['active'] is False and not record.end_time:
    #             record.end_time = datetime.now()

    #         conflicting_batches = self.search([
    #             ('id', '!=', record.id),
    #             ('active', '=', True),
    #             '|',
    #             ('product_ids', 'in', product_ids),
    #             ('location_ids', 'in', location_ids),
    #         ])
    #         conflicting_batches.with_context(skip_conflict_check=True).write({
    #             'active': False,
    #             'end_time': datetime.now()
    #         })

    #     return super(StoreBatch, self).write(vals)

    def write(self, vals):
        res = super().write(vals)

        for batch in self:
            # Handle active → end_time logic
            if 'active' in vals:
                if vals['active']:
                    batch.end_time = False  # Clear end_time when activating
                else:
                    batch.end_time = fields.Datetime.now()  # Set end_time when deactivating

            # Sync product lines
            new_products = batch.product_ids
            new_product_ids = set(new_products.ids)

            # Pass 1: Update existing lines
            for line in batch.batch_line_ids:
                if line.product_id.id in new_product_ids:
                    if not line.counted:
                        line.counted = True
                else:
                    if line.counted:
                        line.counted = False

            # Pass 2: Add missing lines
            existing_product_ids = set(line.product_id.id for line in batch.batch_line_ids)
            missing_product_ids = new_product_ids - existing_product_ids

            new_lines = []
            for product_id in missing_product_ids:
                new_lines.append((0, 0, {
                    'product_id': product_id,
                    'batch_id': batch.id,
                    'consumed_qty': 0.0,
                    'earned_amount': 0.0,
                    'counted': True,
                }))

            if new_lines:
                batch.write({'batch_line_ids': new_lines})

        return res




    @api.depends('initial_qty', 'current_qty', 'active')
    def _compute_consumed_qty(self):
        for batch in self:
            if batch.active:
                batch.consumed_qty = batch.initial_qty - batch.current_qty

        

        


    @api.constrains('active', 'end_time')
    def _check_reactivation(self):
        for rec in self:
            if rec.active and rec.end_time:
                raise ValidationError(_("You cannot reactivate a store batch that has already ended."))


    

    def action_refresh_batches_info(self):
        self.run_batch_consumption_tracker()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }



