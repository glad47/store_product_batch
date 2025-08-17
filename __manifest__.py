{
    'name': 'Store Product Batch',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Track store batches by location with barcode scanning',
    'author': 'gladdema',
    'website': 'https://gladdema.com',
    'depends': ['base', 'product', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/store_location_views.xml',
        'views/store_batch_views.xml',
        'views/store_batch_sequence.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
