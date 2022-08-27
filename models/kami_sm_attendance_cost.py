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
      string="Descrição"
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
    partial_cost = fields.Boolean(
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
    account_payment_info = fields.Many2one(
      "kami_sm.partner.account",
      string="Dados Bancários Para Pagamento"
    )
    project_id = fields.Many2one(
      "project.project",
      string="Pipe Do Financeiro"
    )
    order_id = fields.Char(string="Pedido de Venda")
    partner_id = fields.Many2one(related="attendance_id.partner_id")
    
    # ------------------------------------------------------------
    # COMPUTES 
    # ------------------------------------------------------------

    @api.depends("attendance_id")
    def _compute_default_name(self):
        for record in self:
            record.name = record.attendance_id.name
         
    # ------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------

    @api.model
    def create(self, values):
      for record in self:
        if record.cost_type == "cash":
          acc_num = record.account_payment_info.account_number,
          acc_dig = record.account_payment_info.account_digit
          account = f"{acc_num}-{acc_dig}"
          payment_info = {            
            "Chave Pix":record.account_payment_info.pix_key,
            "Banco":record.account_payment_info.bank_code,
            "Agência":record.account_payment_info.agency,
            "Conta":account
          }
          description = f"-------Dados para Pagamento------\n \
            {str(payment_info)}\n \
            --------------------------------- \
            {record.description}"           
          task_vals = {
            "name": record.name,
            "project_id": record.project_id.id,
            "provider_id": record.attendance_id.partner_id.id,
            "cost": record.cost,
            "description": description
          }
        self.env["project.task"].create(task_vals)
      
      return super(KamiSmAttendanceCost, self).create(values)