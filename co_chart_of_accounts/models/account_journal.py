# -*- coding: utf-8 -*-
from odoo import api, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    @api.model
    def _coa_unique_journal_code(self, coa, exclude_journal=None):
        initials = ''.join(
            word[0] for word in (coa.name or '').split() if word
        ).upper()
        base_code = (initials or 'JRN')[:5]
        candidate = base_code
        sequence = 2
        domain = [
            ('company_id', '=', coa.company_id.id),
            ('code', '=', candidate),
        ]
        if exclude_journal:
            domain.append(('id', '!=', exclude_journal.id))
        while self.sudo().search_count(domain):
            suffix = str(sequence)
            candidate = '%s%s' % (base_code[:5 - len(suffix)], suffix)
            domain[1] = ('code', '=', candidate)
            sequence += 1
        return candidate

    @api.model
    def create_journals_from_coa(self, *args, **kwargs):
        """One bank or cash journal per Bank and Cash ledger; existing journals are updated."""
        all_coas = self.env['account.account'].search([
            ('user_type_id.name', 'ilike', 'Bank and Cash'),
            '|',
            ('name', 'ilike', 'bank'),
            ('name', 'ilike', 'cash')
        ])

        for coa in all_coas:
            existing_journal = self.sudo().search([
                ('company_id', '=', coa.company_id.id),
                '|', '|',
                ('default_account_id', '=', coa.id),
                ('payment_debit_account_id', '=', coa.id),
                ('payment_credit_account_id', '=', coa.id),
            ], limit=1)

            journal_type = 'bank' if 'bank' in (coa.name or '').lower() else 'cash'
            code = self._coa_unique_journal_code(coa, existing_journal)
            values = {
                'name': coa.name,
                'type': journal_type,
                'company_id': coa.company_id.id,
                'default_account_id': coa.id,
                'code': code,
                'payment_debit_account_id': coa.id,
                'payment_credit_account_id': coa.id,
            }

            if existing_journal:
                existing_journal.write(values)
                continue

            self.sudo().with_company(coa.company_id).with_context(
                allowed_company_ids=[coa.company_id.id],
            ).create(values)
        return True
