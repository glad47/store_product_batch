from odoo import models, fields

class PosSession(models.Model):
    _inherit = 'pos.session'

    branch_id = fields.Many2one('store.branch', string='Store Branch')
