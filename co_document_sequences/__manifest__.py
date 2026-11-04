## -*- coding: utf-8 -*-
{
    'name': 'Document Number Control',

    'summary': 'Invoice sequence, document numbering and journal sequence reset',

    'description': """
CPA Books Re-Sequences
======================
Manage and re-sequence document numbers across Accounting, Sales,
Purchase, Inventory, Project and CRM in Odoo 14.
    """,

    'author': 'CPA Books',
    'website': 'https://www.cpabooks.co',

    'category': 'Productivity',
    'version': '14.0.1.67',
    'license': 'LGPL-3',
    'price': 0.00,
    'currency': 'USD',
    'live_test_url': 'https://cpabooks.org/contactus?debug=1',

    'images': [
        'static/description/banner_screenshot.jpg',
    ],

    'depends': [
        'base',
        'account',
        'sale',
        'purchase',
        'stock',
        'project',
        'crm',
    ],

    'data': [
        'views/views.xml',
        'views/templates.xml',
        'views/sequence_menu.xml',
        'views/account_move.xml',
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/stock_picking.xml',
        'views/set_company_prefix_vew.xml',
        'views/assets.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/create_sequences.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'support': 'info@cpabooks.org',
}
