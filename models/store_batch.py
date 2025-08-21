from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class StoreBatch(models.Model):
    _name = 'store.batch'
    _description = 'Store Batch in Store'
    _rec_name = 'name'

    name = fields.Char(string="Batch Name", 
                        copy=False,
                        index=True,
                        required=True,
                        default=lambda self: self.env['ir.sequence'].next_by_code('store.batch.name'))
    product_id = fields.Many2one('product.product', string="Product", required=True)
    branch_id = fields.Many2one('store.branch', string="Branch", required=True)
    location_id = fields.Many2one('store.location', string="Location", required=True,domain="[('branch_id', '=', branch_id)]")
    start_time = fields.Datetime(
        string="Start Time",
        default=fields.Datetime.now,
        readonly=True
    )
    end_time = fields.Datetime(string="End Time", readonly=True)
    consumed_qty = fields.Float(string="Consumed Quantity", store=True)
    earned_amount = fields.Float(string="Earned Amount", store=True)
    
    active = fields.Boolean(string="Active", default=True, required=True, readonly=True)

     # Add this field
    processed_order_ids = fields.Many2many(
        'pos.order',
        'store_batch_pos_order_rel',  # relation table name
        'batch_id',
        'order_id',
        string='Processed Orders'
    )


    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.location_id = False


    
    @api.model
    def run_batch_consumption_tracker(self):
        active_batches = self.search([('active', '=', True)])
        for batch in active_batches:
            location = batch.location_id
            branch = location.branch_id

            if not branch or not location:
                continue  # Skip if location or branch is missing

            sessions = branch.pos_session_ids
            start_time = batch.start_time
            product = batch.product_id

            relevant_orders = self.env['pos.order'].search([
                ('session_id', 'in', sessions.ids),
                ('date_order', '>=', start_time),
                ('state', '=', 'paid'),
                ('id', 'not in', batch.processed_order_ids.ids),
            ])

            consumed = 0.0
            earned = 0.0
            newly_processed_orders = []

            for order in relevant_orders:
                for line in order.lines:
                    if line.product_id == product:
                        consumed += line.qty
                        earned += line.price_subtotal
                        newly_processed_orders.append(order.id)

            # Update batch totals
            batch.consumed_qty += consumed
            batch.earned_amount += earned

            # Mark orders as processed
            if newly_processed_orders:
                batch.processed_order_ids = [(4, oid) for oid in newly_processed_orders]
    

    @api.model
    def create(self, vals):
        location_id = vals.get('location_id')
        product_id = vals.get('product_id')
    
        if location_id and product_id:
            location = self.env['store.location'].browse(location_id)
            branch_id = location.branch_id.id
            vals['consumed_qty'] = 0
            vals['earned_amount'] = 0
            # Deactivate conflicting batches in the same branch
            conflicting_batches = self.search([
                ('active', '=', True),
                ('location_id.branch_id', '=', branch_id),
                '|',
                ('location_id', '=', location_id),
                ('product_id', '=', product_id),
            ])
            conflicting_batches.write({'active': False})

        return super(StoreBatch, self).create(vals)
    
    
   

    def write(self, vals):

        if self.env.context.get('skip_conflict_check'):
            return super(StoreBatch, self).write(vals)
    
        location_id = vals.get('location_id')
        product_id = vals.get('product_id')

        # If 'active' is being set to False and end_time is not already set
        if 'active' in vals and vals['active'] is False:
            for record in self:
                if not record.end_time:
                    vals['end_time'] = datetime.now()

        location = self.env['store.location'].browse(location_id)
        branch_id = location.branch_id.id

        # Deactivate other conflicting batches in the same branch
        conflicting_batches = self.search([
            ('id', '!=', self.id),
            ('active', '=', True),
            ('location_id.branch_id', '=', branch_id),
            '|',
            ('location_id', '=', location_id),
            ('product_id', '=', product_id),
        ])
        conflicting_batches.with_context(skip_conflict_check=True).write({
            'active': False,
            'end_time': datetime.now()
        })
                 
        return super(StoreBatch, self).write(vals)




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



