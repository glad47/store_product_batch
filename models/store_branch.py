from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class StoreBranch(models.Model):
    _name = 'store.branch'
    _description = 'Store Branch'
    _rec_name = 'name'

    name = fields.Char(string='Branch Name', required=True)
    active = fields.Boolean(string="Active", default=True)
    pos_session_ids = fields.One2many('pos.session', 'branch_id', string='POS Sessions')
    location_ids = fields.One2many('store.location', 'branch_id', string='Store Locations')


    def unlink(self):
        for record in self:
            if record.active:
                raise ValidationError(_("You must archive the branch before deleting it."))
        return super().unlink()



    
