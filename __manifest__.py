{
    'name': 'Store Product Batch',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Track store batches by location with barcode scanning',
    'author': 'gladdema',
    'website': 'https://gladdema.com',
    'depends': ['base', 'product', 'point_of_sale', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/store_branch_view.xml',          
        'views/store_location_view.xml',
        'views/store_batch_view.xml',
        'views/store_batch_sequence.xml',
        'views/store_batch_report_view.xml',
        'views/store_batch_menu_view.xml',      
        'report/report_store_batch_template.xml',
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
