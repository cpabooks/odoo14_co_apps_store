# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ClosingWizard(models.TransientModel):
    _name = 'cpabooks.recipe.closing.wizard'
    _description = 'Create Daily Closing Lines'

    date = fields.Date(default=fields.Date.context_today, required=True)
    branch = fields.Selection(selection='_branch_choices', required=True)

    @api.model
    def _branch_choices(self):
        return [(company.name, company.name) for company in self.env.user.company_ids]

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if 'branch' in fields_list and not values.get('branch'):
            values['branch'] = self.env.company.name
        return values

    def action_create(self):
        company = self.env['res.company'].search([('name', '=', self.branch)], limit=1) or self.env.company
        products = self.env['cpabooks.recipe.line'].search([
            ('recipe_id.company_id', '=', company.id),
        ]).mapped('product_id')
        Closing = self.env['cpabooks.recipe.closing']
        for product in products:
            Closing.create({
                'date': self.date,
                'branch': self.branch,
                'company_id': company.id,
                'product_id': product.id,
                'actual_closing_qty': 0,
            })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cpabooks.recipe.closing',
            'view_mode': 'tree,form',
            'domain': [('date', '=', self.date), ('branch', '=', self.branch)],
        }
