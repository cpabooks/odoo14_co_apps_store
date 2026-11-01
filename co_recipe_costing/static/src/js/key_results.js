odoo.define('co_recipe_costing.key_results', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var Dialog = require('web.Dialog');

    var KeyResults = AbstractAction.extend({
        template: 'RecipeKeyResults',
        hasControlPanel: false,
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.action = action;
            this.data = {companies: [], total: {}};
        },
        willStart: function () {
            var ready = this._super.apply(this, arguments);
            var stored = this._storedPeriod();
            var args = stored ? [stored.date_from, stored.date_to] : [];
            var loaded = this._rpc({
                model: 'cpabooks.recipe',
                method: 'get_key_results',
                args: args,
            }).then(function (data) {
                this.data = data || this.data;
            }.bind(this));
            return Promise.all([ready, loaded]);
        },
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._setPeriod();
                self.$el.on('click', '.kr_company .kr_link', self._onCompany.bind(self));
                self.$el.on('click', '.kr_category .kr_link', self._onCategory.bind(self));
                self.$el.on('click', '.kr_item .kr_link', self._onItem.bind(self));
                self.$el.on('click', '.kr_drill, .kr_drill_cell', self._onPurchases.bind(self));
                self.$el.on('click', '.kr_open_cons', self._onOpenConsumption.bind(self));
                self.$el.on('click', '.kr_open_close', self._onOpenClosing.bind(self));
                self.$el.on('click', '.kr_apply', self._onApply.bind(self));
                self.$el.on('click', '.kr_last_month', function () { self._shiftMonth(-1); });
                self.$el.on('click', '.kr_before_last', function () { self._shiftMonth(-2); });
                self.$el.on('click', '.kr_export', self._onExport.bind(self));
                self.$el.on('contextmenu', '.kr_prod', self._onProdMenu.bind(self));
                self._cardCache = {};
            });
        },
        _storedPeriod: function () {
            try {
                var raw = window.localStorage.getItem('cpabooks_key_results_period');
                var stored = raw ? JSON.parse(raw) : null;
                if (stored && stored.date_from && stored.date_to) {
                    return stored;
                }
            } catch (error) {
                return null;
            }
            return null;
        },
        _savePeriod: function (dateFrom, dateTo) {
            if (!dateFrom || !dateTo) {
                return;
            }
            window.localStorage.setItem('cpabooks_key_results_period', JSON.stringify({
                date_from: dateFrom,
                date_to: dateTo,
            }));
        },
        _setPeriod: function () {
            this.$('.kr_date_from').val(this.data.date_from || '');
            this.$('.kr_date_to').val(this.data.date_to || '');
        },
        _iso: function (date) {
            var month = date.getMonth() + 1;
            var day = date.getDate();
            return date.getFullYear() + '-' + (month < 10 ? '0' : '') + month + '-' + (day < 10 ? '0' : '') + day;
        },
        _shiftMonth: function (offset) {
            var now = new Date();
            var start = new Date(now.getFullYear(), now.getMonth() + offset, 1);
            var end = new Date(now.getFullYear(), now.getMonth() + offset + 1, 0);
            this._reload(this._iso(start), this._iso(end));
        },
        _onApply: function () {
            this._reload(this.$('.kr_date_from').val(), this.$('.kr_date_to').val());
        },
        _reload: function (dateFrom, dateTo) {
            var self = this;
            this._removeCard();
            this._savePeriod(dateFrom, dateTo);
            this._rpc({
                model: 'cpabooks.recipe',
                method: 'get_key_results',
                args: [dateFrom || false, dateTo || false],
            }).then(function (data) {
                self.data = data || self.data;
                self.$el.html(core.qweb.render('RecipeKeyResults', {widget: self}));
                self._setPeriod();
            });
        },
        _company: function (id) {
            return _.find(this.data.companies, function (row) {
                return String(row.id) === String(id);
            });
        },
        _onCompany: function (event) {
            var company = this._company($(event.currentTarget).closest('tr').data('id'));
            if (!company) {
                return;
            }
            this._openCompany = company;
            this.$('.kr_company').removeClass('kr_item_on');
            $(event.currentTarget).closest('tr').addClass('kr_item_on');
            this.$('.kr_detail').html(this._categoriesHtml(company));
        },
        _colgroup: function () {
            return '<colgroup><col class="kr_col_name"/>' +
                '<col class="kr_col_num"/><col class="kr_col_num"/><col class="kr_col_num"/>' +
                '<col class="kr_col_num"/><col class="kr_col_num"/><col class="kr_col_num"/>' +
                '<col class="kr_col_num"/><col class="kr_col_gap"/></colgroup>';
        },
        _metricRow: function (css, attrs, row) {
            var link = css.indexOf('kr_category') >= 0 || css.indexOf('kr_item') >= 0;
            var nameClass = link ? 'kr_link' : '';
            var prodAttr = '';
            if (row.product_id) {
                nameClass += ' kr_prod';
                prodAttr = ' data-product-id="' + row.product_id + '"';
            }
            return '<tr class="' + css + '" ' + attrs + '>' +
                '<td class="' + nameClass + '"' + prodAttr + ' title="' + _.escape(row.name || '') + '">' + _.escape(row.name || '') + '</td>' +
                this._cell('kr_sale', row.sales, row.sales_missing, row.sold_qty) +
                this._cell('kr_cost', row.actual, row.actual_missing, row.actual_qty, this._purchaseDrill(row, 'actual', row.actual, row.actual_qty)) +
                this._cell('kr_cost', row.potential, row.potential_missing) +
                this._cell('kr_cost', row.daily, row.daily_missing, row.daily_qty, this._purchaseDrill(row, 'daily', row.daily, row.daily_qty)) +
                this._cell('kr_cost', row.theo, row.theo_missing, row.theo_qty, this._purchaseDrill(row, 'daily', row.theo, row.theo_qty)) +
                '<td class="kr_cost">' + _.escape(row.com_pct || '') + '</td>' +
                '<td class="kr_sale">' + _.escape(row.gm || '') + '</td>' +
                '<td class="kr_gap" title="' + _.escape(row.gap || '') + '">' + _.escape(row.gap || '') + '</td></tr>';
        },
        _categoriesHtml: function (company) {
            var rows = _.map(company.categories, function (category) {
                var key = _.escape(category.key);
                var html = this._metricRow('kr_category', 'data-key="' + key + '"', category);
                _.each(category.items, function (item) {
                    html += this._metricRow(
                        'kr_child kr_item',
                        'data-key="' + key + '" data-item-key="' + _.escape(item.key) + '" data-recipe-id="' + item.recipe_id + '" style="display:none"',
                        item
                    );
                }, this);
                return html;
            }, this).join('');
            return '<div class="kr_block_head"><h3>' + _.escape(company.name) + '</h3>' +
                '<button type="button" class="btn btn-primary kr_open kr_open_cons" data-company-id="' + company.id + '">Consumption list</button>' +
                '<button type="button" class="btn btn-secondary kr_open kr_open_close" data-company-id="' + company.id + '">Closing list</button></div>' +
                '<table class="kr_table">' + this._colgroup() +
                '<thead><tr><th title="Category / item">Category / item</th>' +
                '<th class="kr_sale" title="Total Sales">Total Sales</th>' +
                '<th class="kr_cost" title="COM (Actual)">COM (Actual)</th><th class="kr_cost" title="COM Potential">COM Potential</th>' +
                '<th class="kr_cost" title="COM (Daily Consumptions)">COM (Daily Consumptions)</th><th class="kr_cost" title="COM Theoretical">COM Theoretical</th>' +
                '<th class="kr_cost" title="COM %">COM %</th><th class="kr_sale" title="GM">GM</th><th title="Missing">Missing</th></tr></thead><tbody>' +
                rows +
                this._metricRow('kr_total', '', {
                    name: 'TOTAL',
                    id: company.id,
                    sales: company.sales,
                    actual: company.actual,
                    potential: company.potential,
                    daily: company.daily,
                    theo: company.theo,
                    sold_qty: company.sold_qty,
                    actual_qty: company.actual_qty,
                    daily_qty: company.daily_qty,
                    theo_qty: company.theo_qty,
                    com_pct: company.com_pct,
                    gm: company.gm,
                    gap: company.gap,
                    sales_missing: company.sales_missing,
                    actual_missing: company.actual_missing,
                    potential_missing: company.potential_missing,
                    daily_missing: company.daily_missing,
                    theo_missing: company.theo_missing,
                }) +
                '</tbody></table>';
        },
        _purchaseDrill: function (row, kind, amount, qty) {
            var companyId = (row && (row.company_id || row.id)) || (this._openCompany && this._openCompany.id) || 0;
            if (!companyId || (!amount && !qty)) {
                return null;
            }
            return {
                kind: kind,
                companyId: companyId,
                products: (row && row.drill_products) || [],
                amount: amount || '',
                qty: qty || '',
            };
        },
        _cell: function (tone, value, missing, subqty, drill) {
            var inner = '';
            if (value) {
                inner += '<div class="kr_amt">' + _.escape(value) + '</div>';
            }
            if (subqty) {
                inner += '<div class="kr_subqty">' + _.escape(subqty) + '</div>';
            }
            var attrs = '';
            var drillClass = '';
            if (drill) {
                drillClass = ' kr_drill_cell';
                attrs = ' data-kind="' + _.escape(drill.kind || 'actual') + '"' +
                    ' data-company-id="' + (drill.companyId || 0) + '"' +
                    ' data-products="' + _.escape((drill.products || []).join(',')) + '"' +
                    ' data-amount="' + _.escape(drill.amount || '') + '"' +
                    ' data-qty="' + _.escape(drill.qty || '') + '"';
            }
            return '<td class="' + tone + (missing ? ' kr_miss' : '') + drillClass + '"' + attrs + '>' + inner + '</td>';
        },
        _detailRow: function (kind, name, productId, row) {
            row = row || {};
            var cls = 'kr_text';
            var prodAttr = '';
            if (productId) {
                cls += ' kr_link kr_prod kr_ing_name';
                prodAttr = ' data-product-id="' + productId + '"';
            }
            var companyId = (this._openCompany && this._openCompany.id) || 0;
            var dateHtml = '';
            if (row.date) {
                dateHtml = '<span class="kr_drill" data-kind="' + _.escape(row.drill_kind || 'daily') + '"' +
                    ' data-company-id="' + companyId + '" data-products="' + (productId || 0) + '"' +
                    ' data-amount="' + _.escape(row.drill_amount || row.daily || row.actual || '') + '"' +
                    ' data-qty="' + _.escape(row.drill_qty || row.daily_qty || row.actual_qty || '') + '">' +
                    _.escape(row.date) + '</span> ';
            }
            var kindHtml = kind ? '<span class="kr_kind">' + _.escape(kind) + '</span>' : '';
            var productDrill = function (kindName, amount, qty) {
                if (!productId || (!amount && !qty)) {
                    return null;
                }
                return {
                    kind: kindName,
                    companyId: companyId,
                    products: [productId],
                    amount: amount || '',
                    qty: qty || '',
                };
            };
            return '<tr class="kr_line_row">' +
                '<td class="' + cls + '"' + prodAttr + ' title="' + _.escape(((kind ? kind + ' ' : '') + (row.date ? row.date + ' ' : '') + (name || ''))) + '">' +
                dateHtml + kindHtml + _.escape(name || '') + '</td>' +
                this._cell('kr_sale', row.sales, row.sales_missing, row.sales_qty) +
                this._cell('kr_cost', row.actual, row.actual_missing, row.actual_qty, productDrill('actual', row.actual, row.actual_qty)) +
                this._cell('kr_cost', row.potential, row.potential_missing, row.potential_qty) +
                this._cell('kr_cost', row.daily, row.daily_missing, row.daily_qty, productDrill('daily', row.daily, row.daily_qty)) +
                this._cell('kr_cost', row.theo, row.theo_missing, row.theo_qty, productDrill('daily', row.theo, row.theo_qty)) +
                '<td class="kr_cost"></td><td class="kr_sale"></td>' +
                '<td class="kr_gap" title="' + _.escape(row.gap || '') + '">' + _.escape(row.gap || '') + '</td></tr>';
        },
        _onCategory: function (event) {
            var key = String($(event.currentTarget).closest('tr').attr('data-key'));
            var $kids = this.$('.kr_child').filter(function () {
                return String($(this).attr('data-key')) === key;
            });
            var open = $kids.filter('.kr_item:visible').length;
            this.$('.kr_child').hide();
            this.$('.kr_line_row').remove();
            this.$('.kr_category, .kr_item').removeClass('kr_item_on');
            if (!open) {
                $(event.currentTarget).closest('tr').addClass('kr_item_on');
                $kids.filter('.kr_item').show();
            }
        },
        _onItem: function (event) {
            var $row = $(event.currentTarget).closest('tr');
            var itemKey = String($row.attr('data-item-key') || '');
            var key = String($row.attr('data-key'));
            var company = this._openCompany;
            var category = _.find((company && company.categories) || [], function (row) {
                return String(row.key) === key;
            });
            var item = _.find((category && category.items) || [], function (row) {
                return String(row.key) === itemKey;
            });
            var already = $row.hasClass('kr_item_on') && $row.next('.kr_line_row').length;
            this.$('.kr_item').removeClass('kr_item_on');
            this.$('.kr_line_row').remove();
            if (!item || already) {
                return;
            }
            $row.addClass('kr_item_on');
            var lines = _.filter(category.lines || [], function (line) {
                if (item.recipe_id) {
                    return String(line.recipe_id) === String(item.recipe_id);
                }
                return !line.recipe_id && line.sale === item.name;
            });
            var names = _.map(lines, function (line) { return line.ingredient; });
            var closings = _.filter(category.closing || [], function (line) {
                if (item.product_id && String(line.product_id) === String(item.product_id)) {
                    return true;
                }
                return names.indexOf(line.product) >= 0;
            });
            var html = _.map(lines, function (line) {
                return this._detailRow('Ingredient', line.ingredient || '', line.product_id, {
                    date: line.date,
                    drill_kind: 'daily',
                    sales: line.sales,
                    sales_qty: line.sold,
                    sales_missing: line.sales_missing,
                    actual: line.actual,
                    actual_missing: line.actual_missing,
                    potential: line.potential_com,
                    potential_missing: line.potential_missing,
                    daily: line.daily,
                    daily_qty: line.daily_qty,
                    daily_missing: line.daily_missing,
                    theo: line.theo,
                    theo_qty: line.theoretical_qty,
                    theo_missing: line.theo_missing,
                    gap: (line.origin ? line.origin + '. ' : '') + (line.gap || ''),
                });
            }, this).join('');
            html += _.map(item.daily_lines || [], function (line) {
                return this._detailRow('', line.name || item.name, line.product_id || item.product_id, {
                    date: line.date,
                    drill_kind: 'daily',
                    daily: line.amount,
                    daily_qty: line.qty,
                    daily_missing: !line.amount || line.amount === '0.00',
                    gap: line.note || '',
                });
            }, this).join('');
            html += _.map(closings, function (line) {
                var note = 'Chef closing ' + (line.closing || '0.00');
                if (line.variance) {
                    note += ' · Var ' + line.variance;
                }
                if (line.state) {
                    note += ' · ' + line.state;
                }
                if (line.gap) {
                    note += ' · ' + line.gap;
                }
                return this._detailRow('Closing', line.product || '', line.product_id, {
                    date: line.date,
                    drill_kind: 'actual',
                    actual_qty: line.purchase,
                    theo_qty: line.theoretical,
                    gap: note,
                });
            }, this).join('');
            if (!html) {
                html = '<tr class="kr_line_row"><td colspan="9">No ingredient, consumption or closing in this period</td></tr>';
            }
            $row.after(html);
        },
        _plainNumber: function (value) {
            return parseFloat(String(value || '0').replace(/,/g, '')) || 0;
        },
        _onPurchases: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var $el = $(event.target).closest('.kr_drill, .kr_drill_cell');
            if (!$el.length) {
                return;
            }
            var companyId = parseInt($el.attr('data-company-id'), 10) || 0;
            var kind = $el.attr('data-kind') || 'actual';
            var products = String($el.attr('data-products') || '').split(',').filter(Boolean).map(function (id) {
                return parseInt(id, 10);
            }).filter(function (id) {
                return id;
            });
            if (!products.length) {
                var company = this._company(companyId);
                _.each((company && company.categories) || [], function (category) {
                    _.each(category.drill_products || [], function (productId) {
                        if (products.indexOf(productId) < 0) {
                            products.push(productId);
                        }
                    });
                });
            }
            var screenAmount = $el.attr('data-amount') || '';
            var screenQty = $el.attr('data-qty') || '';
            var self = this;
            this._rpc({
                model: 'cpabooks.recipe',
                method: 'get_key_result_purchases',
                args: [companyId, products, this.data.date_from, this.data.date_to, kind],
            }).then(function (result) {
                self._openPurchases(result || {}, screenAmount, screenQty);
            });
        },
        _openPurchases: function (result, screenAmount, screenQty) {
            var rows = _.map(result.lines || [], function (line) {
                return '<tr><td>' + _.escape(line.date || '') + '</td><td>' + _.escape(line.bill || '') + '</td>' +
                    '<td class="kr_text">' + _.escape(line.partner || '') + '</td>' +
                    '<td class="kr_text">' + _.escape(line.product || '') + '</td>' +
                    '<td class="kr_num">' + _.escape(line.qty || '') + '</td>' +
                    '<td class="kr_num">' + _.escape(line.amount || '') + '</td></tr>';
            }).join('');
            if (!rows) {
                rows = '<tr><td colspan="6">No purchase bill in this window</td></tr>';
            }
            var sameAmount = screenAmount && Math.abs(this._plainNumber(screenAmount) - this._plainNumber(result.total_amount)) < 0.02;
            var footer = '';
            if (screenAmount && !sameAmount) {
                footer = '<tr class="kr_subtotal"><td colspan="4">Purchase bills</td><td class="kr_num">' + _.escape(result.total_qty || '') + '</td><td class="kr_num">' + _.escape(result.total_amount || '') + '</td></tr>' +
                    '<tr class="kr_total"><td colspan="4">Total</td><td class="kr_num">' + _.escape(screenQty || '') + '</td><td class="kr_num">' + _.escape(screenAmount) + '</td></tr>';
            } else {
                footer = '<tr class="kr_total"><td colspan="4">Total</td><td class="kr_num">' + _.escape(screenQty || result.total_qty || '') + '</td><td class="kr_num">' + _.escape(screenAmount || result.total_amount || '') + '</td></tr>';
            }
            var note = result.window_note ? '<p class="kr_purchase_note">' + _.escape(result.window_note) + '</p>' : '';
            var html = '<div class="kr_purchase_box"><p class="kr_purchase_window">' + _.escape(result.window || '') + '</p>' + note +
                '<table class="kr_table kr_purchases"><thead><tr><th>Date</th><th>Bill</th><th>Vendor</th><th>Item</th><th class="kr_num">Qty</th><th class="kr_num">Amount</th></tr></thead><tbody>' +
                rows + footer + '</tbody></table></div>';
            new Dialog(this, {
                title: result.title || 'Purchases',
                size: 'large',
                $content: $(html),
                buttons: [{text: 'Close', close: true, classes: 'btn-secondary'}],
            }).open();
        },
        _onExport: function () {
            var self = this;
            this._rpc({
                model: 'cpabooks.recipe',
                method: 'export_key_results_xlsx',
                args: [this.data.date_from, this.data.date_to],
            }).then(function (result) {
                if (!result || !result.file) {
                    return;
                }
                var binary = atob(result.file);
                var bytes = new Uint8Array(binary.length);
                for (var index = 0; index < binary.length; index++) {
                    bytes[index] = binary.charCodeAt(index);
                }
                var blob = new Blob([bytes], {type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
                var link = document.createElement('a');
                var url = URL.createObjectURL(blob);
                link.href = url;
                link.download = result.filename || 'key_results.xlsx';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            });
        },
        _onProdMenu: function (event) {
            var productId = parseInt($(event.currentTarget).attr('data-product-id'), 10);
            if (!productId) {
                return;
            }
            event.preventDefault();
            event.stopPropagation();
            this._removeCard();
            var self = this;
            var recipeId = parseInt($(event.currentTarget).closest('tr').attr('data-recipe-id'), 10);
            var menu = '<div class="kr_menu">';
            if (recipeId) {
                menu += '<button type="button" class="kr_open_recipe">See recipe</button>';
            }
            menu += '<button type="button" class="kr_open_product">Open to see details</button></div>';
            this.$card = $(menu);
            $('body').append(this.$card);
            var left = Math.min(event.clientX, window.innerWidth - 190);
            var top = Math.min(event.clientY, window.innerHeight - 72);
            this.$card.css({top: top, left: left});
            this.$card.on('click', '.kr_open_recipe', function (clickEvent) {
                clickEvent.preventDefault();
                clickEvent.stopPropagation();
                self._openRecipe(recipeId);
            });
            this.$card.on('click', '.kr_open_product', function (clickEvent) {
                clickEvent.preventDefault();
                clickEvent.stopPropagation();
                self._openFromProduct(productId);
            });
            setTimeout(function () {
                $(document).one('click', function () {
                    self._removeCard();
                });
            }, 0);
        },
        _removeCard: function () {
            if (this.$card) {
                this.$card.remove();
                this.$card = null;
            }
        },
        _openFromProduct: function (productId) {
            var card = this._cardCache[productId];
            if (card && card.tmpl_id) {
                this._openProduct(card.tmpl_id);
                return;
            }
            var self = this;
            this._rpc({
                model: 'cpabooks.recipe',
                method: 'get_product_card',
                args: [productId, this._openCompany && this._openCompany.id],
            }).then(function (loaded) {
                self._cardCache[productId] = loaded || {};
                self._openProduct(loaded && loaded.tmpl_id);
            });
        },
        _openRecipe: function (recipeId) {
            if (!recipeId) {
                return;
            }
            this._removeCard();
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Recipe',
                res_model: 'cpabooks.recipe',
                res_id: recipeId,
                views: [[false, 'form']],
                target: 'current',
            });
        },
        _openProduct: function (templateId) {
            if (!templateId) {
                return;
            }
            this._removeCard();
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Product',
                res_model: 'product.template',
                res_id: templateId,
                views: [[false, 'form']],
                target: 'current',
            });
        },
        _onOpenConsumption: function (event) {
            var $button = $(event.currentTarget);
            var domain = [
                ['company_id', '=', parseInt($button.data('company-id'), 10)],
                ['date', '>=', this.data.date_from],
                ['date', '<=', this.data.date_to],
            ];
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Consumption Analysis',
                res_model: 'cpabooks.recipe.consumption',
                views: [[false, 'list'], [false, 'pivot']],
                domain: domain,
                target: 'current',
            });
        },
        _onOpenClosing: function (event) {
            var company = this._company($(event.currentTarget).data('company-id'));
            var ids = [];
            _.each((company && company.categories) || [], function (category) {
                _.each(category.closing || [], function (line) {
                    ids.push(line.id);
                });
            });
            ids = _.uniq(ids);
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Closing Stock',
                res_model: 'cpabooks.recipe.closing',
                views: [[false, 'list'], [false, 'form']],
                domain: [['id', 'in', ids.length ? ids : [0]]],
                target: 'current',
            });
        },
    });

    core.action_registry.add('cpabooks_recipe_key_results', KeyResults);
    return KeyResults;
});
