# -*- coding: utf-8 -*-
from odoo import api, fields, models


class RecipeStatus(models.Model):
    _inherit = 'cpabooks.recipe'

    @api.model
    def get_status_dashboard(self):
        company = self.env.company
        recipes = self.search([('company_id', '=', company.id)])
        priced = recipes.filtered(lambda recipe: recipe.menu_price)
        preps = self.env['cpabooks.prep.recipe'].search_count([('company_id', '=', company.id)])
        closings = self.env['cpabooks.recipe.closing'].search([('company_id', '=', company.id)])

        def money(value):
            return '%.2f' % (value or 0.0)

        def avg(records, field):
            if not records:
                return 0.0
            return sum(records.mapped(field)) / len(records)

        sample_sales = sum((recipe.sample_sold_qty or 0.0) * (recipe.menu_price or 0.0) for recipe in recipes)
        sample_food = sum((recipe.sample_sold_qty or 0.0) * (recipe.budget_cost or 0.0) for recipe in recipes)
        actual_food = sum((recipe.sample_sold_qty or 0.0) * (recipe.standard_cost or 0.0) for recipe in recipes)

        menu_rows = []
        for recipe in priced.sorted(key=lambda item: item.potential_cost_pct or 0.0, reverse=True)[:8]:
            menu_rows.append({
                'id': recipe.id,
                'name': recipe.name,
                'price': money(recipe.menu_price),
                'budget': money(recipe.budget_cost),
                'actual': money(recipe.standard_cost),
                'budget_pct': '%.1f' % (recipe.budget_cost_pct or 0.0),
                'actual_pct': '%.1f' % (recipe.potential_cost_pct or 0.0),
                'sold': '%.0f' % (recipe.sample_sold_qty or 0.0),
                'width': min(recipe.potential_cost_pct or 0.0, 100.0),
            })

        categories = {}
        for recipe in recipes:
            key = recipe.category or 'other'
            label = dict(self._fields['category'].selection).get(key, key)
            bucket = categories.setdefault(key, {'name': label, 'cost': 0.0, 'count': 0})
            bucket['cost'] += recipe.budget_cost or 0.0
            bucket['count'] += 1
        max_cost = max([row['cost'] for row in categories.values()] or [1.0]) or 1.0
        category_bars = [{
            'key': key,
            'name': row['name'],
            'cost': money(row['cost']),
            'count': row['count'],
            'width': (row['cost'] / max_cost) * 100.0,
        } for key, row in sorted(categories.items(), key=lambda item: item[1]['cost'], reverse=True)]

        variance_rows = []
        flagged = closings.filtered(lambda line: line.state != 'ok')
        ordered = flagged.sorted(key=lambda line: abs(line.variance_qty or 0.0), reverse=True)[:8]
        if not ordered:
            ordered = closings.sorted(key=lambda line: abs(line.variance_qty or 0.0), reverse=True)[:8]
        for line in ordered:
            variance_rows.append({
                'id': line.id,
                'product': line.product_id.display_name,
                'expected': '%.2f' % (line.theoretical_consumption or 0.0),
                'actual': '%.2f' % (line.actual_consumption or 0.0),
                'variance': '%.2f' % (line.variance_qty or 0.0),
                'state': line.state or 'ok',
            })

        store_rows = []
        purchased = closings.filtered(lambda line: (line.purchase_qty or 0.0) > 0)
        for line in purchased.sorted(key=lambda item: item.purchase_qty or 0.0, reverse=True)[:8]:
            store_rows.append({
                'id': line.id,
                'product': line.product_id.display_name,
                'purchase': '%.2f' % (line.purchase_qty or 0.0),
                'expected': '%.2f' % (line.theoretical_consumption or 0.0),
                'closing': '%.2f' % (line.actual_closing_qty or 0.0),
                'matched': bool(line.theoretical_consumption),
            })
        unmatched = purchased.filtered(lambda line: not line.theoretical_consumption)
        period, period_note = self._status_period(company, closings)

        return {
            'company': company.name,
            'company_id': company.id,
            'period': period,
            'period_note': period_note,
            'management': {
                'recipes': len(recipes),
                'priced': len(priced),
                'preps': preps,
                'avg_budget_pct': '%.1f' % avg(priced, 'budget_cost_pct'),
                'avg_actual_pct': '%.1f' % avg(priced, 'potential_cost_pct'),
                'sample_sales': money(sample_sales),
                'sample_food': money(sample_food),
                'actual_food': money(actual_food),
                'margin': money(sample_sales - actual_food),
                'rows': menu_rows,
                'bars': category_bars,
            },
            'chef': {
                'lines': len(closings),
                'ok': len(closings.filtered(lambda line: line.state == 'ok')),
                'check': len(closings.filtered(lambda line: line.state == 'warning')),
                'variance': len(closings.filtered(lambda line: line.state == 'variance')),
                'rows': variance_rows,
            },
            'store': {
                'purchased': len(purchased),
                'unmatched': len(unmatched),
                'purchase_qty': '%.2f' % sum(purchased.mapped('purchase_qty')),
                'rows': store_rows,
            },
        }

    @api.model
    def _status_period(self, company, closings):
        def show(day):
            day = fields.Date.to_date(day)
            return day.strftime('%d %b %Y') if day else ''

        days = sorted(set(closings.mapped('date')))
        if not days:
            period = 'No closing date loaded'
        elif len(days) == 1:
            period = 'Sample day %s' % show(days[0])
        else:
            period = 'Sample days %s to %s' % (show(days[0]), show(days[-1]))

        posted_sales = self.env['sale.order'].search_count([
            ('company_id', '=', company.id),
            ('state', 'in', ('sale', 'done')),
        ])
        purchase_span = ''
        product_ids = closings.mapped('product_id').ids
        if product_ids:
            self.env.cr.execute("""
                SELECT MIN(po.date_order)::date, MAX(po.date_order)::date
                FROM purchase_order_line pol
                JOIN purchase_order po ON po.id = pol.order_id
                WHERE po.state IN ('purchase', 'done')
                  AND pol.product_id IN %s
            """, [tuple(product_ids)])
            start, end = self.env.cr.fetchone()
            if start and end:
                purchase_span = '%s to %s' % (show(start), show(end))

        note = (
            'Sales AED, food AED and margin use the sample sold qty for that day, '
            'times menu price and recipe cost. They are not posted sale orders'
        )
        note += ' (this company has none).' if not posted_sales else ' (%s posted sale orders exist and are not in these totals).' % posted_sales
        note += ' Food-cost % is the current recipe card, not a month.'
        if purchase_span:
            note += ' Purchase qty is every posted purchase order from %s, not cut to the sample day.' % purchase_span
        else:
            note += ' Purchase qty is every posted purchase order, not cut to the sample day.'
        return period, note

    @api.model
    def _link_daily_report_menus(self):
        reports = self.env.ref('co_recipe_costing.menu_daily_reports', raise_if_not_found=False)
        closing = self.env.ref('co_recipe_costing.menu_daily_closing_stock', raise_if_not_found=False)
        if not reports:
            return
        links = (
            ('cpabooks_daily_reports.action_daily_control_report_wizard', 'Daily Control Report', 1, reports),
            ('cpabooks_daily_reports.action_daily_transaction_report', 'Daily Transaction Report', 2, reports),
            ('cpabooks_daily_reports.action_daily_sales_analysis_report', 'Daily Sales Analysis', 3, reports),
            ('cpabooks_daily_reports.action_daily_invoice_report', 'Daily Invoice Report', 4, reports),
            ('cpabooks_daily_reports.action_daily_goods_dashboard', 'Run Daily Goods Report', 1, closing or reports),
            ('cpabooks_daily_reports.action_goods_in_dashboard', 'Run goods in report', 2, closing or reports),
            ('cpabooks_daily_reports.action_goods_out_dashboard', 'Run goods out report', 3, closing or reports),
        )
        Menu = self.env['ir.ui.menu'].sudo()
        Data = self.env['ir.model.data'].sudo()
        for xmlid, name, sequence, parent in links:
            action = self.env.ref(xmlid, raise_if_not_found=False)
            if not action:
                continue
            data_name = 'menu_daily_' + xmlid.split('.')[-1]
            existing = self.env.ref('co_recipe_costing.' + data_name, raise_if_not_found=False)
            vals = {
                'name': name,
                'parent_id': parent.id,
                'action': '%s,%s' % (action._name, action.id),
                'sequence': sequence,
            }
            if existing:
                existing.sudo().write(vals)
                continue
            menu = Menu.create(vals)
            Data.create({
                'name': data_name,
                'module': 'co_recipe_costing',
                'model': 'ir.ui.menu',
                'res_id': menu.id,
                'noupdate': True,
            })
