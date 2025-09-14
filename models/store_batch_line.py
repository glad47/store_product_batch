from odoo import models, fields, api
from datetime import date, timedelta


class StoreBatchLine(models.Model):
    _name = 'store.batch.line'
    _description = 'Product Consumption in Store Batch'

    batch_id = fields.Many2one('store.batch', string="Batch", required=True)
    product_id = fields.Many2one('product.product', string="Product", required=True)
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

    counted = fields.Boolean(string="Active",required=True, default=True)
    daily_log_ids = fields.One2many(
        'store.batch.line.daily',
        'batch_line_id',
        string="Daily Logs",
        store=True,
    )

    @api.depends('daily_log_ids.consumed_qty', 'daily_log_ids.earned_amount')
    def _compute_totals(self):
        for line in self:
            total_qty = sum(line.daily_log_ids.mapped('consumed_qty'))
            total_amount = sum(line.daily_log_ids.mapped('earned_amount'))
            line.consumed_qty = total_qty
            line.earned_amount = total_amount



    def log_daily_consumption(self, qty, amount):
        # - timedelta(days=1)
        today = date.today()
        for line in self:
            existing_log = self.env['store.batch.line.daily'].search([
                ('batch_line_id', '=', line.id),
                ('date', '=', today)
            ], limit=1)

            if existing_log:
                existing_log.consumed_qty += qty
                existing_log.earned_amount += amount
            else:
                self.env['store.batch.line.daily'].create({
                    'batch_line_id': line.id,
                    'date': today,
                    'consumed_qty': qty,
                    'earned_amount': amount
                })


