# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class co_document_sequences(models.Model):
#     _name = 'co_document_sequences.co_document_sequences'
#     _description = 'co_document_sequences.co_document_sequences'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
