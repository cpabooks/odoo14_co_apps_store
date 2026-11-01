# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class DailyClosing(models.Model):
    _name='cpabooks.recipe.closing'; _description='Daily Ingredient Closing Stock'; _order='date desc, branch, product_id'
    date=fields.Date(required=True,default=fields.Date.context_today); company_id=fields.Many2one('res.company',default=lambda s:s.env.company,required=True)
    branch=fields.Char(required=True); product_id=fields.Many2one('product.product',required=True,string='Ingredient')
    uom_id=fields.Many2one(related='product_id.uom_id',store=True); opening_qty=fields.Float(); purchase_qty=fields.Float(); transfer_in_qty=fields.Float(); transfer_out_qty=fields.Float(); waste_qty=fields.Float()
    actual_closing_qty=fields.Float(string='Chef Closing Qty',required=True); actual_consumption=fields.Float(compute='_calc',store=True)
    theoretical_consumption=fields.Float(string='Expected from Sales'); expected_closing_qty=fields.Float(compute='_calc',store=True); variance_qty=fields.Float(compute='_calc',store=True); variance_pct=fields.Float(compute='_calc',store=True)
    state=fields.Selection([('ok','OK'),('warning','Check'),('variance','Variance')],compute='_calc',store=True)
    is_demo = fields.Boolean(string='Sample', default=False, index=True)
    def name_get(self):
        result = []
        for row in self:
            product = row.product_id.display_name or ''
            when = row.date and fields.Date.to_string(row.date) or ''
            result.append((row.id, (when + ' ' + product).strip() or 'Closing'))
        return result
    @api.depends('opening_qty','purchase_qty','transfer_in_qty','transfer_out_qty','waste_qty','actual_closing_qty','theoretical_consumption')
    def _calc(self):
      for r in self:
        available=r.opening_qty+r.purchase_qty+r.transfer_in_qty-r.transfer_out_qty-r.waste_qty
        r.actual_consumption=available-r.actual_closing_qty
        r.expected_closing_qty=available-r.theoretical_consumption
        r.variance_qty=r.actual_consumption-r.theoretical_consumption
        r.variance_pct=r.theoretical_consumption and r.variance_qty/r.theoretical_consumption*100 or 0
        a=abs(r.variance_pct); r.state='ok' if a<=3 else ('warning' if a<=8 else 'variance')

class ConsumptionAnalysis(models.Model):
    _name='cpabooks.recipe.consumption'; _description='Recipe Consumption Analysis'; _auto=False
    date=fields.Date(); company_id=fields.Many2one('res.company'); branch=fields.Char(); recipe_id=fields.Many2one('cpabooks.recipe'); sale_product_id=fields.Many2one('product.product'); ingredient_id=fields.Many2one('product.product')
    sold_qty=fields.Float(); recipe_qty=fields.Float(); theoretical_qty=fields.Float(); unit_cost=fields.Float(); theoretical_cost=fields.Float(); sales_value=fields.Float(); potential_cost_pct=fields.Float()
    origin = fields.Char(string='Source')
    category = fields.Selection([
        ('sushi', 'Sushi'), ('buffet', 'Buffet'), ('japanese', 'Japanese'),
        ('arabic', 'Arabic'), ('other', 'Other'), ('none', 'No recipe'),
    ], string='Sales Category')
    def init(self):
      self.env.cr.execute('DROP VIEW IF EXISTS cpabooks_recipe_consumption CASCADE')
      self.env.cr.execute('''CREATE VIEW cpabooks_recipe_consumption AS (
        SELECT row_number() OVER () AS id, src.date, src.company_id, src.branch, src.recipe_id,
               src.sale_product_id, src.ingredient_id, src.sold_qty, src.recipe_qty,
               src.theoretical_qty, src.unit_cost, src.theoretical_cost, src.sales_value,
               src.potential_cost_pct, src.origin, src.category
        FROM (
          SELECT (so.date_order AT TIME ZONE 'UTC' AT TIME ZONE COALESCE(NULLIF(cp.tz, ''), 'UTC'))::date AS date,
                 so.company_id, r.branch, r.id AS recipe_id,
                 sol.product_id AS sale_product_id, rl.product_id AS ingredient_id,
                 sum(sol.product_uom_qty) AS sold_qty, rl.qty AS recipe_qty,
                 sum(sol.product_uom_qty * rl.qty) AS theoretical_qty,
                 max(coalesce(rl.unit_cost, 0)) AS unit_cost,
                 sum(sol.product_uom_qty * coalesce(rl.line_cost, 0)) AS theoretical_cost,
                 sum(sol.price_subtotal) AS sales_value,
                 CASE WHEN sum(sol.price_subtotal) <> 0
                      THEN sum(sol.product_uom_qty * coalesce(rl.line_cost, 0)) / sum(sol.price_subtotal) * 100
                      ELSE 0 END AS potential_cost_pct,
                 'Posted sale' AS origin,
                 coalesce(r.category, 'other') AS category
          FROM sale_order_line sol
          JOIN sale_order so ON so.id = sol.order_id
          JOIN cpabooks_recipe r ON r.sale_product_id = sol.product_id
          JOIN cpabooks_recipe_line rl ON rl.recipe_id = r.id
          LEFT JOIN res_company co ON co.id = so.company_id
          LEFT JOIN res_partner cp ON cp.id = co.partner_id
          WHERE so.state IN ('sale', 'done')
          GROUP BY (so.date_order AT TIME ZONE 'UTC' AT TIME ZONE COALESCE(NULLIF(cp.tz, ''), 'UTC'))::date,
                   so.company_id, r.branch, r.id, sol.product_id, rl.product_id, rl.qty, cp.tz
          UNION ALL
          SELECT DATE '2026-08-28', r.company_id, r.branch, r.id, r.sale_product_id, rl.product_id,
                 r.sample_sold_qty, rl.budget_qty,
                 r.sample_sold_qty * rl.qty,
                 rl.budget_unit_cost,
                 r.sample_sold_qty * rl.budget_line_cost,
                 r.sample_sold_qty * coalesce(r.menu_price, 0),
                 CASE WHEN coalesce(r.menu_price, 0) <> 0
                      THEN (rl.budget_line_cost / r.menu_price) * 100 ELSE 0 END,
                 'Sample sheet',
                 coalesce(r.category, 'other')
          FROM cpabooks_recipe r
          JOIN cpabooks_recipe_line rl ON rl.recipe_id = r.id
          WHERE coalesce(r.sample_sold_qty, 0) <> 0
          UNION ALL
          SELECT (so.date_order AT TIME ZONE 'UTC' AT TIME ZONE COALESCE(NULLIF(cp.tz, ''), 'UTC'))::date,
                 so.company_id, c.name, NULL::integer, sol.product_id, NULL::integer,
                 sol.product_uom_qty, 0, 0, 0, 0, sol.price_subtotal, 0,
                 'Sale, no recipe',
                 'none'
          FROM sale_order_line sol
          JOIN sale_order so ON so.id = sol.order_id
          JOIN res_company c ON c.id = so.company_id
          LEFT JOIN res_partner cp ON cp.id = c.partner_id
          WHERE so.state IN ('sale', 'done')
            AND NOT EXISTS (
              SELECT 1 FROM cpabooks_recipe r WHERE r.sale_product_id = sol.product_id
            )
        ) src
      )''')
