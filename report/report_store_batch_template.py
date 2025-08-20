from odoo import models, api
from datetime import datetime

class StoreBatchReport(models.AbstractModel):
    _name = 'report.store_product_batch.report_store_batch_template'
    _description = 'Store Batch Summary Report'



    @api.model
    def _get_report_values(self, docids, data=None):
        batches = self.env['store.batch'].search(['|', ('active', '=', False) , ('active', '=', True)])

        branch_summaries = []

        # Group batches by branch
        branches = {}
        for batch in batches:
            branch = batch.location_id.branch_id
            if not branch:
                continue  # Skip if no branch linked
            if branch.id not in branches:
                branches[branch.id] = {
                    'branch_name': branch.name,
                    'total_consumed': 0.0,
                    'total_earned': 0.0,
                    'location_by_qty': {},
                    'location_by_earned': {},
                    'product_summary': {},
                    'batches': [],
                }

            summary = branches[branch.id]
            loc = batch.location_id.code
            prod = batch.product_id.name
            consumed = batch.consumed_qty or 0.0
            earned = batch.earned_amount or 0.0

            summary['total_consumed'] += consumed
            summary['total_earned'] += earned
            summary['location_by_qty'][loc] = summary['location_by_qty'].get(loc, 0.0) + consumed
            summary['location_by_earned'][loc] = summary['location_by_earned'].get(loc, 0.0) + earned
            summary['product_summary'][prod] = summary['product_summary'].get(prod, 0.0) + consumed
            summary['batches'].append(batch)

        # Convert dict to sorted list
        branch_summaries = []
        for branch_id, summary in branches.items():
            summary['location_by_qty'] = sorted(summary['location_by_qty'].items(), key=lambda x: x[1], reverse=True)
            summary['location_by_earned'] = sorted(summary['location_by_earned'].items(), key=lambda x: x[1], reverse=True)
            summary['product_summary'] = sorted(summary['product_summary'].items(), key=lambda x: x[1], reverse=True)
            branch_summaries.append(summary)

        return {
            'doc_ids': docids,
            'doc_model': 'store.batch',
            'docs': batches,
            'data': {
                'branches': branch_summaries
            }
        }
