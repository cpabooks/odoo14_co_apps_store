from odoo import api, fields, models


class MaterialReturnLine(models.Model):
    _name = 'material.return.line'
    _description = 'Material Return Line'

    task_id = fields.Many2one(
        'project.task',
        string='CRN No',
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    description = fields.Char(string='Description')
    quantity = fields.Float(string='Quantity', default=1.0)
    return_move_id = fields.Many2one(
        'stock.move',
        string='Return Move',
        copy=False,
        ondelete='set null',
    )
    quantity_done = fields.Float(
        string='Returned Quantity',
        compute='_compute_quantity_done',
    )
    amount_done = fields.Float(
        string='Returned Amount',
        compute='_compute_quantity_done',
    )

    @api.depends(
        'task_id',
        'return_move_id',
        'return_move_id.quantity_done',
        'return_move_id.state',
    )
    def _compute_quantity_done(self):
        picking_model = self.env['stock.picking']
        has_issue_task_field = 'issue_project_task_id' in picking_model._fields
        for rec in self:
            rec.quantity_done = 0.0
            rec.amount_done = 0.0
            if rec.return_move_id:
                move = rec.return_move_id
                if move.state != 'cancel':
                    rec.quantity_done = move.quantity_done
                    if 'amount' in move._fields:
                        rec.amount_done = move.amount
                    else:
                        rec.amount_done = move.quantity_done * (rec.product_id.list_price or 0.0)
            elif rec.task_id and has_issue_task_field:
                pickings = picking_model.search([
                    ('issue_project_task_id', '=', rec.task_id.id),
                    ('is_material_return', '=', True),
                    ('state', '=', 'done'),
                ])
                moves = pickings.move_ids_without_package.filtered(
                    lambda mv: mv.product_id.id == rec.product_id.id and mv.state != 'cancel'
                )
                rec.quantity_done = sum(moves.mapped('quantity_done'))
                if moves and 'amount' in moves._fields:
                    rec.amount_done = sum(moves.mapped('amount'))
                else:
                    rec.amount_done = rec.quantity_done * (rec.product_id.list_price or 0.0)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and not self.description:
            self.description = self.product_id.display_name
