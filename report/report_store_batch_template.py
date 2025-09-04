from odoo import models, api, http
from odoo.http import request

from datetime import datetime

class StoreBatchReport(models.AbstractModel):
    _name = 'report.store_product_batch.report_store_batch_template'
    _description = 'Store Batch Summary Report'



    @http.route('/store_product_batch/chart_data', type='json', auth='user')
    def get_chart_data(self, time_dimension='Year'):
        report_model = request.env['report.store_product_batch.report_store_batch_template']
        docids = request.env['store.batch'].search([('active', '=', True)]).ids

        report_data = report_model._get_report_values(docids, {'time_dimension': time_dimension})
        return report_data['data']['chart_option']

    @api.model
    def _get_batch_consumption_data(self, time_dimension='Year'):
        print("##########################")
        batches = self.env['store.batch'].search(['|', ('active', '=', False) , ('active', '=', True)])
        result = []



        for batch in batches:
            time_value = None
            if time_dimension == 'Year':
                time_value = batch.start_time.year if batch.start_time else None
            elif time_dimension == 'Month':
                time_value = batch.start_time.strftime('%b') if batch.start_time else None
            elif time_dimension == 'Week':
                time_value = batch.start_time.strftime('W%U') if batch.start_time else None
            else:
                time_value = batch.start_time.strftime('%Y-%m-%d') if batch.start_time else None

            result.append({
                'Branch': batch.branch_id.name if batch.branch_id else 'Unknown',
                time_dimension: time_value,
                'Consumed Quantity': batch.consumed_qty,
                'Batch': batch.name,
            })

        return result

    


    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        time_dimension = data.get('time_dimension', 'Year')  # Default to 'Year' if not provided

        # Fetch raw batch consumption data — you should implement this method
        raw_data = self._get_batch_consumption_data(time_dimension=time_dimension)

        # Build the report structure using your modular function
        return self.build_batch_consumption_report(
            raw_data=raw_data,
            docids=docids,
            doc_model='store.batch',
            time_dimension=time_dimension
        )


    def build_batch_consumption_report(self, *, raw_data, docids=None, doc_model='store.batch', time_dimension='Year'):
        docids = docids or []

        # Extract unique batches
        batches = list({item['Batch'] for item in raw_data})

        # Prepare dataset filters and series
        dataset_with_filters = []
        series_list = []

        for batch in batches:
            dataset_id = f'dataset_{batch}'
            dataset_with_filters.append({
                'id': dataset_id,
                'fromDatasetId': 'dataset_raw',
                'transform': {
                    'type': 'filter',
                    'config': {
                        'and': [
                            {'dimension': time_dimension, 'gte': 2020},
                            {'dimension': 'Batch', '=': batch}
                        ]
                    }
                }
            })

            series_list.append({
                'type': 'line',
                'datasetId': dataset_id,
                'showSymbol': False,
                'name': batch,
                'endLabel': {
                    'show': True,
                    'formatter': "function(params) { return params.value[2] + ': ' + params.value[1]; }"
                },
                'labelLayout': {'moveOverlap': 'shiftY'},
                'emphasis': {'focus': 'series'},
                'encode': {
                    'x': time_dimension,
                    'y': 'Consumed Quantity',
                    'label': ['Batch', 'Consumed Quantity'],
                    'itemName': time_dimension,
                    'tooltip': ['Consumed Quantity']
                }
            })

        chart_option = {
            'animationDuration': 1000,
            'dataset': [{'id': 'dataset_raw', 'source': raw_data}] + dataset_with_filters,
            'title': {'text': f'Batch Consumption by {time_dimension}'},
            'tooltip': {'order': 'valueDesc', 'trigger': 'axis'},
            'legend': {'top': 'bottom'},
            'xAxis': {'type': 'category', 'name': time_dimension, 'nameLocation': 'middle'},
            'yAxis': {'name': 'Consumed Quantity'},
            'grid': {'right': 140},
            'series': series_list
        }

        # Aggregate branch summaries
        branch_summaries = {}
        for item in raw_data:
            branch = item.get('Branch') or 'Unknown'
            if branch not in branch_summaries:
                branch_summaries[branch] = {
                    'total_qty': 0,
                    'batches': set()
                }
            branch_summaries[branch]['total_qty'] += item.get('Consumed Quantity', 0)
            branch_summaries[branch]['batches'].add(item['Batch'])

        # Convert sets to lists
        for branch in branch_summaries:
            branch_summaries[branch]['batches'] = list(branch_summaries[branch]['batches'])

        return {
            'doc_ids': docids,
            'doc_model': doc_model,
            'docs': batches,
            'data': {
                'chart_option': chart_option,
                'branches': branch_summaries
            }
        }


