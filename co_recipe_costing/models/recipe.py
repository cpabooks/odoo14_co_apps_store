# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class RecipeBook(models.Model):
    _name = 'cpabooks.recipe'
    _description = 'Recipe Book'
    _inherit = ['mail.thread'] if False else []
    _order = 'name'

    name = fields.Char(required=True, tracking=False)
    code = fields.Char()
    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company)
    branch = fields.Char(help='Branch/location name. Kept generic for Odoo 14 CE/EE compatibility.')
    sale_product_id = fields.Many2one('product.product', string='Sales Item', required=True, domain=[('sale_ok','=',True)])
    product_tmpl_id = fields.Many2one(
        'product.template', compute='_compute_product_tmpl_id', store=True, index=True,
        string='Product',
    )
    image_1920 = fields.Image(string='Menu Image')
    category = fields.Selection([
        ('sushi', 'Sushi'), ('buffet', 'Buffet'), ('japanese', 'Japanese'),
        ('arabic', 'Arabic'), ('other', 'Other'),
    ], default='other')
    is_demo = fields.Boolean(string='Sample', default=False, index=True, readonly=True)
    cloned_from_id = fields.Many2one('cpabooks.recipe', string='Cloned From', readonly=True, copy=False)
    menu_price = fields.Float(string='Menu Price', digits='Product Price')
    budget_cost = fields.Monetary(
        compute='_compute_cost', store=True, currency_field='currency_id', string='Budget Cost',
    )
    budget_cost_pct = fields.Float(
        compute='_compute_cost', store=True, string='Budget Food Cost %',
    )
    budget_margin = fields.Monetary(
        compute='_compute_cost', store=True, currency_field='currency_id', string='Budget Margin',
    )
    sample_sold_qty = fields.Float(string='Sample Sold Qty')
    sample_food_cost_total = fields.Float(string='Sample Food Cost Total', digits='Product Price')
    portion_qty = fields.Float(default=1.0, string='Portion / Sale Qty')
    line_ids = fields.One2many('cpabooks.recipe.line','recipe_id', string='Ingredients')
    currency_id = fields.Many2one(related='company_id.currency_id', store=True)
    standard_cost = fields.Monetary(compute='_compute_cost', store=True, currency_field='currency_id', string='Actual Food Cost')
    selling_price = fields.Float(
        related='sale_product_id.lst_price', readonly=True,
        string='Selling Price', digits='Product Price',
    )
    potential_cost_pct = fields.Float(compute='_compute_cost', store=True, string='Potential Food Cost %')
    margin = fields.Monetary(compute='_compute_cost', store=True, currency_field='currency_id')
    active = fields.Boolean(default=True)
    notes = fields.Text()

    @api.depends('sale_product_id', 'sale_product_id.product_tmpl_id')
    def _compute_product_tmpl_id(self):
        for recipe in self:
            recipe.product_tmpl_id = recipe.sale_product_id.product_tmpl_id

    @api.depends(
        'line_ids.qty', 'line_ids.unit_cost', 'line_ids.budget_line_cost',
        'sale_product_id.lst_price', 'menu_price',
    )
    def _compute_cost(self):
        for r in self:
            r.standard_cost = sum(r.line_ids.mapped('line_cost'))
            r.budget_cost = sum(r.line_ids.mapped('budget_line_cost'))
            price = r.menu_price or r.selling_price
            r.margin = price - r.standard_cost
            r.potential_cost_pct = price and (r.standard_cost / price * 100.0) or 0.0
            r.budget_margin = price - r.budget_cost
            r.budget_cost_pct = price and (r.budget_cost / price * 100.0) or 0.0

    def action_clone_to_actual(self):
        """Copy a sample recipe into an actual recipe that can be edited."""
        self.ensure_one()
        new = self.copy(default={
            'is_demo': False,
            'cloned_from_id': self.id,
            'name': self.name,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Actual Recipe'),
            'res_model': 'cpabooks.recipe',
            'view_mode': 'form',
            'res_id': new.id,
            'target': 'current',
        }

    def action_open_clone_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Clone from Demo'),
            'res_model': 'cpabooks.recipe.clone.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_sales(self):
        self.ensure_one()
        return {'type':'ir.actions.act_window','name':_('Sales Lines'),'res_model':'sale.order.line','view_mode':'tree,form','domain':[('product_id','=',self.sale_product_id.id),('order_id.state','in',['sale','done'])]}

class RecipeLine(models.Model):
    _name = 'cpabooks.recipe.line'
    _description = 'Recipe Ingredient'
    _order = 'sequence,id'
    sequence = fields.Integer(default=10)
    recipe_id = fields.Many2one('cpabooks.recipe', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Ingredient / Prep Item', required=True, domain=[('purchase_ok','=',True)])
    qty = fields.Float(required=True, digits=(16, 4))
    uom_id = fields.Many2one('uom.uom', required=True)
    unit_cost = fields.Float(
        compute='_compute_line_cost', store=True, string='Actual Cost', digits='Product Price',
    )
    line_cost = fields.Float(
        compute='_compute_line_cost', store=True, string='Actual Line Cost', digits='Product Price',
    )
    budget_qty = fields.Float(string='Kitchen Qty', digits=(16, 4))
    budget_uom = fields.Char(string='Kitchen UOM')
    budget_unit_cost = fields.Float(string='Budget Price', digits='Product Price')
    budget_line_cost = fields.Float(string='Budget Cost', compute='_compute_budget_line', store=True)
    link_note = fields.Char(string='Inventory Link')

    @api.depends('budget_qty', 'budget_unit_cost')
    def _compute_budget_line(self):
        for line in self:
            line.budget_line_cost = line.budget_qty * line.budget_unit_cost
    @api.depends('qty', 'product_id', 'recipe_id.company_id')
    def _compute_line_cost(self):
        costs = self._book_unit_costs(self, lambda line: line.recipe_id.company_id.id)
        for line in self:
            unit = costs.get(line.id, 0.0)
            line.unit_cost = unit
            line.line_cost = (line.qty or 0.0) * unit

    @api.model
    def _purchase_avg_cost(self, product_ids, company_id):
        """Weighted average of posted purchase lines, per product UOM."""
        if not product_ids:
            return {}
        cr = self.env.cr
        cr.execute("""
            SELECT pol.product_id,
                   SUM(pol.price_subtotal) / NULLIF(SUM(pol.product_qty), 0)
            FROM purchase_order_line pol
            JOIN purchase_order po ON po.id = pol.order_id
            WHERE pol.product_id IN %s
              AND po.state IN ('purchase', 'done')
              AND po.company_id = %s
              AND pol.product_qty > 0
            GROUP BY pol.product_id
        """, [tuple(product_ids), company_id or 0])
        found = {row[0]: row[1] or 0.0 for row in cr.fetchall()}
        missing = [pid for pid in product_ids if not found.get(pid)]
        if not missing:
            return found
        cr.execute("""
            SELECT pol.product_id,
                   SUM(pol.price_subtotal) / NULLIF(SUM(pol.product_qty), 0)
            FROM purchase_order_line pol
            JOIN purchase_order po ON po.id = pol.order_id
            WHERE pol.product_id IN %s
              AND po.state IN ('purchase', 'done')
              AND pol.product_qty > 0
            GROUP BY pol.product_id
        """, [tuple(missing)])
        for product_id, cost in cr.fetchall():
            found[product_id] = cost or 0.0
        return found

    @api.model
    def _book_unit_costs(self, lines, company_of):
        """Product cost on the company, otherwise the purchase average already in the books."""
        grouped = {}
        for line in lines:
            company_id = company_of(line) or self.env.company.id
            grouped.setdefault(company_id, []).append(line)
        costs = {}
        Product = self.env['product.product']
        for company_id, group in grouped.items():
            product_ids = list({line.product_id.id for line in group if line.product_id})
            purchase = self._purchase_avg_cost(product_ids, company_id)
            products = Product.browse(product_ids).with_context(force_company=company_id)
            standard = {product.id: product.standard_price or 0.0 for product in products}
            for line in group:
                product_id = line.product_id.id
                costs[line.id] = standard.get(product_id) or purchase.get(product_id) or 0.0
        return costs

    @api.model
    def _recompute_book_costs(self):
        self.search([]).modified(['product_id'])
        self.env['cpabooks.prep.recipe.line'].search([]).modified(['product_id'])
        self.recompute()
        self.env['cpabooks.recipe'].search([]).modified(['line_ids'])
        self.env['cpabooks.prep.recipe'].search([]).modified(['line_ids'])
        self.recompute()

class PrepRecipe(models.Model):
    _name='cpabooks.prep.recipe'; _description='Prep / Sub Recipe'
    name=fields.Char(required=True); code=fields.Char(); company_id=fields.Many2one('res.company',default=lambda s:s.env.company,required=True)
    is_demo = fields.Boolean(string='Sample', default=False, index=True, readonly=True)
    product_id=fields.Many2one('product.product',string='Prep Product',required=True)
    batch_yield=fields.Float(required=True,default=1.0); uom_id=fields.Many2one('uom.uom',required=True)
    line_ids=fields.One2many('cpabooks.prep.recipe.line','prep_id')
    batch_cost=fields.Float(compute='_cost',store=True); unit_cost=fields.Float(compute='_cost',store=True)
    @api.depends('line_ids.line_cost','batch_yield')
    def _cost(self):
        for r in self:
            r.batch_cost=sum(r.line_ids.mapped('line_cost')); r.unit_cost=r.batch_yield and r.batch_cost/r.batch_yield or 0
class PrepRecipeLine(models.Model):
    _name='cpabooks.prep.recipe.line'; _description='Prep Recipe Ingredient'
    prep_id=fields.Many2one('cpabooks.prep.recipe',required=True,ondelete='cascade'); product_id=fields.Many2one('product.product',required=True)
    qty=fields.Float(required=True); uom_id=fields.Many2one('uom.uom',required=True)
    unit_cost=fields.Float(compute='_c', store=True, string='Actual Cost', digits='Product Price')
    line_cost=fields.Float(compute='_c', store=True, string='Actual Line Cost', digits='Product Price')
    @api.depends('qty', 'product_id', 'prep_id.company_id')
    def _c(self):
        costs = self.env['cpabooks.recipe.line']._book_unit_costs(
            self, lambda line: line.prep_id.company_id.id,
        )
        for line in self:
            unit = costs.get(line.id, 0.0)
            line.unit_cost = unit
            line.line_cost = (line.qty or 0.0) * unit
