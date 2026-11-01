"""Run using odoo-bin shell on a disposable release database."""
modules = (
    'co_chart_of_accounts', 'co_cafm', 'co_fire_safety',
    'co_recipe_costing', 'co_document_sequences', 'co_switchgear',
    'co_field_service', 'co_audited_financials',
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

    # Resolve the restored forms, including their complete inheritance chains.
    for xmlid in (
        'co_field_service.view_fsm_project_task_form_view_inherit',
        'co_field_service.issue_form',
        'account.view_move_form',
    ):
        view = env.ref(xmlid)
        result = env[view.model].fields_view_get(view_id=view.id, view_type='form')
        assert result['arch'], xmlid
    assert not env['material.request.line'].with_user(public).check_access_rights('write', raise_exception=False)
    assert not env['invoice.type'].with_user(public).check_access_rights('write', raise_exception=False)

    project = env['project.project'].create({'name': 'Release FSM project', 'is_fsm': True})
    partner = env['res.partner'].create({'name': 'Release service customer'})
    task = env['project.task'].with_context(fsm_mode=True).create({
        'name': 'Release service request', 'project_id': project.id,
        'partner_id': partner.id, 'is_fsm': True,
    })
    quotation = task.action_fsm_create_quotation()
    assert quotation['context']['default_task_id'] == task.id
    assert quotation['context']['default_partner_id'] == partner.id
    product = env['product.product'].create({'name': 'Release service material', 'type': 'product'})
    request = env['material.request.line'].create({
        'task_id': task.id, 'product_id': product.id, 'quantity': 2,
    })
    warehouse = env['stock.warehouse'].search([('company_id', '=', env.company.id)], limit=1)
    issue = env['stock.picking'].create({
        'issue_project_task_id': task.id, 'picking_type_id': warehouse.int_type_id.id,
        'location_id': warehouse.lot_stock_id.id,
        'location_dest_id': env.ref('stock.stock_location_customers').id,
    })
    issue._onchange_issue_project_task_id()
    assert issue.move_ids_without_package.product_uom_qty == 2
    issue.action_confirm()
    issue.move_ids_without_package.quantity_done = 2
    issue.button_validate()
    assert issue.state == 'done'
    request.invalidate_cache()
    assert request.quantity_done == 2
    returned = env['stock.picking'].new({
        'stock_issue_picking_id': issue.id, 'picking_type_id': warehouse.int_type_id.id,
    })
    returned._onchange_stock_issue_picking_id()
    assert returned.is_stock_return_note and returned.move_ids_without_package.product_uom_qty == 2
    for xmlid in ('task_custom_report', 'task_custom_report_customer_copy'):
        html, _ = env.ref('co_field_service.' + xmlid)._render_qweb_html(task.ids)
        assert b'JOB COMPLETION REPORT' in html, xmlid
    print('PASS: FSM forms, quotation, material issue/return, both JCR HTML reports and public ACL')

    contract = env['cpabooks.cafm.contract'].create({
        'client_id': partner.id, 'total_contract_value': 1200,
    })
    order = env['cpabooks.cafm.contract.order'].create({
        'contract_id': contract.id, 'partner_id': partner.id, 'amount': 100,
    })
    html, _ = env.ref('co_cafm.action_report_cafm_contract_order')._render_qweb_html(order.ids)
    assert b'QUOTATION' in html
    print('PASS: CAFM contract/order creation and report HTML without private templates')

    version = env['audited.financial.version'].afg_dashboard_default_version()
    if isinstance(version, dict):
        version_id = version.get('id') or version.get('version_id')
    else:
        version_id = version.id if hasattr(version, 'id') else version
    version = env['audited.financial.version'].browse(version_id).exists()
    assert version, 'AFG default version missing'
    payload = version._afg_dashboard_data_impl(active_id=version.id)
    assert payload and not payload.get('error'), 'AFG dashboard returned an error'
    for xmlid in ('action_report_afg_audit_pdf', 'action_report_afg_simple_fs_pdf'):
        report = env.ref('co_audited_financials.' + xmlid)
        html, _ = report._render_qweb_html(version.ids)
        assert html and b'o_afg_audit_pdf' in html, xmlid
    print('PASS: AFG dashboard data and both financial report HTML renderers')
finally:
    env.cr.rollback()
