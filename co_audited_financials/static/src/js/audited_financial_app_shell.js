odoo.define('co_audited_financials.audited_financial_app_shell', function (require) {
'use strict';

var ActionManager = require('web.ActionManager');
var core = require('web.core');

var SHELL_CLASS = 'o_audited_financial_app_shell';

var NAV_ITEMS = [
    {section: 'Home', items: [
        {key: 'overview', label: 'Dashboard', xmlid: 'co_audited_financials.action_audited_financials_dashboard_client'},
        {key: 'afg_pl', label: 'Statement of Profit or Loss', xmlid: 'co_audited_financials.action_audited_financials_dashboard_pl'},
        {key: 'afg_bs', label: 'Statement of Financial Position', xmlid: 'co_audited_financials.action_audited_financials_dashboard_bs'},
        {key: 'afg_review', label: 'IFRS / FTA Review', xmlid: 'co_audited_financials.action_audited_financials_dashboard_review'},
    ]},
    {section: 'Configuration', items: [
        {key: 'afg_coa', label: 'Chart of Accounts', xmlid: 'co_audited_financials.action_afg_chart_of_accounts'},
        {key: 'afg_versions', label: 'Versions', xmlid: 'co_audited_financials.action_audited_financial_version'},
    ]},
];

var AUDITED_RES_MODELS = {
    'audited.financial.group': true,
    'audited.financial.group.line': true,
    'audited.financial.version': true,
    'audited.financial.line': true,
    'audited.financial.note': true,
    'audited.financial.edit.log': true,
    'audited.financial.alert': true,
    'audited.financial.sensitive.wizard': true,
    'audited.financial.ctf.group': true,
};

var XMLID_TO_KEY = {};
_.each(NAV_ITEMS, function (block) {
    _.each(block.items, function (item) {
        if (item.xmlid) {
            XMLID_TO_KEY[item.xmlid] = item.key;
        }
    });
});

function isAuditedFinancialSidebarMode() {
    return require('web.session').app_web_ui_mode === 'audited_financial';
}

function isAuditedFinancialAction(action) {
    if (!action) {
        return false;
    }
    if (action.tag === 'audited_financials_dashboard') {
        return true;
    }
    if (action.res_model === 'account.account' || action.res_model === 'account.group') {
        var mapCtx = action.context || {};
        var mapXml = action.xml_id || action.xmlId || '';
        return !!(mapCtx.afg_map_list || String(mapXml).indexOf('action_afg') !== -1);
    }
    if (action.res_model && AUDITED_RES_MODELS[action.res_model]) {
        return true;
    }
    if (action.tag === 'account_report') {
        var ctx = action.context || {};
        if (ctx.project_multicompany_kind) {
            return true;
        }
        if (action.name && String(action.name).toLowerCase().indexOf('multico') !== -1) {
            return true;
        }
    }
    if (action.xml_id && XMLID_TO_KEY[action.xml_id]) {
        return true;
    }
    if (action.xml_id && action.xml_id.indexOf('co_audited_financials.') === 0) {
        return true;
    }
    return false;
}

function stackHasAuditedFinancial(actionManager) {
    return _.some(actionManager.controllerStack || [], function (controller) {
        return controller && controller.action && isAuditedFinancialAction(controller.action);
    });
}

function activeKeyFromAction(action) {
    if (!action) {
        return 'overview';
    }
    if (action.xml_id && XMLID_TO_KEY[action.xml_id]) {
        return XMLID_TO_KEY[action.xml_id];
    }
    if (action.tag === 'audited_financials_dashboard') {
        var section = (action.context || {}).afg_section;
        if (section === 'pl') {
            return 'afg_pl';
        }
        if (section === 'bs') {
            return 'afg_bs';
        }
        if (section === 'review') {
            return 'afg_review';
        }
        return 'overview';
    }
    if (action.tag === 'account_report') {
        var kind = (action.context || {}).project_multicompany_kind;
        if (kind === 'bs') {
            return 'bs_multico';
        }
        if (kind === 'pl') {
            return 'pl_multico';
        }
    }
    if (action.res_model === 'audited.financial.version') {
        return 'afg_versions';
    }
    if (action.res_model === 'audited.financial.group') {
        return 'afg_setup';
    }
    return 'overview';
}

function renderSidebarHtml(activeKey) {
    var html = '<aside class="o_audited_financial_app_sidebar">' +
        '<div class="o_audited_financial_app_sidebar_title">Audited Financial Dashboard</div>' +
        '<ul class="list-group list-group-flush o_audited_financial_app_sidebar_nav">';
    _.each(NAV_ITEMS, function (block) {
        if (block.section) {
            html += '<li class="list-group-item o_audited_financial_app_sidebar_section">' +
                _.escape(block.section) + '</li>';
        }
        _.each(block.items, function (item) {
            var cls = item.key === activeKey ? ' active' : '';
            html += '<li class="list-group-item' + cls + '"><a href="#" data-nav-key="' + item.key + '">' +
                _.escape(item.label) + '</a></li>';
        });
    });
    html += '</ul></aside>';
    return html;
}

function bindSidebarNav($sidebar, doActionFn) {
    $sidebar.find('.o_audited_financial_app_sidebar_nav a').off('click').on('click', function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var navKey = $(ev.currentTarget).data('navKey');
        if (!navKey || !doActionFn) {
            return;
        }
        var selectedItem = null;
        _.each(NAV_ITEMS, function (block) {
            _.each(block.items, function (item) {
                if (!selectedItem && item.key === navKey) {
                    selectedItem = item;
                }
            });
        });
        if (selectedItem) {
            return doActionFn(selectedItem);
        }
    });
}

var AppShell = {
    SHELL_CLASS: SHELL_CLASS,
    NAV_ITEMS: NAV_ITEMS,

    activate: function () {
        $('body').addClass(SHELL_CLASS);
    },

    deactivate: function () {
        $('body').removeClass(SHELL_CLASS);
        // Only unwrap shell-created layouts (have .o_audited_financial_app_content).
        // The dashboard QWeb used to share class o_audited_financial_app_layout — removing
        // those wiped the whole AFG screen after F5 when ui_mode != audited_financial.
        $('.o_audited_financial_app_layout').each(function () {
            var $layout = $(this);
            var $main = $layout.children('.o_audited_financial_app_content');
            if (!$main.length) {
                return;
            }
            var $content = $layout.closest('.o_content');
            if ($content.length) {
                $main.children().appendTo($content);
                $layout.remove();
            }
        });
    },

    isAuditedFinancialSidebarMode: isAuditedFinancialSidebarMode,

    isAuditedFinancialAction: isAuditedFinancialAction,

    activeKeyFromAction: activeKeyFromAction,

    isNativeBackendScreen: function (action) {
        if (!action) {
            return false;
        }
        if (action.res_model === 'res.config.settings') {
            return true;
        }
        if (_.contains(['res.partner', 'account.move', 'account.journal', 'account.payment'], action.res_model)) {
            return true;
        }
        return false;
    },

    mountSidebar: function ($host, activeKey, doActionFn) {
        if (!$host || !$host.length) {
            return $();
        }
        var $existing = $host.children('.o_audited_financial_app_sidebar');
        if ($existing.length) {
            $existing.replaceWith($(renderSidebarHtml(activeKey)));
        } else {
            $host.prepend($(renderSidebarHtml(activeKey)));
        }
        var $sidebar = $host.children('.o_audited_financial_app_sidebar').first();
        bindSidebarNav($sidebar, doActionFn);
        return $sidebar;
    },

    wrapActionContent: function ($content, activeKey, doActionFn) {
        if (!$content || !$content.length) {
            return $();
        }
        var $layout = $content.children('.o_audited_financial_app_layout').first();
        if (!$layout.length) {
            $layout = $('<div class="o_audited_financial_app_layout row no-gutters"/>');
            var $sidebarHost = $('<div class="o_audited_financial_sidebar_host col-auto"/>');
            var $main = $('<div class="o_audited_financial_app_content col"/>');
            $main.append($content.contents());
            $layout.append($sidebarHost).append($main);
            $content.empty().append($layout);
        }
        this.mountSidebar($layout.children('.o_audited_financial_sidebar_host').first(), activeKey, doActionFn);
        return $layout.find('.o_audited_financial_app_content').first();
    },

    syncActionManager: function (actionManager, action) {
        if (!actionManager) {
            return;
        }
        var self = this;
        if (this.isNativeBackendScreen(action)) {
            this.deactivate();
            return;
        }
        var onAfg = isAuditedFinancialAction(action) || stackHasAuditedFinancial(actionManager);
        if (!this.isAuditedFinancialSidebarMode()) {
            // Apps-menu entry: keep dashboard DOM; do not run deactivate (class collision wipe).
            if (!onAfg) {
                this.deactivate();
            }
            return;
        }
        if (!onAfg) {
            this.deactivate();
            return;
        }
        this.activate();
        var activeKey = activeKeyFromAction(action);
        var $action = $('.o_action_manager .o_action').filter(':visible').last();
        var $content = $action.children('.o_content').first();
        if (!$content.length) {
            $content = $action.find('.o_content').first();
        }
        if (!$content.length) {
            return;
        }
        var doActionFn = function (item) {
            if (item.xmlid) {
                return actionManager.do_action(item.xmlid);
            }
            return $.when();
        };
        self.wrapActionContent($content, activeKey, doActionFn);
        $content.find('.o_audited_financial_app_sidebar_nav .list-group-item').removeClass('active');
        $content.find('.o_audited_financial_app_sidebar_nav a[data-nav-key="' + activeKey + '"]')
            .closest('.list-group-item').addClass('active');
    },
};

ActionManager.include({
    /**
     * Stale bookmarks keep a dead numeric action id (e.g. 15088). /web/action/load
     * returns false → blank screen. Recover by loading the AFG dashboard xmlid when
     * the URL menu is Audited Financial.
     *
     * Important: do NOT raise a branded "AFG action failed" for unrelated apps
     * (Icon View / Invoicing / etc.) when a numeric action id simply misses.
     */
    doAction: function (action, options) {
        var self = this;
        var _superDoAction = this._super.bind(this);
        var requested = action;
        var dashXmlids = [
            'co_audited_financials.action_audited_financials_dashboard_client',
            'co_audited_financials.action_audited_financials_dashboard_client',
        ];
        var isNumeric = _.isNumber(requested) || (/^\d+$/).test(String(requested || ''));
        var requestedStr = typeof requested === 'string' ? requested : '';
        var isAfgXmlid = requestedStr.indexOf('co_audited_financials.') === 0 ||
            requestedStr.indexOf('co_audited_financials.action_audited_financials') === 0;
        var passThrough = function (errorOrFalse) {
            if (errorOrFalse) {
                return Promise.reject(errorOrFalse);
            }
            return $.when(false);
        };
        var retryDash = function () {
            return _superDoAction(dashXmlids[0], options || {}).then(function (result) {
                if (result) {
                    return result;
                }
                return _superDoAction(dashXmlids[1], options || {});
            });
        };
        var maybeRetry = function (errorOrFalse) {
            if (requested && typeof requested === 'object' && requested.type) {
                return passThrough(errorOrFalse);
            }
            if (isAfgXmlid) {
                // Already on an AFG xmlid — try the sibling module xmlid once, then stop.
                if (requestedStr === dashXmlids[0]) {
                    return _superDoAction(dashXmlids[1], options || {}).then(function (result) {
                        return result || passThrough(errorOrFalse);
                    }).guardedCatch(function (err) {
                        return passThrough(err || errorOrFalse);
                    });
                }
                return passThrough(errorOrFalse);
            }
            if (!isNumeric) {
                return passThrough(errorOrFalse);
            }
            var state = {};
            try {
                state = $.bbq.getState(true) || {};
            } catch (e) {
                state = {};
            }
            var menuId = state.menu_id ? parseInt(state.menu_id, 10) : 0;
            if (!menuId) {
                // Without Audited Financial menu context, do not assume AFG.
                return passThrough(errorOrFalse);
            }
            return self._rpc({
                model: 'ir.ui.menu',
                method: 'search_read',
                args: [[['id', '=', menuId]], ['name']],
                kwargs: {limit: 1},
            }).then(function (rows) {
                var name = (rows && rows[0] && rows[0].name) || '';
                if (!/audited financial/i.test(name)) {
                    return passThrough(errorOrFalse);
                }
                try {
                    if ($.bbq && $.bbq.pushState) {
                        $.bbq.pushState({action: dashXmlids[0]}, 2);
                    }
                } catch (e2) { /* ignore */ }
                return retryDash();
            }).guardedCatch(function () {
                return passThrough(errorOrFalse);
            });
        };
        return _superDoAction(action, options).then(function (result) {
            if (result) {
                return result;
            }
            // /web/action/load can return false (HTTP 200) → blank AFG screen only.
            if (isNumeric || isAfgXmlid) {
                return maybeRetry(false);
            }
            return result;
        }).guardedCatch(function (error) {
            if (isNumeric || isAfgXmlid) {
                return maybeRetry(error);
            }
            return Promise.reject(error);
        });
    },

    _handleAction: function (action, options) {
        var self = this;
        return this._super(action, options).then(function () {
            AppShell.syncActionManager(self, action);
        });
    },
});

core.bus.on('show_home_menu', null, function () {
    AppShell.deactivate();
});
core.bus.on('will_show_home_menu', null, function () {
    AppShell.deactivate();
});

return AppShell;
});
