# -*- coding: utf-8 -*-
# from odoo import http


# class CpabooksSequences(http.Controller):
#     @http.route('/co_document_sequences/co_document_sequences/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/co_document_sequences/co_document_sequences/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('co_document_sequences.listing', {
#             'root': '/co_document_sequences/co_document_sequences',
#             'objects': http.request.env['co_document_sequences.co_document_sequences'].search([]),
#         })

#     @http.route('/co_document_sequences/co_document_sequences/objects/<model("co_document_sequences.co_document_sequences"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('co_document_sequences.object', {
#             'object': obj
#         })
