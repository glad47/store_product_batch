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

    active = fields.Boolean(string="Active", default=True, required=True)



    @api.model
    def create(self, vals):
        location_id = vals.get('location_id')
        product_id = vals.get('product_id')
        if location_id and product_id:
            product = self.env['product.product'].browse(product_id)
            on_hand_qty = product.qty_available

            # quants = self.env['stock.quant'].search([
            #     ('product_id', '=', product_id)
            # ])
            print("***********************************************")
            print("***********************************************")
            print(on_hand_qty) 
            initial_qty = on_hand_qty
            vals['initial_qty'] = initial_qty
            self.search([
                ('location_id', '=', location_id),
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




    @api.depends('initial_qty', 'current_qty')
    def _compute_consumed_qty(self):
        for batch in self:
            batch.consumed_qty = batch.initial_qty - batch.current_qty



    def update_current_qty(self):
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
          
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
                raise ValidationError(_("You cannot reactivate a batch that has already ended."))


