"""Run using odoo-bin shell on a disposable release database."""
modules = (
    'co_chart_of_accounts', 'co_cafm', 'co_fire_safety',
    'co_recipe_costing', 'co_document_sequences', 'co_switchgear',
)
try:
    for name in modules:
        module = env['ir.module.module'].search([('name', '=', name)])
        assert module.state == 'installed', (name, module.state)
        records = env['ir.model.data'].search_count([('module', '=', name)])
        assert records > 0, name
        print('PASS:', name, records, 'external identifiers')
    Account = env['account.account']
    assert Account.search_count([]) > 100
    values = {
        'name': 'Release validation ledger',
        'user_type_id': env.ref('account.data_account_type_expenses').id,
        'company_id': env.company.id,
    }
    ledger = Account.create(values)
    duplicate = ledger.copy({'name': 'Release validation duplicate'})
    assert ledger.code and duplicate.code and ledger.code != duplicate.code
    assert env.ref('co_chart_of_accounts.action_cpa_coa_setup_file')
    public = env.ref('base.public_user')
    for model in ('cpabooks.cafm.unit', 'cpabooks.cafm.contract'):
        assert not env[model].with_user(public).check_access_rights('write', raise_exception=False)
    print('PASS: account numbering, duplicate, renamed action and CAFM public write denial')
finally:
    env.cr.rollback()
