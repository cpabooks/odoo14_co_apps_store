# -*- coding: utf-8 -*-
# from odoo import http


# class CpabooksFieldServieceExtend(http.Controller):
#     @http.route('/co_field_service/co_field_service/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/co_field_service/co_field_service/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('co_field_service.listing', {
#             'root': '/co_field_service/co_field_service',
#             'objects': http.request.env['co_field_service.co_field_service'].search([]),
#         })

#     @http.route('/co_field_service/co_field_service/objects/<model("co_field_service.co_field_service"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('co_field_service.object', {
#             'object': obj
#         })
