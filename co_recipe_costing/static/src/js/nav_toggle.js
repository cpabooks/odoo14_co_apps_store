odoo.define('co_recipe_costing.nav_toggle', function (require) {
    'use strict';

    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var core = require('web.core');

    var STORAGE_KEY = 'cpabooks_nav_mode';
    var APP_XMLID = 'co_recipe_costing.menu_recipe_root';

    function escapeText(value) {
        return $('<div/>').text(value || '').html();
    }

    function actionId(menu) {
        if (!menu || !menu.action) {
            return '';
        }
        return String(menu.action).split(',')[1] || '';
    }

    function containsId(node, id) {
        if (!node || !id) {
            return false;
        }
        if (node.id === id) {
            return true;
        }
        return _.some(node.children || [], function (child) {
            return containsId(child, id);
        });
    }

    var NavToggle = Widget.extend({
        template: 'RecipeNavToggle',
        sequence: 200,
        events: {
            'click .o_nav_side': '_onSide',
            'click .o_nav_top': '_onTop',
        },
        start: function () {
            var self = this;
            core.bus.on('change_menu_section', this, this._sync);
            $(window).on('hashchange.recipe_nav', this._sync.bind(this));
            return this._super.apply(this, arguments).then(function () {
                self._sync();
            });
        },
        destroy: function () {
            $(window).off('hashchange.recipe_nav');
            if (this.$sidebar) {
                this.$sidebar.remove();
            }
            document.body.classList.remove('o_cpa_nav_side');
            this._shiftPage(false);
            this._super.apply(this, arguments);
        },
        _menuWidget: function () {
            var systray = this.getParent();
            return systray && systray.getParent();
        },
        _recipeApp: function () {
            var menu = this._menuWidget();
            var apps = (menu && menu.menu_data && menu.menu_data.children) || [];
            return _.find(apps, function (app) {
                return app.xmlid === APP_XMLID;
            });
        },
        _inRecipe: function (app) {
            if (!app) {
                return false;
            }
            var menu = this._menuWidget();
            var current = menu && menu.current_primary_menu;
            if (current === app.id) {
                return true;
            }
            var hash = window.location.hash || '';
            var match = hash.match(/menu_id=(\d+)/);
            return !!(match && containsId(app, parseInt(match[1], 10)));
        },
        _onSide: function (event) {
            event.preventDefault();
            this._apply('side');
        },
        _onTop: function (event) {
            event.preventDefault();
            this._apply('top');
        },
        _apply: function (mode) {
            window.localStorage.setItem(STORAGE_KEY, mode);
            this.$('.o_nav_side').toggleClass('active', mode === 'side');
            this.$('.o_nav_top').toggleClass('active', mode !== 'side');
            this._sync();
        },
        _sync: function () {
            var mode = window.localStorage.getItem(STORAGE_KEY) || 'top';
            var app = this._recipeApp();
            var show = mode === 'side' && this._inRecipe(app);
            document.body.classList.toggle('o_cpa_nav_side', show);
            this.$('.o_nav_side').toggleClass('active', mode === 'side');
            this.$('.o_nav_top').toggleClass('active', mode !== 'side');
            this._shiftPage(show);
            if (show) {
                this._renderSidebar(app);
            } else if (this.$sidebar) {
                this.$sidebar.remove();
                this.$sidebar = null;
            }
        },
        _shiftPage: function (on) {
            var client = document.querySelector('.o_web_client');
            if (!client) {
                return;
            }
            if (on) {
                client.style.setProperty('margin-left', '268px', 'important');
                client.style.setProperty('width', 'calc(100vw - 268px)', 'important');
                client.style.setProperty('max-width', 'calc(100vw - 268px)', 'important');
                client.style.setProperty('padding-left', '0px', 'important');
                client.style.setProperty('box-sizing', 'border-box', 'important');
            } else {
                client.style.removeProperty('margin-left');
                client.style.removeProperty('width');
                client.style.removeProperty('max-width');
                client.style.removeProperty('padding-left');
                client.style.removeProperty('box-sizing');
            }
        },
        _item: function (menu, tier) {
            var id = actionId(menu);
            if (!id) {
                return '';
            }
            return '<li class="o_recipe_side_item ' + tier + '">' +
                '<a href="#" data-menu-id="' + menu.id + '" data-action-id="' + id + '">' +
                escapeText(menu.name) + '</a></li>';
        },
        _section: function (label, tone) {
            return '<li class="o_recipe_side_section o_recipe_side_' + tone + '">' + escapeText(label) + '</li>';
        },
        _renderSidebar: function (app) {
            var kids = _.sortBy(app.children || [], 'sequence');
            var dashboard = _.find(kids, function (menu) {
                return menu.xmlid === 'co_recipe_costing.menu_dashboard';
            });
            var daily = _.find(kids, function (menu) {
                return menu.xmlid === 'co_recipe_costing.menu_daily_reports';
            });
            var stock = _.find(kids, function (menu) {
                return menu.xmlid === 'co_recipe_costing.menu_daily_closing_stock';
            });
            var rest = _.filter(kids, function (menu) {
                return menu !== dashboard && menu !== daily && menu !== stock;
            });
            var html = '<div class="o_recipe_side_title">Recipe Book</div><ul>';
            html += this._section('Home', 'home');
            html += this._item(dashboard, 'o_recipe_side_main');
            html += this._section('Recipe Book', 'book');
            var self = this;
            _.each(rest, function (menu) {
                if (menu.children && menu.children.length) {
                    html += self._section(menu.name, 'config');
                    _.each(_.sortBy(menu.children, 'sequence'), function (child) {
                        html += self._item(child, 'o_recipe_side_sub');
                    });
                } else {
                    html += self._item(menu, 'o_recipe_side_sub');
                }
            });
            html += this._section('Daily Closing Stock', 'stock');
            _.each(_.sortBy((stock && stock.children) || [], 'sequence'), function (child) {
                html += self._item(child, 'o_recipe_side_sub');
            });
            html += this._section('Daily Reports', 'daily');
            _.each(_.sortBy((daily && daily.children) || [], 'sequence'), function (child) {
                if (child.children && child.children.length) {
                    html += self._section(child.name, 'daily');
                    _.each(_.sortBy(child.children, 'sequence'), function (leaf) {
                        html += self._item(leaf, 'o_recipe_side_sub');
                    });
                } else {
                    html += self._item(child, 'o_recipe_side_sub');
                }
            });
            html += '</ul>';
            if (!this.$sidebar) {
                this.$sidebar = $('<aside class="o_recipe_app_sidebar"/>');
                $('body').append(this.$sidebar);
                this.$sidebar.on('click', 'a[data-action-id]', this._onMenu.bind(this));
            }
            this.$sidebar.html(html);
            this._markActive();
        },
        _markActive: function () {
            var hash = window.location.hash || '';
            var action = (hash.match(/action=(\d+)/) || [])[1];
            this.$sidebar.find('a').each(function () {
                var on = action && String($(this).attr('data-action-id')) === String(action);
                $(this).closest('li').toggleClass('active', !!on);
            });
        },
        _onMenu: function (event) {
            event.preventDefault();
            var $link = $(event.currentTarget);
            this.trigger_up('menu_clicked', {
                id: parseInt($link.attr('data-menu-id'), 10),
                action_id: parseInt($link.attr('data-action-id'), 10),
            });
            this.$sidebar.find('li').removeClass('active');
            $link.closest('li').addClass('active');
        },
    });

    SystrayMenu.Items.push(NavToggle);
    return NavToggle;
});
