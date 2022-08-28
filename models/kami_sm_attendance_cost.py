# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class KamiSmAttendanceCost(models.Model):
    _name = "kami_sm.attendance.cost"
    _description = "Attendance Cost Model for Kami Service Manager Module"
    _order = "id"


    name = fields.Text(
      string="Título", 
      required=True,
      compute="_compute_default_name",
      readonly=True
    )
    description = fields.Text(
      string="Descrição",
      default="Pagamento Diária"
    )
    active = fields.Boolean(default=True)    
    attendance_id = fields.Many2one(
      "kami_sm.attendance",
      string="Atendimento"
    )
    cost_type = fields.Selection(      
      [("cash", "Dinheiro"),
      ("product", "Produto")],
      string="Tipo",
      default="new"
    )
    partial = fields.Boolean(
      string="Parcial",
      default=False
    )
    cost = fields.Monetary(
      string="Valor", 
      currency_field="currency_id"
    )
    currency_id = fields.Many2one(
      "res.currency",
      string="Currency"
    )
    order_id = fields.Char(string="Pedido de Venda")    
    
    # ------------------------------------------------------------
    # COMPUTES 
    # ------------------------------------------------------------

    @api.depends("attendance_id")
    def _compute_default_name(self):
      for record in self:
        record.name = record.attendance_id.name 
    