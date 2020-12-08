# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'AG_mastex_reports',
    'author': 'Fouad',
    'depends': ['sale'],
    'data': [
        
        'report/invoice_arabic.xml',
        'report/account_report_ar.xml',
        'report/report_templates.xml',
        'views/account_view.xml'
       
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
