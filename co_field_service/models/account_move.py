# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Mirror PT v1 delivery print toggles so FSM upgrades succeed when PT
    # views are newer than PT Python on the server (live partial deploy).
    show_delivery_mode = fields.Boolean(string='Show Delivery Mode', default=False)
    show_delivery_person = fields.Boolean(string='Show Delivery Person', default=False)

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._cpabooks_refresh_linked_fsm_tasks()
        return moves

    def write(self, vals):
        res = super().write(vals)
        if {'state', 'name', 'move_type'} & set(vals):
            self._cpabooks_refresh_linked_fsm_tasks()
        return res

    def _cpabooks_refresh_linked_fsm_tasks(self):
        if not self.env.registry.get('sale.order'):
            return
        orders = self.env['sale.order'].search([
            ('invoice_ids', 'in', self.ids),
            ('task_id', '!=', False),
        ])
        tasks = orders.mapped('task_id').filtered('is_fsm')
        if tasks and hasattr(tasks, '_cpabooks_refresh_fsm_quotation_display'):
            tasks._cpabooks_refresh_fsm_quotation_display()
