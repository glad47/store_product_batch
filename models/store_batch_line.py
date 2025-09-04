from odoo import models, fields, api

class StoreBatchLine(models.Model):
    _name = 'store.batch.line'
    _description = 'Product Consumption in Store Batch'

    batch_id = fields.Many2one('store.batch', string="Batch", required=True)
    product_id = fields.Many2one('product.product', string="Product", required=True)
    consumed_qty = fields.Float(string="Consumed Quantity", required=True)
    earned_amount = fields.Float(string="Earned Amount")
    counted = fields.Boolean(string="Active",required=True, default=True)
    

