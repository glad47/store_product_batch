from odoo import models, fields, api
import uuid


class StoreLocation(models.Model):
    _name = 'store.location'
    _description = 'Store Location'
    _rec_name = 'code'
    # default=lambda self: self.env['ir.sequence'].next_by_code('store.location.reference')
    code = fields.Char(
        string="Reference",
        copy=False,
        index=True
     )


    batch_ids = fields.One2many('store.batch', 'location_ids', string="Store Batches")
    branch_id = fields.Many2one('store.branch', string="Branch")
    
    
    @api.onchange('branch_id')
    def _onchange_generate_code(self):
        if self.branch_id:
            prefix = self.branch_id.location_prefix
            count = self.env['store.location'].search_count([('branch_id', '=', self.branch_id.id)])
            next_number = str(count + 1).zfill(6)
            self.code = f"{prefix}{next_number}"


    @api.model
    def create(self, vals):
        if not vals.get('code') and vals.get('branch_id'):
            branch = self.env['store.branch'].browse(vals['branch_id'])
            prefix = branch.location_prefix or 'LOC-'
            count = self.env['store.location'].search_count([('branch_id', '=', branch.id)])
            next_number = str(count + 1).zfill(6)
            vals['code'] = f"{prefix}{next_number}"
        return super().create(vals)

        





    
