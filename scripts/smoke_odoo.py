"""Run with odoo-bin shell on a disposable database; all writes roll back."""
Account = env['account.account']
try:
    assert Account.search_count([]) > 100, 'Default COA was not initialized'
    assert env['account.group'].search_count([]) > 0
    values = {
        'name': 'Release smoke ledger',
        'user_type_id': env.ref('account.data_account_type_expenses').id,
        'company_id': env.company.id,
    }
    ledger = Account.create(values)
    assert ledger.code and not ledger.code.startswith('__'), 'Automatic code missing'
    duplicate = ledger.copy({'name': 'Release smoke duplicate'})
    assert duplicate.code and duplicate.code != ledger.code
    manual = Account.create(dict(values, code='MANUAL-RELEASE'))
    assert manual.code == 'MANUAL-RELEASE', 'Explicit account code was overwritten'
    batch = Account.create([dict(values), dict(values)])
    assert len(set(batch.mapped('code'))) == 2, 'Batch codes are duplicated'
    assert all(code and not code.startswith('__') for code in batch.mapped('code'))
    assert env.ref('co_chart_of_accounts.action_cpa_coa_setup_file')
    public = env.ref('base.public_user')
    for model in ('visa.product', 'product.analytic.acc.conf'):
        assert not env[model].with_user(public).check_access_rights('write', raise_exception=False)
    print('PASS: seed data, create, duplicate, manual code, batch create, action, public ACL')
finally:
    env.cr.rollback()
