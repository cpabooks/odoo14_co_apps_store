# -*- coding: utf-8 -*-
import logging

from odoo.addons.cpabooks_chart_of_accounts.hooks import post_init_hook

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Databases upgrading from the 0.x compatibility shell never ran post_init_hook."""
    if not version:
        return
    _logger.info('CPABooks CoA: upgrading from %s, running COA setup', version)
    # The former V1 add-on switched off every view of this module; bring them back.
    cr.execute(
        """
        UPDATE ir_ui_view AS view
           SET active = TRUE
          FROM ir_model_data AS data
         WHERE data.module = 'cpabooks_chart_of_accounts'
           AND data.model = 'ir.ui.view'
           AND data.res_id = view.id
           AND view.active = FALSE
        """
    )
    post_init_hook(cr, None)
