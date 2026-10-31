# -*- coding: utf-8 -*-
{
    'name': 'Chart of Accounts Management',
    'summary': 'IFRS chart of accounts, ledger coding, COA reset, merge and opening balance',
    'description': """
CPA Books Chart of Accounts
===========================
IFRS-structured chart of accounts for Odoo 14 Accounting:
type / group / ledger coding, automatic ledger codes, COA reset and
regenerate wizards, merge and delete of unused ledgers, opening balance
entry, correspondent Dr/Cr ledgers and product COA codes.
    """,
    'author': 'CPA Books (WhastApp +971562568128)',
    'website': 'https://www.cpabooks.co',
    'support': 'info@cpabooks.org',
    'category': 'Accounting/Accounting',
    'version': '14.0.1.0.0',
    'license': 'LGPL-3',
    'price': 0.00,
    'currency': 'USD',
    'live_test_url': 'https://cpabooks.org/contactus?debug=1',
    'images': [
        'static/description/banner_store.jpg',
    ],
    'depends': [
        'base',
        'web',
        'mail',
        'product',
        'account',
        'purchase',
    ],
    'data': [
        'security/account_group_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/disable_legacy_coa_views.xml',
        'data/initialize_coa_code_digits.xml',
        'views/coa_legacy/coa_create.xml',
        'views/coa_legacy/inherit_account_account.xml',
        'views/coa_bulk_actions_wizard.xml',
        'views/coa_legacy/account_account.xml',
        'views/coa_legacy/chart_of_account_list.xml',
        'views/coa_legacy/productTemplate.xml',
        'views/templates.xml',
        'views/coa_ifrs_coding_wizard.xml',
        'views/account_account_views.xml',
        'views/account_correspondent.xml',
        'views/coa_setup_file_views.xml',
        'views/account_account_search_views.xml',
        'views/account_opening_balance_views.xml',
        'views/product_with_analytic_acc_config.xml',
        'views/account_move.xml',
        'views/res_config_settings_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
