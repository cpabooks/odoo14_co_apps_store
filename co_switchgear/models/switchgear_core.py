# -*- coding: utf-8 -*-
"""Self-contained estimate, requisition, and quality models for the apps store."""

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class JobEstimateLine(models.Model):
    _name = 'job.estimate.line'
    _description = 'Switchgear Estimate Line'

    estimate_id = fields.Many2one('job.estimate', ondelete='cascade')
    labour_estimate_id = fields.Many2one('job.estimate', ondelete='cascade')
    overhead_estimate_id = fields.Many2one('job.estimate', ondelete='cascade')
    line_type = fields.Selection([
        ('material', 'Material'),
        ('labour', 'Labour'),
        ('overhead', 'Overhead'),
    ], default='material')
    product_id = fields.Many2one('product.product', string='Product')
    bom_product_id = fields.Many2one('product.product', string='BoM Product')
    description = fields.Char()
    quantity = fields.Float(default=1.0)
    hours = fields.Float(default=0.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    price_unit = fields.Float()
    discount = fields.Float()
    type = fields.Selection([
        ('material', 'Material'),
        ('labour', 'Labour'),
        ('overhead', 'Overhead'),
    ], default='material')
    subtotal = fields.Float()


class JobEstimate(models.Model):
    _name = 'job.estimate'
    _description = 'Switchgear Job Estimate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(default='New', copy=False, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True,
    )
    date = fields.Date(default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    sales_person_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')
    project_id = fields.Many2one('project.project', string='Job Order')
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    bom_id = fields.Many2one('mrp.bom', string='BoM Item Template')
    bom_reference = fields.Char(related='bom_id.name', string='BOM Reference')
    bom_product_id = fields.Many2one('product.product', string='BoM Item Name')
    bom_count = fields.Integer(compute='_compute_bom_count')
    customer_ref = fields.Char(string='Customer Reference')
    crm_reference = fields.Char(related='opportunity_id.enquiry_number', string='CRM Reference')
    description = fields.Text()
    profit_percent = fields.Float(string='Profit %', default=10.0)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', tracking=True)
    material_estimation_ids = fields.One2many(
        'job.estimate.line', 'estimate_id', string='Materials',
    )
    labour_estimation_ids = fields.One2many(
        'job.estimate.line', 'labour_estimate_id', string='Labour',
    )
    overhead_estimation_ids = fields.One2many(
        'job.estimate.line', 'overhead_estimate_id', string='Overhead',
    )
    total_job_estimate = fields.Float(compute='_compute_total', store=True)
    sale_quotation_id = fields.Many2one('sale.order', string='Quotation')

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('name') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('switchgear.job.estimate') or 'EST'
        return super().create(vals)

    @api.depends(
        'material_estimation_ids.subtotal',
        'labour_estimation_ids.subtotal',
        'overhead_estimation_ids.subtotal',
        'profit_percent',
    )
    def _compute_total(self):
        for rec in self:
            base = (
                sum(rec.material_estimation_ids.mapped('subtotal'))
                + sum(rec.labour_estimation_ids.mapped('subtotal'))
                + sum(rec.overhead_estimation_ids.mapped('subtotal'))
            )
            rec.total_job_estimate = base * (1.0 + (rec.profit_percent or 0.0) / 100.0)

    def _compute_bom_count(self):
        for job in self:
            job.bom_count = self.env['mrp.bom'].search_count([('estimate_id', '=', job.id)])

    def action_job_confirm(self):
        self.write({'state': 'confirmed'})
        return True

    def action_approve(self):
        self.write({'state': 'approved'})
        return True

    def action_create_quotation(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_('Set a customer before creating a quotation.'))
        product = self.bom_product_id
        line_vals = {
            'name': self.name,
            'product_uom_qty': 1.0,
            'price_unit': self.total_job_estimate or 0.0,
        }
        if product:
            line_vals.update({
                'product_id': product.id,
                'name': product.display_name,
                'product_uom': product.uom_id.id,
            })
        order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'opportunity_id': self.opportunity_id.id,
            'job_estimate_id': self.id,
            'order_line': [(0, 0, line_vals)],
        })
        self.sale_quotation_id = order.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': order.id,
            'view_mode': 'form',
        }

    @api.onchange('bom_id')
    def get_bom_product(self):
        for rec in self:
            rec.material_estimation_ids = [(5, 0, 0)]
            product = False
            if rec.bom_id and rec.bom_id.product_tmpl_id:
                product = self.env['product.product'].search([
                    ('product_tmpl_id', '=', rec.bom_id.product_tmpl_id.id),
                ], limit=1)
            rec.bom_product_id = product
            lines = []
            for line in rec.bom_id.bom_line_ids:
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'type': 'material',
                    'quantity': line.product_qty,
                    'uom_id': line.product_uom_id.id,
                    'price_unit': line.product_id.lst_price,
                    'subtotal': line.product_qty * line.product_id.lst_price,
                }))
            rec.material_estimation_ids = lines

    def action_create_bom(self):
        if not self.bom_product_id:
            raise UserError(_('Please select BOM Product to create BOM'))
        bom = self.env['mrp.bom'].create({
            'product_id': self.bom_product_id.id,
            'product_tmpl_id': self.bom_product_id.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'estimate_id': self.id,
            'project_id': self.project_id.id,
            'partner_id': self.partner_id.id,
        })
        for line in self.material_estimation_ids:
            self.env['mrp.bom.line'].create({
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'bom_id': bom.id,
                'product_uom_id': line.uom_id.id,
            })
        for line in self.labour_estimation_ids:
            self.env['mrp.bom.line'].create({
                'product_id': line.product_id.id,
                'product_qty': line.hours or line.quantity,
                'bom_id': bom.id,
                'product_uom_id': line.uom_id.id,
            })
        for line in self.overhead_estimation_ids:
            self.env['mrp.bom.line'].create({
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'bom_id': bom.id,
                'product_uom_id': line.uom_id.id,
            })
        return True


class QualityPointTestType(models.Model):
    _name = 'quality.point.test_type'
    _description = 'Quality Test Type'

    name = fields.Char(required=True)
    technical_name = fields.Char()


class QualityAlertTeam(models.Model):
    _name = 'quality.alert.team'
    _description = 'Quality Team'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)


class QualityAlertStage(models.Model):
    _name = 'quality.alert.stage'
    _description = 'Quality Alert Stage'

    name = fields.Char(required=True)
    done = fields.Boolean()


class QualityAlert(models.Model):
    _name = 'quality.alert'
    _description = 'Quality Alert'
    _inherit = ['mail.thread']

    name = fields.Char(default='New')
    title = fields.Char()
    product_id = fields.Many2one('product.product')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    team_id = fields.Many2one('quality.alert.team')
    project_id = fields.Many2one('project.project')
    stage_id = fields.Many2one('quality.alert.stage')
    description = fields.Text()

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('name') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('switchgear.quality.alert') or 'QA'
        return super().create(vals)


class QualityPoint(models.Model):
    _name = 'quality.point'
    _description = 'Quality Control Point'

    name = fields.Char(required=True)
    product_id = fields.Many2one('product.product')
    test_type_id = fields.Many2one('quality.point.test_type')
    team_id = fields.Many2one('quality.alert.team')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)


class QualityCheck(models.Model):
    _name = 'quality.check'
    _description = 'Quality Check'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default='New', copy=False)
    product_id = fields.Many2one('product.product', required=True)
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    picking_id = fields.Many2one('stock.picking')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    team_id = fields.Many2one('quality.alert.team')
    test_type_id = fields.Many2one('quality.point.test_type')
    project_id = fields.Many2one('project.project')
    quality_state = fields.Selection([
        ('none', 'To Do'),
        ('pass', 'Passed'),
        ('fail', 'Failed'),
    ], default='none', tracking=True)
    alert_ids = fields.One2many('quality.alert', 'check_id')
    job_order_id = fields.Many2one('stock.picking', string='Job Order')
    partner_id = fields.Many2one('res.partner', string='Customer')
    control_date = fields.Date(default=fields.Date.context_today)

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('name') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('switchgear.quality.check') or 'QC'
        return super().create(vals)

    def do_pass(self):
        self.write({'quality_state': 'pass'})

    def do_fail(self):
        self.write({'quality_state': 'fail'})

    def do_alert(self):
        self.ensure_one()
        alert = self.env['quality.alert'].create({
            'title': self.name,
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'team_id': self.team_id.id,
            'project_id': self.project_id.id,
            'check_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'quality.alert',
            'res_id': alert.id,
            'view_mode': 'form',
        }


class QualityAlertCheck(models.Model):
    _inherit = 'quality.alert'

    check_id = fields.Many2one('quality.check')


class MaterialRequisitionLine(models.Model):
    _name = 'requisition.line'
    _description = 'Purchase Requisition Line'

    requisition_id = fields.Many2one('material.purchase.requisition', ondelete='cascade')
    product_id = fields.Many2one('product.product', required=True)
    description = fields.Char()
    qty = fields.Float(default=1.0)
    uom_id = fields.Many2one('uom.uom')


class MaterialPurchaseRequisition(models.Model):
    _name = 'material.purchase.requisition'
    _description = 'Purchase Requisition'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(default='New', copy=False)
    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one('hr.department')
    requisition_date = fields.Date(default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    reason_for_requisition = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)
    requisition_line_ids = fields.One2many('requisition.line', 'requisition_id')

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('name') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('switchgear.purchase.requisition') or 'PR'
        return super().create(vals)

    def action_confirm(self):
        self.write({'state': 'confirm'})


class AccountMove(models.Model):
    _inherit = 'account.move'

    project_id = fields.Many2one('project.project', string='Project / Job')
