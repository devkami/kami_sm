# -*- coding: utf-8 -*-
from odoo import fields, models, api


class KamiSmAttendanceCost(models.Model):
    _name = 'kami_sm.attendance.cost'
    _description = 'Attendance Cost Model for Kami Service Manager Module'
    _order = 'id'


    name = fields.Text(
      string='Título',
      required=True,
      compute='_compute_default_name',
      readonly=True
    )
    description = fields.Selection(
      [('daily', 'Diária'),
      ('hosting', 'Hospedagem'),
      ('transport', 'Transporte')],
      string='Descrição',
      default='daily'
    )
    active = fields.Boolean(default=True)
    attendance_id = fields.Many2one(
      'kami_sm.attendance',
      string='Atendimento'
    )
    cost_type = fields.Selection(
      [('cash', 'Dinheiro'),
      ('product', 'Produto')],
      string='Tipo',
      default='cash'
    )
    partial = fields.Boolean(
      string='Parcial',
      default=False
    )
    cost = fields.Monetary(
      string='Valor',
      currency_field='currency_id'
    )
    currency_id = fields.Many2one(
      'res.currency',
      string='Currency'
    )
    order_id = fields.Char(string='Pedido de Venda')
    invoice_id = fields.Many2one('account.move', string='Fatura de Pagamento')
    _was_paid = fields.Boolean(default=False, compute='_compute_was_paid')
    partner_id = fields.Many2one(
      'res.partner',
      string='Parceiro',
      related='attendance_id.partner_id'
    )
    attendance_date = fields.Date(related='attendance_id.start_date')
    invoice_date = fields.Date(related='invoice_id.invoice_date')
    invoice_date_due = fields.Date(related='invoice_id.invoice_date_due')
    invoice_state = fields.Selection(related='invoice_id.state')
    _has_invoice = fields.Boolean(default=False, compute='_compute_has_invoice')
    # ------------------------------------------------------------
    # COMPUTES
    # ------------------------------------------------------------

    @api.depends('attendance_id')
    def _compute_default_name(self):
      for attendance_cost in self:
        attendance_cost.name = attendance_cost.attendance_id.name

    @api.depends('invoice_id', 'cost_type', 'order_id')
    def _compute_was_paid(self):
      for attendance_cost in self:
        attendance_cost._was_paid = ( attendance_cost.invoice_id and \
          attendance_cost.invoice_id.state == 'posted')\
        or (attendance_cost.cost_type == 'product' and attendance_cost.order_id)

    def _compute_has_invoice(self):
      for attendance_cost in self:
        attendance_cost._has_invoice = attendance_cost.invoice_id.id != False

    # ------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------

    def action_open_invoice(self):
      for attendance_cost in self:        
        if attendance_cost.invoice_id:
          return {
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'context': self._context
          }

