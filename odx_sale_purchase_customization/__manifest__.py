# -*- coding: utf-8 -*-

{
    'name': 'Sale & Purchase Customization',
    'category': 'Sale, Purchase',
    'sequence': 14,
    'summary': 'Purchase Order is created while conforming the Sale Order and vice versa ',
    'description': """
        Adding sequence to  customers and including it in name get and name search. 
        New fields is added in both sale order and purchase order. While confirming sale order,a purchase
        order is created based on the corresponding sale order and vice versa.
    """,
    'author': 'Odox SoftHub / Albin',
    'website': 'https://www.odoxsofthub.com',
    'version': '13.0.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sale_purchase_customization_data.xml',
        'views/res_partner.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/purchase_landing_cost_view.xml',
        'report/sale_report_template.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
