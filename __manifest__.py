{
    'name': 'Product Batch Tracker',
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': 'Track store batches by location with barcode scanning',
    'author': 'gladdema',
    'website': 'https://gladdema.com',
    'depends': ['base', 'product', 'point_of_sale'],
    'data': [
        'static/lib/echarts.js',
        'security/store_product_batch_security.xml',
        'security/ir.model.access.csv', 
        'data/demo_users.xml',
        'views/store_branch_view.xml',          
        'views/store_location_view.xml',
        'views/store_batch_view.xml',
        'views/store_batch_sequence.xml',
        'views/store_batch_sequence_name.xml',
        'views/store_sale_graph.xml',
        'views/store_batch_report_view.xml', 
        'views/store_batch_menu_view.xml',      
        'views/run_batch_consumption_tracker.xml', 
        'report/report_store_batch_template.xml',
        'report/report_store_batch_template_prod.xml',
        
    ],
    'assets': {
        'web.assets_backend': [
            'store_product_batch/static/lib/echarts.js',
        ],


        'web.assets_frontend': [
            'store_product_batch/static/lib/echarts.js',
        ],
    },

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
