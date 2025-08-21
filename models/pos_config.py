from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'
    branch_id = fields.Many2one('store.branch', string='Store Branch')
