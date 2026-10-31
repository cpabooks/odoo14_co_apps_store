# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.sql import column_exists, create_column


class AccountAccountCorrespondent(models.Model):
    _inherit = 'account.account'

    correspondent_account_id = fields.Many2one(
        'account.account',
        string='Correspondent Dr/Cr Ledger',
        index=True,
        ondelete='set null',
        domain="[('company_id', '=', company_id), ('deprecated', '=', False), ('id', '!=', id)]",
        help='Paired P&L / Balance Sheet ledger. Set on either account; both sides stay in sync.',
    )

    def _auto_init(self):
        if not column_exists(self.env.cr, 'account_account', 'correspondent_account_id'):
            create_column(self.env.cr, 'account_account', 'correspondent_account_id', 'int4')
        return super()._auto_init()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('skip_correspondent_sync'):
            records._sync_correspondent_pair()
        return records

    def write(self, vals):
        old_ids = {}
        if 'correspondent_account_id' in vals:
            for rec in self:
                old_ids[rec.id] = rec.correspondent_account_id.id
        res = super().write(vals)
        if 'correspondent_account_id' in vals and not self.env.context.get('skip_correspondent_sync'):
            self._sync_correspondent_pair(old_ids)
        return res

    def _sync_correspondent_pair(self, old_ids=None):
        old_ids = old_ids or {}
        Account = self.env['account.account'].with_context(skip_correspondent_sync=True)
        for rec in self:
            new = rec.correspondent_account_id
            if new and new.id == rec.id:
                raise UserError(_('A ledger cannot be its own Correspondent Dr/Cr Ledger.'))
            old_id = old_ids.get(rec.id)
            if old_id and old_id != (new.id if new else False):
                old = Account.browse(old_id)
                if old.exists() and old.correspondent_account_id.id == rec.id:
                    old.correspondent_account_id = False
            if not new:
                continue
            prev = new.correspondent_account_id
            if prev and prev.id != rec.id and prev.correspondent_account_id.id == new.id:
                Account.browse(prev.id).correspondent_account_id = False
            if new.correspondent_account_id.id != rec.id:
                new.correspondent_account_id = rec.id
