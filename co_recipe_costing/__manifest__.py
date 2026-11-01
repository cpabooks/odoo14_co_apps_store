# -*- coding: utf-8 -*-
{
    'name': 'Restaurant Recipe Costing',
    'summary': 'Restaurant recipe book, food costing, ingredient consumption and closing stock',
    'description': """
Recipe Book for restaurants on Odoo 14.

* Link each menu item to a sales product and store ingredients per portion.
* Compare budget food cost with the current recipe cost and margin.
* Build theoretical ingredient consumption from confirmed sales.
* Enter chef closing stock and see variance against theoretical use.
* Load sample recipes, then clone them into live recipes.
    """,
    'version': '14.0.1.0.45',
    'category': 'Operations/Restaurant',
    'author': 'CPA Books',
    'website': 'https://www.cpabooks.co',
    'license': 'LGPL-3',
    'price': 150.00,
    'currency': 'USD',
    'support': 'info@cpabooks.org',
    'live_test_url': 'https://cpabooks.org/contactus?debug=1',
    'external_dependencies': {'python': ['openpyxl']},
    'depends': [
        'base',
        'product',
        'sale_management',
        'stock',
        'purchase',
    ],
    'data': [
        'security/recipe_security.xml',
        'security/ir.model.access.csv',
        'views/recipe_views.xml',
        'views/product_recipe_views.xml',
        'views/consumption_views.xml',
        'views/dashboard_views.xml',
        'wizard/closing_stock_wizard_views.xml',
        'wizard/demo_wizard_views.xml',
        'views/menu.xml',
    ],
    'qweb': [
        'static/src/xml/dashboard.xml',
        'static/src/xml/key_results.xml',
    ],
    'images': ['static/description/banner_store.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
