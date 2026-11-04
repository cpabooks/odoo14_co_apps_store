# -*- coding: utf-8 -*-
{
    'name': 'Financial Audit Reports',
    'summary': 'Audited financial statements, trial balance, IFRS profit and loss, balance sheet and cash flow',
    'description': """
CPABooks Audited Financials (AFG)
=================================
From trial balance to the full pack: Profit or Loss, Financial Position,
Equity, Cash Flow, PPE schedule, notes and UAE Corporate Tax.
    """,
    'version': '14.0.1.1.0',
    'category': 'Accounting',
    'author': 'CPA Books',
    'website': 'https://www.cpabooks.co',
    'license': 'LGPL-3',
    'price': 0.00,
    'currency': 'USD',
    'live_test_url': 'https://cpabooks.org/contactus?debug=1',
    'support': 'info@cpabooks.org',
    'images': [
        'static/description/banner_screenshot.jpg',
    ],
    'external_dependencies': {'python': ['openpyxl', 'xlsxwriter']},
    'depends': [
        'base',
        'account',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/audited_financial_security.xml',
        'data/multico_client_actions.xml',
        'views/audited_financials_views.xml',
        'views/afg_map_list_assets.xml',
        'report/afg_audit_report.xml',
        'views/account_account_views.xml',
        'views/audited_financial_ledger_merge_views.xml',
        'views/audited_financial_l1_print_wizard_views.xml',
        'views/audited_financial_print_setup_wizard_views.xml',
        'views/afg_journal_items_views.xml',
        'data/menu_cleanup_legacy_statements.xml',
    ],
    'qweb': ['static/src/xml/audited_financials_dashboard.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
}
