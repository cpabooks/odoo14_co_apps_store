# -*- coding: utf-8 -*-
import logging

from odoo.tools.sql import column_exists, create_column, table_exists

_logger = logging.getLogger(__name__)


def _ensure_account_account_cpabooks_columns(cr):
    """Ensure stored COA helper columns exist before old migrations use them."""
    specs = (
        ("identity_id", "int4"),
        ("identity_code", "varchar"),
        ("is_show_code", "bool"),
        ("get_previous", "bool"),
        ("previous", "int4"),
        ("qid", "varchar"),
        ("is_duplicate", "bool"),
        ("cpabooks_previous_code", "varchar"),
        ("cpabooks_previous_name", "varchar"),
        ("cpabooks_ifrs_code", "varchar"),
        ("cpabooks_ifrs_name", "varchar"),
        ("cpabooks_default_seed_key", "varchar"),
        ("cpabooks_default_manually_modified", "bool"),
        ("cpabooks_sync_name_all_companies", "bool"),
        ("correspondent_account_id", "int4"),
        ("cpabooks_l1_type_code", "varchar"),
        ("cpabooks_l1_type_label", "varchar"),
        ("cpabooks_group_code", "varchar"),
        ("cpabooks_group_series_code", "varchar"),
    )
    for col, col_type in specs:
        if not column_exists(cr, "account_account", col):
            create_column(cr, "account_account", col, col_type)

    if not column_exists(cr, "account_group", "identity_id"):
        create_column(cr, "account_group", "identity_id", "int4")


def _ensure_res_company_coa_code_digits(cr):
    if not column_exists(cr, "res_company", "cpabooks_coa_code_digits"):
        create_column(cr, "res_company", "cpabooks_coa_code_digits", "varchar")
    cr.execute(
        """
        UPDATE res_company
           SET cpabooks_coa_code_digits = '6'
         WHERE cpabooks_coa_code_digits IS NULL
            OR cpabooks_coa_code_digits = ''
        """
    )


def _restore_partner_accounts(env):
    try:
        fixed = env['res.partner'].action_cpabooks_restore_partner_accounts()
        _logger.info(
            'CPABooks CoA: restored receivable/payable on %s partner(s)',
            fixed,
        )
    except Exception:
        _logger.exception('CPABooks CoA: partner account restore skipped')


def _init_coa_wizard_tables(env):
    """Ensure transient wizard tables exist (safe if module was not upgraded yet)."""
    missing = []
    for model_name in (
        "coa.reset.code.options.wizard",
        "coa.menu.action.wizard",
        "coa.reset.code.preview.wizard",
        "coa.reset.code.preview.wizard.line",
        "coa.bulk.actions.wizard",
        "coa.bulk.actions.wizard.line",
        "coa.ifrs.coding.wizard",
        "coa.ifrs.coding.preview.line",
        "coa.ifrs.name.suggestion.wizard",
        "coa.ifrs.reset.confirm.wizard",
        "coa.bulk.delete.wizard",
    ):
        if model_name in env and not table_exists(env.cr, env[model_name]._table):
            missing.append(model_name)
    if not missing:
        return
    try:
        env.registry.init_models(
            env.cr, missing, {'module': 'cpabooks_chart_of_accounts'}, install=False,
        )
    except Exception:
        _logger.exception("CPABooks CoA: could not init tables for %s", missing)


def _drop_account_code_unique_per_company(cr):
    """Allow duplicate ledger codes per company (IFRS XXXC series / mirrored ledgers)."""
    cr.execute(
        """
        SELECT con.conname
          FROM pg_constraint con
          JOIN pg_class rel ON rel.oid = con.conrelid
          JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
         WHERE nsp.nspname = 'public'
           AND rel.relname = 'account_account'
           AND con.contype = 'u'
           AND pg_get_constraintdef(con.oid) ILIKE '%code%'
           AND pg_get_constraintdef(con.oid) ILIKE '%company%'
        """
    )
    for (conname,) in cr.fetchall():
        cr.execute('ALTER TABLE account_account DROP CONSTRAINT IF EXISTS "%s"' % conname.replace('"', ''))
        _logger.info('CPABooks CoA: dropped unique account code constraint %s', conname)


def _recover_ifrs_temp_codes(env):
    try:
        engine = env['coa.ifrs.coding']
        recovered = engine.recover_stuck_temp_ifrs_codes()
        if recovered:
            _logger.info(
                'CPABooks CoA: recovered IFRS codes on %s ledger(s) stuck on temp codes',
                recovered,
            )
        companies = env['res.company'].search([])
        engine.migrate_coa_structure_all_companies()
    except Exception:
        _logger.exception('CPABooks CoA: IFRS temp-code recovery skipped')


def _ensure_default_coa_for_companies(env):
    result = env['account.account'].cpabooks_ensure_default_coa_all_companies()
    env['account.account'].cpabooks_ensure_unaffected_earnings_all_companies()
    _logger.info(
        'CPABooks CoA: all-company defaults created=%s updated=%s preserved=%s',
        result['created'],
        result['updated'],
        result['preserved'],
    )


def _cleanup_stale_account_account_fields(cr):
    """Remove ORM field entries whose columns were never created on account_account."""
    stale = (
        'cpabooks_sync_name_all_companies',
    )
    for field_name in stale:
        if not column_exists(cr, 'account_account', field_name):
            cr.execute(
                "DELETE FROM ir_model_fields WHERE model = 'account.account' AND name = %s",
                (field_name,),
            )
            if cr.rowcount:
                _logger.info('CPABooks CoA: removed stale field entry account.account.%s', field_name)


def post_init_hook(cr, registry):
    from odoo import api, SUPERUSER_ID

    _ensure_account_account_cpabooks_columns(cr)
    _drop_account_code_unique_per_company(cr)
    _ensure_res_company_coa_code_digits(cr)
    env = api.Environment(cr, SUPERUSER_ID, {})
    _init_coa_wizard_tables(env)
    _restore_partner_accounts(env)
    _recover_ifrs_temp_codes(env)
    _ensure_default_coa_for_companies(env)
    env['account.group'].action_cpa_reset_account_groups()
