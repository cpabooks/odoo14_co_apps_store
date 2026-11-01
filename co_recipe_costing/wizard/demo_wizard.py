# -*- coding: utf-8 -*-
from odoo import fields, models, _


class RecipeDemoWizard(models.TransientModel):
    _name = 'cpabooks.recipe.demo.wizard'
    _description = 'Load or clear Recipe Book sample data'

    def action_load(self):
        message = self.env['cpabooks.recipe'].action_load_demo_data()
        return self._open(True, message)

    def action_clear(self):
        message = self.env['cpabooks.recipe'].action_clear_demo_data()
        return self._open(False, message)

    def _open(self, demo, message):
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Sample Recipes') if demo else _('Menu Book'),
            'res_model': 'cpabooks.recipe',
            'view_mode': 'tree,form',
            'domain': [('is_demo', '=', demo)],
            'target': 'current',
        }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recipe Book'),
                'message': message,
                'sticky': True,
                'type': 'success',
                'next': action,
            },
        }


class RecipeCloneWizard(models.TransientModel):
    _name = 'cpabooks.recipe.clone.wizard'
    _description = 'Clone a sample recipe into an actual recipe'

    demo_recipe_id = fields.Many2one(
        'cpabooks.recipe', string='Sample Recipe', required=True,
        domain=[('is_demo', '=', True)],
    )

    def action_clone(self):
        self.ensure_one()
        return self.demo_recipe_id.action_clone_to_actual()
