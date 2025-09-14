from odoo import models, api, http
from odoo.http import request
from collections import defaultdict
import calendar
from builtins import ValueError
from datetime import datetime
import json




class StoreBatchReport(http.Controller):
    _name = 'report.store_product_batch.report_store_batch_template'
    _description = 'Store Batch Summary Report'

    MONTH_KEYS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    

    @http.route('/store_product_batch/get_branches', type='json', auth='user', methods=['POST'])
    def get_branches(self):
        branches = request.env['store.branch'].search([('active', '=', True)])
        result = [{'id': b.id, 'name': b.name} for b in branches]
        return {'branches': result}
    

    
    @http.route('/store_product_batch/get_years', type='json', auth='user', methods=['POST'])
    def get_years(self):
        years = request.env['store.batch'].search(['|', ('active', '=', False), ('active', '=', True)]).mapped('start_time')
        unique_years = sorted({dt.year for dt in years if dt})
        return {'years': unique_years}
    

    

    @http.route('/store_product_batch/get_months', type='json', auth='user', methods=['POST'])
    def get_months(self):
        # You can still parse the year if needed for other logic
        data = json.loads(request.httprequest.data)
        # year = data.get('year')

        # Return all 12 months as abbreviated names (Jan, Feb, ..., Dec)
        all_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        return {'months': all_months}
    



    
    @http.route('/store_product_batch/get_days', type='json', auth='user', methods=['POST'])
    def get_days(self):
        data = json.loads(request.httprequest.data)
        year = int(data['year'])
        month_name = data['month']
        month_map = {name: idx for idx, name in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], start=1)}
        month_num = month_map.get(month_name)
        days = list(range(1, calendar.monthrange(year, month_num)[1] + 1))
        return {'days': days}
    


    
    @http.route('/store_product_batch/chart_data', type='json', auth='user', methods=['POST'])
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
        return self.build_batch_consumption_report(
            docids=docids,
            doc_model='store.batch',
            data=data
        )
    

   
    def build_nested_summary(self, time_granularity='total', data= {}):
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

        summary = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
            'consumed_qty': 0.0,
            'earned_amount': 0.0
        })))

        

        selected_branch = request.env['store.branch'].search([('id', '=', data["branch"])])
        
        batches = request.env['store.batch'].search([
                                                ('branch_id', '=', selected_branch.id),
                                                ('active', 'in', [True, False])
                                            ])
        
        
        # Pre-initialize time keys with zeros
        
        for location in selected_branch.location_ids:
            branch_id = selected_branch.id
            location_id = location.id

            if time_granularity == 'day' and data["year"] and data["month"]:
                for day in range(1, 32):  # Adjust for actual month length if needed
                    summary[branch_id][location_id][str(day)]  # triggers default zero init
            elif time_granularity == 'month' and data["year"]:
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
                for batch_line in batch.batch_line_ids:
                    for daily in batch_line.daily_log_ids:

                        if location not in batch.location_ids or not batch.start_time:
                            continue

                        # Filter by year and/or month based on granularity
                        batch_year = str(daily.date.year) 
                        batch_month = MONTH_KEYS[daily.date.month - 1] 

                        if time_granularity == 'day':
                            if data["year"] and data["month"] and (batch_year != str(data["year"]) or batch_month != data["month"]):
                                continue
                        elif time_granularity == 'month':
                            if data["year"] and batch_year != str(data["year"]):
                                continue

                        location_count = len(batch.location_ids)
                        if location_count == 0:
                            time_key = get_time_key(daily.date)
                            summary[branch_id][location_id][time_key]['consumed_qty'] = 0
                            summary[branch_id][location_id][time_key]['earned_amount'] = 0
                            continue

                        consumed_qty = daily.consumed_qty / location_count
                        earned_amount = daily.earned_amount / location_count

                        time_key = get_time_key(daily.date)
                        summary[branch_id][location_id][time_key]['consumed_qty'] += consumed_qty
                        summary[branch_id][location_id][time_key]['earned_amount'] += earned_amount

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
                for time_key, data in time_data.items():
                    result.append({
                        'Branch': branch.name,
                        'Location': location.code,
                        time_label: time_key,
                        'Consumed Quantity': round(data['consumed_qty'], 2),
                        'Earned Amount': round(data['earned_amount'], 2)
                    })

        return result






    def build_batch_consumption_report(self, *, docids=None, doc_model='store.batch', data):

        MONTH_KEYS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        

        # Fixed month keys
       

        # Granularity mapping
        granularity_map = {
            'Year': 'year',
            'Month': 'month',
            'Day': 'day'
        }
        time_granularity = granularity_map.get(data['time_dimension'], 'total')

        # Fetch raw data
        raw_data = self.build_nested_summary(time_granularity=time_granularity, data=data)
        


      
        # Determine time keys
        if data['time_dimension'] == 'Month':
            time_keys = MONTH_KEYS
        elif data['time_dimension'] == 'Day':
            if not data['year'] or not data['month']:
                raise ValueError("Year and month must be provided for daily view.")
            # Map month name to number
            month_map = {name: idx for idx, name in enumerate(MONTH_KEYS, start=1)}
            month_num = month_map.get(data['month'])
            if not month_num:
                raise ValueError(f"Invalid month name: {data['month']}")
            days_in_month = calendar.monthrange(int(data['year']), month_num)[1]
            time_keys = [str(day) for day in range(1, days_in_month + 1)]
        else:
            # Extract unique keys from data
            time_keys = sorted({item.get(data['time_dimension']) for item in raw_data if item.get(data['time_dimension'])})

        # Collect unique locations
        locations = sorted({item['Location'] for item in raw_data})

        # Initialize location → time → quantity map
        location_time_map = {
            loc: {t: 0 for t in time_keys}
            for loc in locations
        }

        # Populate quantities
        for item in raw_data:
            loc = item['Location']
            t = item.get(data['time_dimension'])
            qty = item.get('Consumed Quantity', 0)
            if loc in location_time_map and t in location_time_map[loc]:
                location_time_map[loc][t] += qty

        # Build chart series
        series = []
        for loc in locations:
            series.append({
                'name': loc,
                'type': 'line',
                'data': [location_time_map[loc][t] for t in time_keys]
            })
        # Chart configuration
        chart_option = {
            'title': {'text': f'الاستهلاك حسب الموقع والوقت'},
            'tooltip': {'trigger': 'axis'},
            'legend': {'data': locations},
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '10%',
                'containLabel': True
            },
            'toolbox': {'feature': {'saveAsImage': {}}},
            'xAxis': {
                'type': 'category',
                'boundaryGap': False,
                'data': time_keys
            },
            'yAxis': {'type': 'value'},
            'series': series
        }

        return {
            'doc_ids': docids,
            'doc_model': doc_model,
            'docs': locations,
            'data': {
                'chart_option': chart_option,
                'locations': locations,
                'time_keys': time_keys
            }
        }
    
    