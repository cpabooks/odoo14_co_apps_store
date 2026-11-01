# -*- coding: utf-8 -*-
"""Samurai sample recipes: budget costing linked to purchased products."""
import base64
import logging
import os
import re
from io import BytesIO

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

# pack_size = kitchen units inside one inventory unit.
# Stock qty on the recipe line = kitchen qty / pack_size.
INGREDIENTS = (
    {'key': 'beef', 'label': 'Brazilian Beef', 'names': ['CHILLED BEEF CUBEROLL BRAZIL'], 'uom': 'kg', 'price': 40.00, 'pack': 1.0},
    {'key': 'chicken', 'label': 'Chicken thigh', 'names': ['CHICKEN THIGH'], 'uom': 'kg', 'price': 22.00, 'pack': 1.0},
    {'key': 'salmon', 'label': 'Salmon', 'names': ['SALMON'], 'uom': 'kg', 'price': 66.00, 'pack': 1.0},
    {'key': 'cheese', 'label': 'Cheese', 'names': ['PHILADELPHIA CHEESE 1.65'], 'uom': 'kg', 'price': 24.00, 'pack': 1.65},
    {'key': 'rice', 'label': 'Rice', 'names': ['JAPONICA RICE 25 KG', 'CALROSE RICE'], 'uom': 'kg', 'price': 12.00, 'pack': 25.0},
    {'key': 'nori', 'label': 'Nori', 'names': ['SUSHI NORI STANDARD 50PCS'], 'uom': 'pcs', 'price': 0.70, 'pack': 50.0},
    {'key': 'avocado', 'label': 'Avocado', 'names': ['AVOCADO'], 'uom': 'kg', 'price': 25.00, 'pack': 1.0},
    {'key': 'shrimp', 'label': 'Shrimp', 'names': ['FROZEN SHRIMPS 8x12 WITH TAIL'], 'uom': 'kg', 'price': 32.00, 'pack': 1.0},
    {'key': 'crab', 'label': 'Crabsticks', 'names': ['CRAB STICKS 500 GRM'], 'uom': 'pcs', 'price': 1.30, 'pack': 30.0},
    {'key': 'cucumber', 'label': 'Cucumber', 'names': ['CUCUMBER'], 'uom': 'kg', 'price': 4.00, 'pack': 1.0},
    {'key': 'smoked', 'label': 'Smoked salmon', 'names': ['SMOKE SALMON FILLET'], 'uom': 'kg', 'price': 68.00, 'pack': 1.0},
    {'key': 'shitake', 'label': 'Sweet Dry Shitake', 'names': ['SHITAKE MUSHROOM DRY'], 'uom': 'kg', 'price': 75.00, 'pack': 1.0},
    {'key': 'tobiko', 'label': 'Tobiko', 'names': ['TOBIKO 500G'], 'uom': 'kg', 'price': 140.00, 'pack': 0.5},
    {'key': 'egg', 'label': 'Egg', 'names': ['EGG'], 'uom': 'pcs', 'price': 1.00, 'pack': 1.0},
    {'key': 'tuna', 'label': 'Tuna', 'names': ['TUNA FISH', 'TUNA'], 'uom': 'kg', 'price': 55.00, 'pack': 1.0},
    {'key': 'mayo', 'label': 'Mayo', 'names': ['QP MAYONNAISE'], 'uom': 'kg', 'price': 30.00, 'pack': 1.0},
    {'key': 'spring_onion', 'label': 'Spring Onion', 'names': ['SPRING ONION'], 'uom': 'kg', 'price': 8.00, 'pack': 1.0},
    {'key': 'soya', 'label': 'Soya Sauce', 'names': ['KIKOMEN SOYA SAUCE 10 LTR'], 'uom': 'ltr', 'price': 21.00, 'pack': 10.0},
    {'key': 'ginger', 'label': 'Ginger', 'names': ['Ginger'], 'uom': 'kg', 'price': 13.00, 'pack': 1.0},
    {'key': 'wasabi', 'label': 'Wasabi', 'names': ['WASABI POWDER 1KG'], 'uom': 'kg', 'price': 35.00, 'pack': 1.0},
    {'key': 'unagi', 'label': 'Unagi', 'names': ['UNAGI KABAYAKI 285G'], 'uom': 'kg', 'price': 164.35, 'pack': 0.285},
    {'key': 'sweet', 'label': 'Sweet', 'names': ['SWEET CHILLI SAUCE', 'SWEET CHILI SAUCE'], 'uom': 'pcs', 'price': 1.00, 'pack': 1.0},
)

# Lines are (ingredient key, kitchen qty). Budget cost = qty * sheet price.
RECIPES = (
    {'code': 'BB-200', 'name': 'buffett beef 200', 'category': 'buffet', 'sale_names': ['buffett beef 200', 'buffet beef 200'],
     'menu_price': 0.0, 'sold': 275.0, 'cost_total': 2750.0,
     'notes': 'Unlimited buffet AED 99 component. Sample sold is 157 + 118 from the sales sheet. Food cost on the sheet is 10.00.',
     'lines': [('beef', 0.20), ('rice', 0.10), ('nori', 1)]},
    {'code': 'BC-200', 'name': 'BUFFET CHICKEN 200', 'category': 'buffet', 'sale_names': ['BUFFET CHICKEN 200', 'buffet chicken 200'],
     'menu_price': 0.0, 'sold': 106.0, 'cost_total': 466.40,
     'notes': 'Unlimited buffet AED 99 component. Sheet food cost 4.40.',
     'lines': [('chicken', 0.20)]},
    {'code': '198', 'name': '198 Samurai Shrimp Maki', 'category': 'sushi', 'sale_names': ['198 Samurai Shrimp Maki'],
     'menu_price': 0.0, 'sold': 131.0, 'cost_total': 598.93,
     'notes': 'Sheet food cost 4.57.',
     'lines': [('shrimp', 0.076), ('rice', 0.12), ('nori', 1)]},
    {'code': 'MISO', 'name': 'MISO SOUP SMALL', 'category': 'japanese', 'sale_names': ['MISO SOUP SMALL'],
     'menu_price': 0.0, 'sold': 122.0, 'cost_total': 366.0,
     'notes': 'Sheet food cost 3.00. Miso paste was not on the ingredient price list, so the budget uses soya, shitake and spring onion.',
     'lines': [('shitake', 0.02), ('soya', 0.05), ('spring_onion', 0.05)]},
    {'code': '217', 'name': '217 Fry Salmon Cheese Roll', 'category': 'sushi', 'sale_names': ['217 Fry Salmon Cheese Roll'],
     'menu_price': 0.0, 'sold': 97.5, 'cost_total': 917.48,
     'notes': 'Sheet food cost 9.41.',
     'lines': [('salmon', 0.08), ('cheese', 0.05), ('rice', 0.12), ('nori', 1), ('mayo', 0.026)]},
    {'code': '73', 'name': '73 Crunchy Crab Roll', 'category': 'sushi', 'sale_names': ['73 Crunchy Crab Roll'],
     'menu_price': 0.0, 'sold': 90.0, 'cost_total': 596.70,
     'notes': 'Sheet food cost 6.63.',
     'lines': [('crab', 2), ('avocado', 0.06), ('rice', 0.12), ('nori', 1), ('mayo', 0.013)]},
    {'code': '63', 'name': '63 Avocado Maki', 'category': 'sushi', 'sale_names': ['63 Avocado Maki'],
     'menu_price': 0.0, 'sold': 1.0, 'cost_total': 0.0,
     'notes': 'A posted sale exists for this item even though it was not on the costing sheet.',
     'lines': [('avocado', 0.08), ('cucumber', 0.03), ('rice', 0.12), ('nori', 1)]},
    {'code': '75', 'name': '75 California Maki', 'category': 'sushi', 'sale_names': ['75 California Maki'],
     'menu_price': 51.45, 'sold': 73.0, 'cost_total': 655.54,
     'notes': 'Menu card 51.45 AED. Sheet food cost 8.98.',
     'lines': [('crab', 2), ('avocado', 0.08), ('cucumber', 0.05), ('rice', 0.12), ('nori', 1), ('mayo', 0.068)]},
    {'code': '68', 'name': '68 Philadelphia Roll', 'category': 'sushi', 'sale_names': ['68 Philadelphia Roll'],
     'menu_price': 55.65, 'sold': 61.0, 'cost_total': 805.81,
     'notes': 'Menu card 55.65 AED. Sheet food cost 13.21.',
     'lines': [('salmon', 0.10), ('cheese', 0.08), ('avocado', 0.06), ('cucumber', 0.04), ('rice', 0.12), ('nori', 1), ('mayo', 0.03)]},
    {'code': '219', 'name': '219 Ebi Rainbow Maki', 'category': 'sushi', 'sale_names': ['219 Ebi Rainbow Maki'],
     'menu_price': 55.65, 'sold': 47.5, 'cost_total': 214.80,
     'notes': 'Menu card 55.65 AED. Sheet food cost 4.52.',
     'lines': [('shrimp', 0.0506), ('avocado', 0.04), ('rice', 0.10), ('nori', 1)]},
    {'code': '65', 'name': '65 Salmon & Avocado Maki', 'category': 'sushi', 'sale_names': ['65 Salmon & Avocado Maki'],
     'menu_price': 0.0, 'sold': 46.5, 'cost_total': 433.85,
     'notes': 'Sheet food cost 9.33.',
     'lines': [('salmon', 0.0786), ('avocado', 0.08), ('rice', 0.12), ('nori', 1)]},
    {'code': '64', 'name': '64 Tempura Maki', 'category': 'sushi', 'sale_names': ['64 Tempura Maki'],
     'menu_price': 0.0, 'sold': 39.0, 'cost_total': 164.58,
     'notes': 'Sheet food cost 4.22.',
     'lines': [('shrimp', 0.0494), ('rice', 0.12), ('nori', 1), ('egg', 0.5)]},
    {'code': '62', 'name': '62 Spicy Salmon', 'category': 'sushi', 'sale_names': ['62 Spicy Salmon'],
     'menu_price': 0.0, 'sold': 17.0, 'cost_total': 159.46,
     'notes': 'Sheet food cost 9.38.',
     'lines': [('salmon', 0.0903), ('mayo', 0.04), ('spring_onion', 0.01), ('rice', 0.12), ('nori', 1)]},
    {'code': '77', 'name': '77 Futo Maki', 'category': 'sushi', 'sale_names': ['77 Futo Maki'],
     'menu_price': 34.65, 'sold': 13.5, 'cost_total': 191.43,
     'notes': 'Menu card 34.65 AED. Futo rice on the kitchen sheet is about 120g. Sheet food cost 14.18.',
     'lines': [('egg', 2), ('crab', 2), ('cucumber', 0.04), ('shitake', 0.02), ('rice', 0.12), ('nori', 2), ('tuna', 0.04), ('avocado', 0.05), ('cheese', 0.068)]},
    {'code': '67', 'name': '67 Spicy Tuna', 'category': 'sushi', 'sale_names': ['67 Spicy Tuna'],
     'menu_price': 43.05, 'sold': 7.0, 'cost_total': 57.96,
     'notes': 'Menu card Spicy Tuna 43.05 AED. Sheet food cost 8.28.',
     'lines': [('tuna', 0.0815), ('mayo', 0.05), ('spring_onion', 0.02), ('rice', 0.12), ('nori', 1)]},
    {'code': '79', 'name': '79 Tekka Maki', 'category': 'sushi', 'sale_names': ['79 Tekka Maki'],
     'menu_price': 26.25, 'sold': 1.0, 'cost_total': 8.0,
     'notes': 'Menu card 26.25 AED. Sheet food cost 8.00.',
     'lines': [('tuna', 0.10), ('rice', 0.12), ('nori', 1), ('wasabi', 0.0103)]},
    {'code': '69', 'name': '69 Spider Roll', 'category': 'sushi', 'sale_names': ['69 Spider Roll'],
     'menu_price': 63.0, 'sold': 1.0, 'cost_total': 12.0,
     'notes': 'Menu card 63 AED, marked Not Available. Sheet food cost 12.00.',
     'lines': [('shrimp', 0.12), ('crab', 2), ('avocado', 0.06), ('rice', 0.12), ('nori', 1), ('mayo', 0.06), ('cucumber', 0.03)]},
    {'code': '60', 'name': '60 Dragon Roll', 'category': 'sushi', 'sale_names': ['60 Dragon Roll'],
     'menu_price': 0.0, 'sold': 4.0, 'cost_total': 40.0,
     'notes': 'Kitchen sheet SR-60 style roll. Sales sheet food cost 10.00.',
     'lines': [('shrimp', 0.08), ('crab', 2), ('avocado', 0.06), ('rice', 0.12), ('nori', 1), ('mayo', 0.04)]},
    {'code': 'KAPPA', 'name': 'Kappa Maki', 'category': 'sushi', 'sale_names': ['5555 kappa maki', 'Kappa Maki'],
     'menu_price': 18.90, 'sold': 0.0, 'cost_total': 0.0,
     'notes': 'Menu card 18.90 AED. Cucumber hoso roll. Not on the sales-cost sheet.',
     'lines': [('cucumber', 0.08), ('rice', 0.12), ('nori', 1)]},
    {'code': 'UNAGI', 'name': 'Unagi Maki', 'category': 'sushi', 'sale_names': ['Unagi Maki'],
     'menu_price': 34.65, 'sold': 0.0, 'cost_total': 0.0,
     'notes': 'Menu card 34.65 AED. Unagi pack in inventory is UNAGI KABAYAKI 285G.',
     'lines': [('unagi', 0.04), ('rice', 0.12), ('nori', 1)]},
    {'code': 'NIGIRI', 'name': 'Nigiri', 'category': 'sushi', 'sale_names': ['Nigiri'],
     'menu_price': 0.0, 'sold': 45.0, 'cost_total': 270.0,
     'notes': 'Sales sheet Nigiri food cost 6.00, sold 45, amount 270.',
     'lines': [('salmon', 0.04), ('tuna', 0.03), ('rice', 0.12), ('wasabi', 0.0077)]},
    {'code': 'RICE', 'name': 'Rice portion', 'category': 'other', 'sale_names': [],
     'menu_price': 0.0, 'sold': 170.0, 'cost_total': 510.0,
     'notes': 'Sales sheet Rice food cost 3.00, sold 170, amount 510. Linked to purchased sushi rice, not a menu card item.',
     'lines': [('rice', 0.25)]},
)

PREPS = (
    {'code': 'P01', 'name': 'Sushi rice (cooked, seasoned)', 'yield': 11.0, 'uom': 'kg',
     'lines': [('rice', 10.0)],
     'notes': 'Prep sheet P01. Vinegar is not on the purchased-ingredient list yet.'},
    {'code': 'P03', 'name': 'Spicy mayo', 'yield': 1.2, 'uom': 'kg',
     'lines': [('mayo', 1.0)],
     'notes': 'Prep sheet P03. Sriracha was not found as its own purchase item.'},
    {'code': 'P07', 'name': 'Wasabi paste', 'yield': 2.5, 'uom': 'kg',
     'lines': [('wasabi', 1.0)],
     'notes': 'Prep sheet P07. Linked to WASABI POWDER 1KG.'},
)


class RecipeBookDemo(models.Model):
    _inherit = 'cpabooks.recipe'

    def _demo_menu_result(self, demo, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recipe Book'),
                'message': message,
                'sticky': False,
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window',
                    'name': _('Sample Recipes') if demo else _('Menu Book'),
                    'res_model': 'cpabooks.recipe',
                    'view_mode': 'kanban,tree,form',
                    'domain': [('is_demo', '=', True)] if demo else [],
                    'target': 'current',
                },
            },
        }

    @api.model
    def action_menu_load_demo(self):
        return self._demo_menu_result(True, self.action_load_demo_data())

    @api.model
    def action_menu_clear_demo(self):
        return self._demo_menu_result(False, self.action_clear_demo_data())

    @api.model
    def action_load_demo_data(self):
        ingredients = {row['key']: row for row in INGREDIENTS}
        products, created_products, linked = self._demo_ingredient_products(ingredients)
        self.search([('is_demo', '=', True), ('code', 'in', [r['code'] for r in RECIPES])]).unlink()
        self.env['cpabooks.prep.recipe'].search([
            ('is_demo', '=', True), ('code', 'in', [p['code'] for p in PREPS]),
        ]).unlink()
        company = self.env.company
        branch = company.name or 'Samurai'
        for spec in RECIPES:
            sale = self._demo_sale_product(spec)
            notes = self._demo_recipe_notes(spec, products, ingredients)
            self.create({
                'name': spec['name'],
                'code': spec['code'],
                'company_id': company.id,
                'branch': branch,
                'category': spec['category'],
                'sale_product_id': sale.id,
                'is_demo': True,
                'menu_price': spec['menu_price'],
                'sample_sold_qty': spec['sold'],
                'sample_food_cost_total': spec['cost_total'],
                'portion_qty': 1.0,
                'image_1920': self._demo_menu_image(spec['name'], spec['menu_price'], spec.get('category'), spec['code']),
                'notes': notes,
                'line_ids': [(0, 0, self._demo_line_vals(key, qty, products, ingredients))
                             for key, qty in spec['lines']],
            })
        Prep = self.env['cpabooks.prep.recipe']
        for spec in PREPS:
            output = self._demo_prep_product(spec)
            Prep.create({
                'name': spec['name'],
                'code': spec['code'],
                'company_id': company.id,
                'is_demo': True,
                'product_id': output.id,
                'batch_yield': spec['yield'],
                'uom_id': output.uom_id.id,
                'line_ids': [(0, 0, {
                    'product_id': products[key].id,
                    'qty': qty / (ingredients[key]['pack'] or 1.0),
                    'uom_id': products[key].uom_id.id,
                }) for key, qty in spec['lines']],
            })
        self._demo_fill_closing(company, branch)
        msg = _(
            'Loaded %(recipes)s sample recipes and %(preps)s prep items. '
            'Linked %(linked)s ingredients to products already purchased. '
            'Created %(created)s products that were not in inventory. '
            'Sale orders were not created. Sample sold qty is from the sales sheet.'
        ) % {
            'recipes': len(RECIPES),
            'preps': len(PREPS),
            'linked': linked,
            'created': created_products,
        }
        _logger.info(msg)
        return msg

    @api.model
    def action_clear_demo_data(self):
        recipes = self.search([('is_demo', '=', True)])
        preps = self.env['cpabooks.prep.recipe'].search([('is_demo', '=', True)])
        recipe_count = len(recipes)
        prep_count = len(preps)
        recipes.unlink()
        preps.unlink()
        self.env['cpabooks.recipe.closing'].search([('is_demo', '=', True)]).unlink()
        Product = self.env['product.product']
        demo_products = Product.sudo().search([('default_code', '=like', 'RB-DEMO-%')])
        used = set()
        if demo_products:
            used.update(self.env['cpabooks.recipe.line'].search([
                ('product_id', 'in', demo_products.ids),
            ]).mapped('product_id').ids)
            used.update(self.env['cpabooks.prep.recipe.line'].search([
                ('product_id', 'in', demo_products.ids),
            ]).mapped('product_id').ids)
            used.update(self.search([
                ('sale_product_id', 'in', demo_products.ids),
            ]).mapped('sale_product_id').ids)
            used.update(self.env['cpabooks.prep.recipe'].search([
                ('product_id', 'in', demo_products.ids),
            ]).mapped('product_id').ids)
        removable = demo_products.filtered(lambda p: p.id not in used)
        removed = len(removable)
        if removable:
            removable.sudo().unlink()
        msg = _(
            'Cleared %(recipes)s sample recipes and %(preps)s sample prep items. '
            'Actual recipes were kept. Removed %(products)s unused demo products.'
        ) % {'recipes': recipe_count, 'preps': prep_count, 'products': removed}
        _logger.info(msg)
        return msg

    MENU_PHOTO_FILES = {
        '67': '67.jpg',
        '68': '68.jpg',
        '69': '69.jpg',
        'KAPPA': '72.jpg',
        '75': '75.jpg',
        '77': '77.jpg',
        'UNAGI': '78.jpg',
        '79': '79.jpg',
        '219': '219.jpg',
    }

    @api.model
    def _menu_photo_b64(self, code):
        filename = self.MENU_PHOTO_FILES.get(code or '')
        if not filename:
            return False
        path = os.path.join(os.path.dirname(__file__), '..', 'static', 'src', 'img', 'menu', filename)
        if not os.path.isfile(path):
            return False
        with open(path, 'rb') as handle:
            return base64.b64encode(handle.read())

    @api.model
    def _apply_menu_photos(self):
        """Put the cut menu-page photos on the matching recipes."""
        for code in self.MENU_PHOTO_FILES:
            photo = self._menu_photo_b64(code)
            if photo:
                self.search([('code', '=', code)]).write({'image_1920': photo})

    @api.model
    def _demo_menu_image(self, name, price, category, code=None):
        """Dish photo cut from the printed menu, otherwise a plain price card."""
        photo = self._menu_photo_b64(code)
        if photo:
            return photo
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception:
            return False
        width, height = 800, 500
        img = Image.new('RGB', (width, height), (18, 18, 20))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 390, width, height), fill=(176, 18, 24))
        try:
            title_font = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 42)
            small_font = ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf', 22)
            price_font = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 36)
        except Exception:
            title_font = small_font = price_font = ImageFont.load_default()
        label = category == 'buffet' and 'BUFFET' or (category or 'MENU').upper()
        draw.text((36, 36), label, fill=(180, 180, 180), font=small_font)
        y = 120
        words = (name or '').split()
        line = ''
        for word in words:
            trial = (line + ' ' + word).strip()
            if len(trial) > 22 and line:
                draw.text((36, y), line, fill=(255, 255, 255), font=title_font)
                y += 52
                line = word
            else:
                line = trial
        if line:
            draw.text((36, y), line, fill=(255, 255, 255), font=title_font)
        if price:
            price_txt = '%.2f AED' % price
        else:
            price_txt = 'Kitchen menu'
        draw.text((36, 415), price_txt, fill=(255, 255, 255), font=price_font)
        raw = BytesIO()
        img.save(raw, format='PNG')
        return base64.b64encode(raw.getvalue())

    @api.model
    def _demo_fill_closing(self, company, branch):
        """Closing sheet from real purchases plus sample sales, including items with no recipe."""
        Closing = self.env['cpabooks.recipe.closing']
        Closing.search([('is_demo', '=', True)]).unlink()
        lines = self.env['cpabooks.recipe.line'].search([('recipe_id.is_demo', '=', True)])
        theoretical = {}
        for line in lines:
            sold = line.recipe_id.sample_sold_qty or 0.0
            theoretical[line.product_id.id] = theoretical.get(line.product_id.id, 0.0) + (sold * line.qty)
        extra = self._demo_extra_purchase_products(list(theoretical), limit=12)
        product_ids = list(set(list(theoretical) + extra))
        purchases = self._demo_purchase_qty(product_ids)
        for product_id in product_ids:
            purchase = purchases.get(product_id, 0.0)
            theory = theoretical.get(product_id, 0.0)
            opening = 0.0 if purchase else theory
            chef = max(opening + purchase - theory, 0.0)
            Closing.create({
                'date': '2026-08-28',
                'company_id': company.id,
                'branch': branch,
                'product_id': product_id,
                'opening_qty': opening,
                'purchase_qty': purchase,
                'theoretical_consumption': theory,
                'actual_closing_qty': chef,
                'is_demo': True,
            })

    @api.model
    def _demo_purchase_qty(self, product_ids):
        if not product_ids:
            return {}
        self.env.cr.execute("""
            SELECT pol.product_id, COALESCE(SUM(pol.product_qty), 0)
            FROM purchase_order_line pol
            JOIN purchase_order po ON po.id = pol.order_id
            WHERE po.state IN ('purchase', 'done')
              AND pol.product_id IN %s
            GROUP BY pol.product_id
        """, [tuple(product_ids)])
        return {row[0]: row[1] for row in self.env.cr.fetchall()}

    @api.model
    def _demo_extra_purchase_products(self, skip_ids, limit=12):
        """Purchased items that are not on a sample recipe, so closing is not only perfect matches."""
        self.env.cr.execute("""
            SELECT pol.product_id
            FROM purchase_order_line pol
            JOIN purchase_order po ON po.id = pol.order_id
            JOIN product_product pp ON pp.id = pol.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE po.state IN ('purchase', 'done')
              AND pt.purchase_ok
              AND pt.name NOT ILIKE '%%steel%%'
              AND pt.name NOT ILIKE '%%wool%%'
            GROUP BY pol.product_id
            ORDER BY COUNT(*) DESC
            LIMIT 80
        """)
        skip = set(skip_ids or [])
        found = []
        for (product_id,) in self.env.cr.fetchall():
            if product_id in skip:
                continue
            found.append(product_id)
            if len(found) >= limit:
                break
        return found

    @api.model
    def _demo_ingredient_products(self, ingredients):
        products = {}
        created = 0
        linked = 0
        uoms = {
            'kg': self.env.ref('uom.product_uom_kgm'),
            'pcs': self.env.ref('uom.product_uom_unit'),
            'ltr': self.env.ref('uom.product_uom_litre'),
        }
        for row in ingredients.values():
            found, bills = self._demo_find_product(row['names'], sale=False)
            if found:
                products[row['key']] = found
                linked += 1
                row['matched_name'] = found.display_name
                row['purchase_bills'] = bills
                continue
            code = 'RB-DEMO-ING-%s' % row['key'].upper()
            product = self.env['product.product'].sudo().search([('default_code', '=', code)], limit=1)
            if not product:
                uom = uoms[row['uom']]
                product = self.env['product.product'].sudo().create({
                    'name': row['label'],
                    'default_code': code,
                    'type': 'product',
                    'purchase_ok': True,
                    'sale_ok': False,
                    'uom_id': uom.id,
                    'uom_po_id': uom.id,
                    'standard_price': row['price'],
                    'company_id': self.env.company.id,
                })
                created += 1
            products[row['key']] = product
            row['matched_name'] = False
            row['purchase_bills'] = 0
        return products, created, linked

    @api.model
    def _demo_find_product(self, names, sale=False):
        Product = self.env['product.product'].sudo()
        Line = (self.env['sale.order.line'] if sale else self.env['purchase.order.line']).sudo()
        best = Product.browse()
        best_n = -1
        for name in names:
            recs = Product.search([('name', '=ilike', name)])
            if not recs and sale:
                recs = Product.search([('name', 'ilike', name)]).filtered(
                    lambda product, phrase=name: self._demo_phrase_in_name(product.name, phrase)
                )
            recs = recs.filtered(lambda p: self._demo_name_ok(p, sale=sale))
            for product in recs:
                count = Line.search_count([('product_id', '=', product.id)])
                if count > best_n or (count == best_n and best and product.id < best.id) or not best:
                    if count > best_n or not best:
                        best = product
                        best_n = count
        return best, max(best_n, 0)

    @api.model
    def _demo_phrase_in_name(self, product_name, phrase):
        """Match 'Unagi Maki' inside '78 Unagi Maki', not 'Nigiri' inside 'Onigiri'."""
        if not product_name or not phrase:
            return False
        return bool(re.search(
            r'(?<![A-Za-z0-9])%s(?![A-Za-z0-9])' % re.escape(phrase),
            product_name,
            re.IGNORECASE,
        ))

    @api.model
    def _demo_name_ok(self, product, sale=False):
        name = (product.name or '').lower()
        if ' - dv' in name or ' - off' in name:
            return False
        if sale:
            return bool(product.sale_ok)
        return bool(product.purchase_ok)

    @api.model
    def _demo_prep_product(self, spec):
        code = 'RB-DEMO-PREP-%s' % spec['code']
        product = self.env['product.product'].sudo().search([('default_code', '=', code)], limit=1)
        if product:
            return product
        uom = self.env.ref('uom.product_uom_kgm')
        return self.env['product.product'].sudo().create({
            'name': spec['name'],
            'default_code': code,
            'type': 'product',
            'purchase_ok': False,
            'sale_ok': False,
            'uom_id': uom.id,
            'uom_po_id': uom.id,
            'company_id': self.env.company.id,
        })

    @api.model
    def _demo_sale_product(self, spec):
        product, _bills = self._demo_find_product(spec['sale_names'], sale=True) if spec['sale_names'] else (self.env['product.product'], 0)
        if product:
            return product
        code = 'RB-DEMO-SALE-%s' % spec['code']
        product = self.env['product.product'].sudo().search([('default_code', '=', code)], limit=1)
        if product:
            return product
        uom = self.env.ref('uom.product_uom_unit')
        return self.env['product.product'].sudo().create({
            'name': spec['name'],
            'default_code': code,
            'type': 'consu',
            'sale_ok': True,
            'purchase_ok': False,
            'list_price': spec['menu_price'] or 0.0,
            'uom_id': uom.id,
            'uom_po_id': uom.id,
            'company_id': self.env.company.id,
        })

    @api.model
    def _demo_line_vals(self, key, qty, products, ingredients):
        row = ingredients[key]
        product = products[key]
        pack = row['pack'] or 1.0
        if row.get('matched_name'):
            note = _('Purchase item %(name)s (%(bills)s purchase lines). Kitchen %(qty)s %(uom)s.') % {
                'name': row['matched_name'],
                'bills': row.get('purchase_bills') or 0,
                'qty': qty,
                'uom': row['uom'],
            }
        else:
            note = _('Not in inventory. Demo product created. Kitchen %(qty)s %(uom)s.') % {
                'qty': qty, 'uom': row['uom'],
            }
        return {
            'product_id': product.id,
            'qty': qty / pack,
            'uom_id': product.uom_id.id,
            'budget_qty': qty,
            'budget_uom': row['uom'],
            'budget_unit_cost': row['price'],
            'link_note': note,
        }

    @api.model
    def _demo_recipe_notes(self, spec, products, ingredients):
        bits = [spec['notes'], _('Budget prices are from the costing sheet. Actual line cost uses the linked product cost.')]
        for key, qty in spec['lines']:
            row = ingredients[key]
            label = row.get('matched_name') or _('demo: %s') % row['label']
            bits.append('%s %s %s -> %s' % (qty, row['uom'], row['label'], label))
        return '\n'.join(bits)


class PrepRecipeDemo(models.Model):
    _inherit = 'cpabooks.prep.recipe'

    def action_clone_to_actual(self):
        self.ensure_one()
        new = self.copy(default={'is_demo': False, 'name': self.name})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Actual Prep'),
            'res_model': 'cpabooks.prep.recipe',
            'view_mode': 'form',
            'res_id': new.id,
            'target': 'current',
        }
