odoo.define('co_recipe_costing.dashboard', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    var RecipeStatusDashboard = AbstractAction.extend({
        template: 'RecipeStatusDashboard',
        hasControlPanel: false,
        events: {
            'click .o_recipe_drill': '_onDrill',
        },
        getTitle: function () {
            return 'Dashboard';
        },
        init: function () {
            this._super.apply(this, arguments);
            this.data = {
                company: '',
                company_id: false,
                management: {bars: [], rows: []},
                chef: {rows: []},
                store: {rows: []},
            };
        },
        willStart: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._rpc({
                    model: 'cpabooks.recipe',
                    method: 'get_status_dashboard',
                }).then(function (data) {
                    self.data = data;
                });
            });
        },
        _companyDomain: function (extra) {
            var domain = [['company_id', '=', this.data.company_id]];
            return extra ? domain.concat(extra) : domain;
        },
        _openList: function (name, model, domain, recipe) {
            this.do_action({
                type: 'ir.actions.act_window',
                name: name,
                res_model: model,
                view_mode: recipe ? 'kanban,tree,form' : 'tree,form',
                views: recipe
                    ? [[false, 'kanban'], [false, 'tree'], [false, 'form']]
                    : [[false, 'tree'], [false, 'form']],
                domain: domain,
                target: 'current',
            });
        },
        _openForm: function (name, model, resId) {
            this.do_action({
                type: 'ir.actions.act_window',
                name: name,
                res_model: model,
                res_id: resId,
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
            });
        },
        _onDrill: function (ev) {
            ev.preventDefault();
            var $el = $(ev.currentTarget);
            var drill = $el.data('drill');
            var cid = this._companyDomain.bind(this);
            if (drill === 'recipes') {
                this._openList('Menu Book', 'cpabooks.recipe', cid(), true);
            } else if (drill === 'budget' || drill === 'actual') {
                this._openList('Priced menu', 'cpabooks.recipe', cid([['menu_price', '>', 0]]), true);
            } else if (drill === 'sales' || drill === 'food' || drill === 'margin') {
                this._openList('Sold samples', 'cpabooks.recipe', cid([['sample_sold_qty', '>', 0]]), true);
            } else if (drill === 'category') {
                this._openList($el.find('span').text() || 'Category', 'cpabooks.recipe', cid([['category', '=', $el.data('key')]]), true);
            } else if (drill === 'recipe') {
                this._openForm('Recipe', 'cpabooks.recipe', $el.data('id'));
            } else if (drill === 'preps') {
                this._openList('Prep & Sub-Recipes', 'cpabooks.prep.recipe', cid(), false);
            } else if (drill === 'closing') {
                this._openList('Daily Closing Stock', 'cpabooks.recipe.closing', cid(), false);
            } else if (drill === 'ok') {
                this._openList('Closing OK', 'cpabooks.recipe.closing', cid([['state', '=', 'ok']]), false);
            } else if (drill === 'check') {
                this._openList('Closing Check', 'cpabooks.recipe.closing', cid([['state', '=', 'warning']]), false);
            } else if (drill === 'variance') {
                this._openList('Closing Variance', 'cpabooks.recipe.closing', cid([['state', '=', 'variance']]), false);
            } else if (drill === 'purchased' || drill === 'purchase_qty') {
                this._openList('Purchased items', 'cpabooks.recipe.closing', cid([['purchase_qty', '>', 0]]), false);
            } else if (drill === 'unmatched') {
                this._openList('Not on a recipe', 'cpabooks.recipe.closing', cid([['purchase_qty', '>', 0], ['theoretical_consumption', '=', 0]]), false);
            } else if (drill === 'closing_line') {
                this._openForm('Daily Closing Stock', 'cpabooks.recipe.closing', $el.data('id'));
            }
        },
    });

    core.action_registry.add('cpabooks_recipe_dashboard', RecipeStatusDashboard);
    return RecipeStatusDashboard;
});
