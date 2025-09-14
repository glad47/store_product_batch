from odoo import models, fields, api
from datetime import datetime

class StoreBatchLineDaily(models.Model):
    _name = 'store.batch.line.daily'
    _description = 'Daily Consumption Log for Batch Line'

    date = fields.Date(string="Date", required=True, default=fields.Date.today)
    consumed_qty = fields.Float(string="Consumed Quantity", default=0.0)
    earned_amount = fields.Float(string="Earned Amount", default=0.0)
    batch_line_id = fields.Many2one('store.batch.line', string="Batch Line", required=True)


    _sql_constraints = [
        ('unique_daily_entry', 'unique(batch_line_id, date)', 'Only one daily record per batch line per day is allowed.')
    ]
