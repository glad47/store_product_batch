{
    'name': 'Product Batch Tracker',
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': 'Track store batches by location with barcode scanning',
    'author': 'gladdema',
    'website': 'https://gladdema.com',
    'depends': ['base', 'product', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/store_branch_view.xml',          
        'views/store_location_view.xml',
        'views/store_batch_view.xml',
        'views/store_batch_sequence.xml',
        'views/store_batch_report_view.xml', 
        'views/store_batch_menu_view.xml',      
        'views/run_batch_consumption_tracker.xml', 
        'report/report_store_batch_template.xml',
    ],
    'assets': {
        'store_product_batch.assets': [
            'store_product_batch/static/src/js/GlobalHeaderButton.js',
            'store_product_batch/static/src/xml/GlobalHeaderButton.xml',
        ],
    },

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
