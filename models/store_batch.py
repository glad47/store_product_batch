from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class StoreBatch(models.Model):
    _name = 'store.batch'
    _description = 'Store Batch in Store'
    _rec_name = 'name'

    name = fields.Char(string="Batch Name", required=True)
    product_id = fields.Many2one('product.product', string="Product", required=True)
    location_id = fields.Many2one('store.location', string="Location", required=True)
    start_time = fields.Datetime(
        string="Start Time",
        default=fields.Datetime.now,
        readonly=True
    )
    end_time = fields.Datetime(string="End Time", readonly=True)
    initial_qty = fields.Float(string="Initial Quantity", readonly=True)
    current_qty = fields.Float(string="Current Quantity", readonly=True)
    consumed_qty = fields.Float(string="Consumed Quantity", compute="_compute_consumed_qty", store=True)
    earned_amount = fields.Float(string="Earned Amount", compute="_compute_earned_amount", store=True)
    active = fields.Boolean(string="Active", default=True, required=True)



    @api.model
    def create(self, vals):
        location_id = vals.get('location_id')
        product_id = vals.get('product_id')
        active = vals.get('active')
        if not active:
            raise ValidationError(_("You cannot create a batch that is not active."))

        if location_id and product_id:
            product = self.env['product.product'].browse(product_id)
            on_hand_qty = product.qty_available
            vals['initial_qty'] = on_hand_qty
            vals['current_qty'] = on_hand_qty
            self.search([
                '|',
                ('location_id', '=', location_id),
                ('product_id', '=', product_id),
                ('active', '=', True)
            ]).write({'active': False})
        return super(StoreBatch, self).create(vals)

    def write(self, vals):
        # If 'active' is being set to False and end_time is not already set
        if 'active' in vals and vals['active'] is False:
            for record in self:
                if not record.end_time:
                    vals['end_time'] = datetime.now()
        return super(StoreBatch, self).write(vals)




    @api.depends('initial_qty', 'current_qty', 'active')
    def _compute_consumed_qty(self):
        for batch in self:
            if batch.active:
                batch.consumed_qty = batch.initial_qty - batch.current_qty


    @api.depends('consumed_qty', 'active')
    def _compute_earned_amount(self):
        for batch in self:
            if batch.active and batch.product_id:
                product = self.env['product.product'].browse(batch.product_id.id)
                batch.earned_amount = batch.consumed_qty * product.lst_price
        



    def update_current_qty(self):       
        for batch in self:
            print(batch.product_id)
            product = self.env['product.product'].browse(batch.product_id.id)
            on_hand_qty = product.qty_available
            print("update_current_qty   on_hand_qty")
            print(on_hand_qty)
            # quants = self.env['stock.quant'].search([
            #     ('product_id', '=', batch.product_id.id)
            # ])
            batch.current_qty = on_hand_qty
        


    @api.constrains('active', 'end_time')
    def _check_reactivation(self):
        for rec in self:
            if rec.active and rec.end_time:
                raise ValidationError(_("You cannot reactivate a store batch that has already ended."))


