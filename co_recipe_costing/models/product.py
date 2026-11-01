# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    recipe_ids = fields.One2many('cpabooks.recipe', 'product_tmpl_id', string='Recipes')
    recipe_id = fields.Many2one(
        'cpabooks.recipe', string='Recipe', compute='_compute_recipe_id', store=True,
    )
    recipe_category = fields.Selection(related='recipe_id.category', readonly=False)
    recipe_menu_price = fields.Float(related='recipe_id.menu_price', readonly=False)
    recipe_food_cost = fields.Monetary(
        related='recipe_id.standard_cost', string='Food Cost', readonly=True,
        currency_field='currency_id',
    )
    recipe_cost_pct = fields.Float(
        related='recipe_id.potential_cost_pct', string='Food Cost %', readonly=True,
    )
    recipe_line_ids = fields.One2many(related='recipe_id.line_ids', readonly=False, string='Ingredients')

    @api.depends('recipe_ids', 'recipe_ids.is_demo')
    def _compute_recipe_id(self):
        for product in self:
            actual = product.recipe_ids.filtered(lambda recipe: not recipe.is_demo)[:1]
            product.recipe_id = actual or product.recipe_ids[:1]

    def action_add_recipe(self):
        self.ensure_one()
        if self.recipe_id:
            return True
        variant = self.product_variant_id or self.product_variant_ids[:1]
        if not variant:
            raise UserError(_('Save the product first, then add the recipe.'))
        self.env['cpabooks.recipe'].create({
            'name': self.name,
            'sale_product_id': variant.id,
            'company_id': self.company_id.id or self.env.company.id,
            'menu_price': self.list_price,
        })
        return True
