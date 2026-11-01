# -*- coding: utf-8 -*-

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

_MIGRATION_KEYS = {
    'creators': 'co_field_service.hook_fsm_creators_v1',
    'deliveries': 'co_field_service.hook_delivery_partners_v1',
    'approval_sync': 'co_field_service.hook_approval_sync_v1',
    'crn_analytic': 'co_field_service.hook_crn_analytic_v1',
    'data_xml': 'co_field_service.hook_data_xml_v1',
}


def _table_exists(cr, table_name):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.tables
         WHERE table_schema = current_schema()
           AND table_name = %s
         LIMIT 1
        """,
        (table_name,),
    )
    return bool(cr.fetchone())


def _column_exists(cr, table_name, column_name):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name = %s
           AND column_name = %s
         LIMIT 1
        """,
        (table_name, column_name),
    )
    return bool(cr.fetchone())


def _run_in_savepoint(cr, label, callback):
    """Run hook work in a savepoint so one failure does not abort the install transaction."""
    try:
        with cr.savepoint():
            callback()
            return True
    except Exception as err:
        _logger.warning('%s skipped: %s', label, err)
        return False


def _migration_done(env, key):
    icp = env['ir.config_parameter'].sudo()
    try:
        with env.cr.savepoint():
            return bool(icp.get_param(key))
    except Exception:
        return False


def _mark_migration_done(env, key):
    icp = env['ir.config_parameter'].sudo()
    with env.cr.savepoint():
        icp.set_param(key, '1')


def _approval_module_installed(cr):
    if not _table_exists(cr, 'ir_module_module'):
        return False
    cr.execute(
        """
        SELECT state
          FROM ir_module_module
         WHERE name = 'cpabooks_approval'
         LIMIT 1
        """
    )
    row = cr.fetchone()
    return row and row[0] in ('installed', 'to upgrade', 'to install')


def _cleanup_orphan_approval_views(cr):
    """Drop stale FSM views that reference approval fields when Approvals is not installed."""
    if _approval_module_installed(cr):
        return
    if not _table_exists(cr, 'ir_ui_view'):
        return
    cr.execute(
        """
        DELETE FROM ir_ui_view v
         USING ir_model_data d
         WHERE d.model = 'ir.ui.view'
           AND d.res_id = v.id
           AND d.module = 'cpabooks_approval'
           AND v.model = 'project.task'
        """
    )
    # Views keep merged arch in arch_db after Approvals was uninstalled; strip those nodes.
    for pattern, like in (
        ('<xpath[^>]*approval_request[^>]*>.*?</xpath>', '%approval_request%'),
        ('<field[^>]*name="approval_request_id"[^>]*/>', '%approval_request_id%'),
        ('<field[^>]*name="approval_state"[^>]*/>', '%approval_state%'),
        ('<field[^>]*name="approval_state_label"[^>]*/>', '%approval_state_label%'),
        ('<button[^>]*name="action_fsm_approval[^>]*/>', '%action_fsm_approval%'),
    ):
        cr.execute(
            """
            UPDATE ir_ui_view
               SET arch_db = regexp_replace(arch_db, %s, '', 'gn')
             WHERE model = 'project.task'
               AND arch_db LIKE %s
            """,
            (pattern, like),
        )
    cr.execute(
        """
        DELETE FROM ir_ui_view
         WHERE model = 'project.task'
           AND (
                arch_db LIKE '%approval_state%'
             OR arch_db LIKE '%approval_request_id%'
           )
           AND id NOT IN (
                SELECT res_id
                  FROM ir_model_data
                 WHERE model = 'ir.ui.view'
                   AND module = 'co_field_service'
           )
        """
    )


def _ensure_approval_state_column(cr):
    """Create approval_state early so FSM form validation passes during field_service upgrade."""
    if not _approval_module_installed(cr):
        return
    if not _table_exists(cr, 'project_task'):
        return
    if _column_exists(cr, 'project_task', 'approval_state'):
        return
    cr.execute(
        """
        ALTER TABLE project_task
        ADD COLUMN approval_state varchar DEFAULT 'pending'
        """
    )


def _drop_stale_fsm_stage7_layout(cr):
    """Remove stage-7 inherit before parent FSM form reload.

    Older DBs kept approval_request_id xpaths in this view after stage 7 was
    simplified; that breaks validation when view_fsm_project_task_form_view_inherit
    is updated.
    """
    if not _table_exists(cr, 'ir_model_data') or not _table_exists(cr, 'ir_ui_view'):
        return
    cr.execute(
        """
        DELETE FROM ir_ui_view v
         USING ir_model_data d
         WHERE d.model = 'ir.ui.view'
           AND d.res_id = v.id
           AND d.module = 'co_field_service'
           AND d.name = 'view_fsm_crn_stage7_layout'
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_data
         WHERE module = 'co_field_service'
           AND name = 'view_fsm_crn_stage7_layout'
        """
    )


def pre_init_hook(cr):
    try:
        import odoo.addons.co_field_service.models.project_task_quotation_display  # noqa: F401
    except Exception:
        _logger.exception(
            'FSM quotation display model could not be pre-loaded during install.'
        )
    _drop_stale_fsm_stage7_layout(cr)
    _cleanup_orphan_approval_views(cr)
    _ensure_approval_state_column(cr)

    if _table_exists(cr, 'account_analytic_line'):
        if not _column_exists(cr, 'account_analytic_line', 'fsm_cost_amount'):
            cr.execute("""
                ALTER TABLE account_analytic_line
                ADD COLUMN fsm_cost_amount numeric
            """)
        for col, coltype in (
            ('fsm_time_in', 'numeric'),
            ('fsm_time_out', 'numeric'),
        ):
            if not _column_exists(cr, 'account_analytic_line', col):
                cr.execute(
                    "ALTER TABLE account_analytic_line ADD COLUMN %s %s" % (col, coltype)
                )

    if _table_exists(cr, 'material_request_line'):
        if not _column_exists(cr, 'material_request_line', 'test_quantity_issued'):
            cr.execute("""
                ALTER TABLE material_request_line
                ADD COLUMN test_quantity_issued numeric
            """)

    if _table_exists(cr, 'project_task'):
        for col, ddl in (
            ('fsm_creator_uid', 'integer'),
            ('fsm_ui_active_stage', 'integer DEFAULT 0'),
            ('fsm_workflow_edit_mode', 'boolean DEFAULT false'),
            ('fsm_stage0_force_complete', 'boolean DEFAULT false'),
            ('fsm_assigned_employee_id', 'integer'),
            ('fsm_transport_cost', 'numeric DEFAULT 0'),
            ('fsm_other_cost', 'numeric DEFAULT 0'),
        ):
            if not _column_exists(cr, 'project_task', col):
                cr.execute(
                    "ALTER TABLE project_task ADD COLUMN %s %s" % (col, ddl)
                )

    if _table_exists(cr, 'stock_quant'):
        if not _column_exists(cr, 'stock_quant', 'cpabooks_inventory_sequence'):
            cr.execute("""
                ALTER TABLE stock_quant
                ADD COLUMN cpabooks_inventory_sequence varchar
            """)


def _run_data_xml_migrations(env):
    """Former project_task_data.xml / project_project_data.xml jobs — once only."""
    env['project.task'].action_normalize_fsm_crn_numbers()
    env['project.task'].action_assign_default_project_to_unlinked_fsm_crns()
    env['stock.picking'].action_recompute_material_return_flags()
    env['account.analytic.line'].action_recompute_fsm_cost_amounts()
    env['project.project'].enable_fsm_for_all_projects()


def post_init_hook(cr, registry):
    """Run after module install; heavy jobs are one-time only."""
    env = api.Environment(cr, SUPERUSER_ID, {})

    if not _migration_done(env, _MIGRATION_KEYS['data_xml']):
        if _run_in_savepoint(cr, 'FSM data migrations', lambda: _run_data_xml_migrations(env)):
            _mark_migration_done(env, _MIGRATION_KEYS['data_xml'])

    if not _migration_done(env, _MIGRATION_KEYS['creators']):
        if _run_in_savepoint(
            cr,
            'FSM creator backfill',
            lambda: env['project.task'].action_backfill_fsm_crn_creators(),
        ):
            _mark_migration_done(env, _MIGRATION_KEYS['creators'])

    def _backfill_ui_stage():
        cr.execute("""
            UPDATE project_task
               SET fsm_ui_active_stage = COALESCE(fsm_ui_active_stage, 0)
             WHERE is_fsm = TRUE AND fsm_ui_active_stage IS NULL
        """)

    _run_in_savepoint(cr, 'FSM UI stage backfill', _backfill_ui_stage)

    if not _migration_done(env, _MIGRATION_KEYS['deliveries']):
        def _fix_deliveries():
            if env.registry.get('stock.picking'):
                env['stock.picking']._cpabooks_fix_missing_delivery_partners()

        if _run_in_savepoint(cr, 'Delivery partner fix', _fix_deliveries):
            _mark_migration_done(env, _MIGRATION_KEYS['deliveries'])

    if not _migration_done(env, _MIGRATION_KEYS['crn_analytic']):
        def _backfill_analytic():
            crn_tasks = env['project.task'].sudo().search([
                '|',
                ('is_fsm', '=', True),
                ('task_seq', '=like', 'CRN%'),
            ])
            if crn_tasks:
                crn_tasks._ensure_crn_analytic_account()

        if _run_in_savepoint(cr, 'CRN analytic backfill', _backfill_analytic):
            _mark_migration_done(env, _MIGRATION_KEYS['crn_analytic'])
