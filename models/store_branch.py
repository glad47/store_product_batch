from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class StoreBranch(models.Model):
    _name = 'store.branch'
    _description = 'Store Branch'
    _rec_name = 'name'

    name = fields.Char(string='Branch Name', required=True)
    active = fields.Boolean(string="Active", default=True)
    pos_ids = fields.One2many('pos.config', 'branch_id', string='POS')
    location_ids = fields.One2many('store.location', 'branch_id', string='Store Locations')
    location_prefix = fields.Char(string="Location Prefix", default="LOC-", required=True)
    batch_prefix = fields.Char(string="Batch Prefix", default="BAT-", required=True)



    @api.model
    def create(self, vals):
        branch = super().create(vals)
        for location in branch.location_ids:
            location.branch_id = branch.id
        return branch
    
    def write(self, vals):
        res = super().write(vals)
        for branch in self:
            for location in branch.location_ids:
                location.branch_id = branch.id
        return res




    def unlink(self):
        for record in self:
            if record.active:
                raise ValidationError(_("You must archive the branch before deleting it."))
        return super().unlink()



    
