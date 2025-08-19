from odoo import models, fields, api
import uuid


class StoreLocation(models.Model):
    _name = 'store.location'
    _description = 'Store Location'
    _rec_name = 'code'

    code = fields.Char(
        string="Reference",
        copy=False,
        index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('store.location.reference')
     )


    batch_ids = fields.One2many('store.batch', 'location_id', string="Store Batches")
    branch_id = fields.Many2one('store.branch', string="Branch")
