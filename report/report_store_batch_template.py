from odoo import models, api
from datetime import datetime

class StoreBatchReport(models.AbstractModel):
    _name = 'report.store_product_batch.report_store_batch_template'
    _description = 'Store Batch Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        batches = self.env['store.batch'].search([])

        location_by_qty = {}     
        location_by_earned = {}
        product_summary = {}
        time_summary_by_location  = {}
        earned_by_location_hour = {}

        for batch in batches:
            loc = batch.location_id.name
            consumed = batch.consumed_qty or 0
            hour = batch.start_time.strftime('%H') if batch.start_time else 'Unknown'
            earned = batch.earned_amount or 0

            # Location by consumed quantity
            location_by_qty[loc] = location_by_qty.get(loc, 0) + consumed

            # Location by earned amount
            location_by_earned[loc] = location_by_earned.get(loc, 0) + earned

            # Product summary
            prod = batch.product_id.name
            product_summary[prod] = product_summary.get(prod, 0) + consumed

            # Time summary per location
            if loc not in time_summary_by_location:
                time_summary_by_location[loc] = {}
            
            time_summary_by_location[loc][hour] = time_summary_by_location[loc].get(hour, 0) + consumed    

            if loc not in earned_by_location_hour:
                earned_by_location_hour[loc] = {}

            earned_by_location_hour[loc][hour] = earned_by_location_hour[loc].get(hour, 0) + earned

        # Sort both summaries
        sorted_by_qty = sorted(location_by_qty.items(), key=lambda x: x[1], reverse=True)
        sorted_by_earned = sorted(location_by_earned.items(), key=lambda x: x[1], reverse=True)

        # Sort the time_by_location (quantity)
        for loc in time_summary_by_location:
            time_by_location_sorted_by_qty = dict(
                sorted(
                    time_summary_by_location[loc].items(),
                    key=lambda item: item[1],  # Sort by quantity
                    reverse=True               # Descending order
                )
            )
            time_summary_by_location[loc] = time_by_location_sorted_by_qty

        # Sort the time_by_location (earned)
        for loc in earned_by_location_hour:
            time_by_location_sorted_by_earned = dict(
                sorted(
                    earned_by_location_hour[loc].items(),
                    key=lambda item: item[1],  # Sort by quantity
                    reverse=True               # Descending order
                )
            )
            earned_by_location_hour[loc] = time_by_location_sorted_by_earned   


        return {
            'doc_ids': docids,
            'doc_model': 'store.batch',
            'docs': batches,
            'data': {
                'location_by_earned': sorted_by_earned,
                'location_by_qty': sorted_by_qty,
                'product_summary': product_summary,
                'time_summary_by_location': time_summary_by_location,
                'earned_by_location_hour':earned_by_location_hour,
            }
        }
