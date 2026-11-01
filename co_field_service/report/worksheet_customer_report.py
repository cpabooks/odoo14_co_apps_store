# -*- coding: utf-8 -*-

from odoo import api, models


class TaskCustomCustomerCopyReport(models.AbstractModel):
    _name = 'report.co_field_service.worksheet_custom_customer'
    _description = 'Task Worksheet Customer Copy Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['project.task'].browse(docids).sudo()

        return {
            'doc_ids': docids,
            'doc_model': 'project.task',
            'docs': docs,
            'worksheet_map': {},
            'report_copy_label': 'TMC Customer',
        }
