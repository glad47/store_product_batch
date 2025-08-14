from odoo import models, fields

class StoreBatch(models.Model):
    _name = 'store.batch'
    _description = 'Store Batch in Store'
    _rec_name = 'name'

    name = fields.Char(string="Batch Name", required=True)
    product_id = fields.Many2one('product.product', string="Product", required=True)
    location_id = fields.Many2one('store.location', string="Location", required=True)
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    current_qty = fields.Float(string="Current Quantity")
    approx_qty_left = fields.Float(string="Approximate Quantity Left")
    active = fields.Boolean(string="Active", default=True)
