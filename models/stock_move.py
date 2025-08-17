from odoo import models

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self):
        res = super()._action_done()
        affected_products = self.mapped('product_id')
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print(affected_products)
        self.env['store.batch'].search([
            ('product_id', 'in', affected_products.ids),
            ('active', '=', True)
        ]).update_current_qty()  
        return res
