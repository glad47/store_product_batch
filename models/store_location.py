from odoo import models, fields, api
import uuid

class StoreLocation(models.Model):
    _name = 'store.location'
    _description = 'Store Location'
    _rec_name = 'name'

    name = fields.Char(string="Location Name", required=True)
    code = fields.Char(
        string="Reference",
        copy=False,
        index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('store.location.reference')
     )


    batch_ids = fields.One2many('store.batch', 'location_id', string="Store Batches")

    # @api.model
    # def create(self, vals):
    #     if not vals.get('code'):
    #         vals['code'] = self.env['ir.sequence'].next_by_code('store.location.reference')
    #     return super(StoreLocation, self).create(vals)

