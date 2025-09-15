from odoo import models, api, http
from odoo.http import request
from collections import defaultdict
import calendar
from builtins import ValueError
from datetime import datetime
import json




class StoreBatchReportProd(http.Controller):
    _name = 'report.store_product_batch.report_store_batch_template_prod'
    _description = 'Store Batch Summary Report'

    MONTH_KEYS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    

    @http.route('/store_product_batch/get_branches_prod', type='json', auth='user', methods=['POST'])
    def get_branches(self):
        branches = request.env['store.branch'].search([('active', '=', True)])
        result = [{'id': b.id, 'name': b.name} for b in branches]
        return {'branches': result}
    

    
    @http.route('/store_product_batch/get_years_prod', type='json', auth='user', methods=['POST'])
    def get_years(self):
        years = request.env['store.batch'].search(['|', ('active', '=', False), ('active', '=', True)]).mapped('start_time')
        unique_years = sorted({dt.year for dt in years if dt})
        return {'years': unique_years}
    

    

    @http.route('/store_product_batch/get_months_prod', type='json', auth='user', methods=['POST'])
    def get_months(self):
        # You can still parse the year if needed for other logic
        data = json.loads(request.httprequest.data)
        # year = data.get('year')

        # Return all 12 months as abbreviated names (Jan, Feb, ..., Dec)
        all_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        return {'months': all_months}
    



    
    @http.route('/store_product_batch/get_days_prod', type='json', auth='user', methods=['POST'])
    def get_days(self):
        data = json.loads(request.httprequest.data)
        year = int(data['year'])
        month_name = data['month']
        month_map = {name: idx for idx, name in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], start=1)}
        month_num = month_map.get(month_name)
        days = list(range(1, calendar.monthrange(year, month_num)[1] + 1))
        return {'days': days}
    


    
    @http.route('/store_product_batch/chart_data_prod', type='json', auth='user', methods=['POST'])
    def get_chart_data(self):
        data = json.loads(request.httprequest.data)
        payload= data['payload']
        branch = payload['branch']
        
        year = payload['year']
        month = payload['month']

        # Determine time_dimension granularity
        if not year and not month:
            time_dimension = 'Year'
        elif year and not month:
            time_dimension = 'Month'
        elif year and month:
            time_dimension = 'Day'
        else:
            time_dimension = 'Year'  # Fallback safety
        
           
        payload["time_dimension"] = time_dimension

        # Fetch all batch records (active and inactive)
        docids = request.env['store.batch'].search([
                                                ('branch_id', '=', branch),
                                                ('active', 'in', [True, False])
                                            ]).ids

        # Get chart data based on resolved time_dimension
        report_data = self._get_report_values(docids, payload)
        return report_data['data']['chart_option']


    


    @api.model
    def _get_report_values(self, docids, data=None):
        return self.build_location_stacked_report(
            docids=docids,
            doc_model='store.batch',
            data=data
        )
    



    

    def build_product_nested_summary(self, time_granularity='total', data={}):
        MONTH_KEYS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        def get_time_key(batch_date):
            if time_granularity == 'year':
                return str(batch_date.year)
            elif time_granularity == 'month':
                return MONTH_KEYS[batch_date.month - 1]
            elif time_granularity == 'day':
                return str(batch_date.day)
            else:
                return 'Total'

        # Add product layer inside summary
        summary = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
            'consumed_qty': 0.0,
            'earned_amount': 0.0
        }))))

        selected_branch = request.env['store.branch'].search([('id', '=', data["branch"])])
        batches = request.env['store.batch'].search([
            ('branch_id', '=', selected_branch.id),
            ('active', 'in', [True, False])
        ])

        for location in selected_branch.location_ids:
            branch_id = selected_branch.id
            location_id = location.id

            if time_granularity == 'day' and data.get("year") and data.get("month"):
                for day in range(1, 32):
                    summary[branch_id][location_id][str(day)]  # triggers default init
            elif time_granularity == 'month' and data.get("year"):
                for month in MONTH_KEYS:
                    summary[branch_id][location_id][month]
            elif time_granularity == 'year':
                year_raw = data.get("year")
                try:
                    current_year = int(year_raw) if year_raw is not None else datetime.now().year
                except (TypeError, ValueError):
                    current_year = datetime.now().year
                summary[branch_id][location_id][str(current_year)]

        for location in selected_branch.location_ids:
            branch_id = selected_branch.id
            location_id = location.id

            for batch in batches:
                if location not in batch.location_ids or not batch.start_time:
                    continue

                batch_year = str(batch.start_time.year)
                batch_month = MONTH_KEYS[batch.start_time.month - 1]

                if time_granularity == 'day':
                    if data.get("year") and data.get("month") and (batch_year != str(data["year"]) or batch_month != data["month"]):
                        continue
                elif time_granularity == 'month':
                    if data.get("year") and batch_year != str(data["year"]):
                        continue

                location_count = len(batch.location_ids)
                if location_count == 0:
                    continue

                time_key = get_time_key(batch.start_time)

                for line in batch.batch_line_ids:
                    product_name = line.product_id.name
                    consumed_qty = line.consumed_qty / location_count
                    earned_amount = line.earned_amount / location_count if line.earned_amount else 0.0

                    summary[branch_id][location_id][time_key][product_name]['consumed_qty'] += consumed_qty
                    summary[branch_id][location_id][time_key][product_name]['earned_amount'] += earned_amount

        result = []
        time_label = {
            'year': 'Year',
            'month': 'Month',
            'day': 'Day'
        }.get(time_granularity, 'Total')

        for branch_id, locations in summary.items():
            branch = request.env['store.branch'].browse(branch_id)
            for location_id, time_data in locations.items():
                location = request.env['store.location'].browse(location_id)
                for time_key, product_data in time_data.items():
                    for product_name, data in product_data.items():
                        if round(data['consumed_qty'], 2) > 0 and round(data['earned_amount'], 2) > 0:
                            result.append({
                                'Branch': branch.name,
                                'Location': location.code,
                                time_label: time_key,
                                'Product': product_name,
                                'Consumed Quantity': round(data['consumed_qty'], 2),
                                'Earned Amount': round(data['earned_amount'], 2)
                            })
            
        return result



    def build_location_product_stacked_report(self, *, docids=None, doc_model='store.batch', data):

        MONTH_KEYS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        granularity_map = {
            'Year': 'year',
            'Month': 'month',
            'Day': 'day'
        }
        time_granularity = granularity_map.get(data['time_dimension'], 'total')

        # Fetch raw product-level data
        raw_data = self.build_product_nested_summary(time_granularity=time_granularity, data=data)

        # Determine time keys
        if data['time_dimension'] == 'Month':
            time_keys = MONTH_KEYS
        elif data['time_dimension'] == 'Day':
            if not data.get('year') or not data.get('month'):
                raise ValueError("Year and month must be provided for daily view.")
            month_map = {name: idx for idx, name in enumerate(MONTH_KEYS, start=1)}
            month_num = month_map.get(data['month'])
            if not month_num:
                raise ValueError(f"Invalid month name: {data['month']}")
            days_in_month = calendar.monthrange(int(data['year']), month_num)[1]
            time_keys = [str(day) for day in range(1, days_in_month + 1)]
        else:
            time_keys = sorted({item.get(data['time_dimension']) for item in raw_data if item.get(data['time_dimension'])})

        # Collect unique products and locations
        products = sorted({item['Product'] for item in raw_data})
        locations = sorted({item['Location'] for item in raw_data})

        # Initialize: time → location → product → qty
        time_location_product_map = {
            t: {
                loc: {prod: 0.0 for prod in products}
                for loc in locations
            }
            for t in time_keys
        }

        # Populate quantities
        for item in raw_data:
            t = item.get(data['time_dimension'])
            loc = item['Location']
            prod = item['Product']
            qty = item.get('Consumed Quantity', 0)
            if t in time_location_product_map and loc in time_location_product_map[t]:
                time_location_product_map[t][loc][prod] += qty

        # Build chart series: one per product, stacked across locations
        emphasis_style = {
            'itemStyle': {
                'shadowBlur': 10,
                'shadowColor': 'rgba(0,0,0,0.3)'
            }
        }

        series = []
        for prod in products:
            series.append({
                'name': prod,
                'type': 'bar',
                'stack': 'total',
                'emphasis': emphasis_style,
                'data': [
                    sum(time_location_product_map[t][loc][prod] for loc in locations)
                    for t in time_keys
                ]
            })

        # Build tabular result with time included
        time_label = data['time_dimension']
        result = []
        for t in time_keys:
            for loc in locations:
                for prod in products:
                    qty = time_location_product_map[t][loc][prod]
                    result.append({
                        time_label: t,
                        'Location': loc,
                        'Product': prod,
                        'Consumed Quantity': round(qty, 2)
                    })

        # Chart configuration
        chart_option = {
            'title': {'text': 'Product Consumption by Time and Location'},
            'tooltip': {'trigger': 'item'},
            'legend': {
                'type': 'scroll',
                'orient': 'horizontal',
                'bottom': 0,
                'data': products
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '10%',
                'containLabel': True
            },
            'toolbox': {
                'feature': {
                    'magicType': {'type': ['stack']},
                    'dataView': {},
                    'saveAsImage': {}
                }
            },
            'brush': {
                'toolbox': ['rect', 'polygon', 'lineX', 'lineY', 'keep', 'clear'],
                'xAxisIndex': 0
            },
            'xAxis': {
                'type': 'category',
                'boundaryGap': True,
                'axisLabel': {
                    'rotate': 45  # or 30, or even 90 if needed
                },
                'data': time_keys,
                
            },
            'yAxis': {'type': 'value'},
            'series': series
        }

        return {
            'doc_ids': docids,
            'doc_model': doc_model,
            'docs': products,
            'data': {
                'chart_option': chart_option,
                'products': products,
                'time_keys': time_keys,
                'result': result
            }
        }
    

    def build_location_stacked_report(self, *, docids=None, doc_model='store.batch', data):
        

        MONTH_KEYS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        granularity_map = {
            'Year': 'year',
            'Month': 'month',
            'Day': 'day'
        }
        time_granularity = granularity_map.get(data['time_dimension'], 'total')

        # Fetch raw product-level data
        raw_data = self.build_product_nested_summary(time_granularity=time_granularity, data=data)

        # Collect unique products and locations
        products = sorted({item['Product'] for item in raw_data})
        locations = sorted({item['Location'] for item in raw_data})

        # Initialize: location → product → qty
        # Initialize dynamically: location → product → qty
        location_product_map = defaultdict(lambda: defaultdict(float))

        # Populate quantities only for actual product-location pairs
        for item in raw_data:
            loc = item['Location']
            prod = item['Product']
            qty = item.get('Consumed Quantity', 0)

            location_product_map[loc][prod] += qty

           




        # Build chart series: one per product, stacked across locations
        emphasis_style = {
            'itemStyle': {
                'shadowBlur': 10,
                'shadowColor': 'rgba(0,0,0,0.3)'
            }
        }

        series = []
        for prod in products:
            series.append({
                'name': prod,
                'type': 'bar',
                'stack': 'one',
                'emphasis': emphasis_style,
                'data': [location_product_map[loc][prod] for loc in locations]
            })



        



        # Build tabular result
        result = []
        for loc in locations:
            for prod in products:
                qty = location_product_map[loc][prod]
                result.append({
                    'Location': loc,
                    'Product': prod,
                    'Consumed Quantity': round(qty, 2)
                })

           

        # Chart configuration
        chart_option = {
            'title': {'text': 'استهلاك المنتج حسب الموقع'},
            'tooltip': {'trigger': 'item'},
            'legend': {
                'type': 'scroll',
                'orient': 'horizontal',
                'bottom': 0,
                'data': products
                },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '10%',
                'containLabel': True
            },
            'toolbox': {
                'feature': {
                    'magicType': {'type': ['stack']},
                    'dataView': {},
                    'saveAsImage': {}
                }
            },
            'brush': {
                'toolbox': ['rect', 'polygon', 'lineX', 'lineY', 'keep', 'clear'],
                'xAxisIndex': 0
            },
            'xAxis': {
                'type': 'category',
                'data': locations,
                'axisLabel': {
                    'rotate': 45  # or 30, or even 90 if needed
                },
                'name': 'Location'
            },
            'yAxis': {'type': 'value'},
            'series': series
        }

        return {
            'doc_ids': docids,
            'doc_model': doc_model,
            'docs': products,
            'data': {
                'chart_option': chart_option,
                'products': products,
                'locations': locations,
                'result': result
            }
        }





        


