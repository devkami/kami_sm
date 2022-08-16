# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class KamiInEducationAttendance(models.Model):
    _name = "kami_sm.attendance"
    _description = "Attendance Model for Kami In Education Module"
    _order = "id desc"

    active = fields.Boolean(default=True)
    state = fields.Selection(
        [("new", "Aguardando Aprovação"),        
        ("approved", "Aprovado"),
        ("done", "Encerrado"),
        ("waiting", "Aguardando Cancelamento"),
        ("canceled", "Cancelado")],
        string="Status",
        default="new"
    )
    seller_id =  fields.Many2one(
        "res.users", 
        string="Vendedor", 
        default=lambda self: self.env.user         
    )    
    client_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        copy=False,
        default=None
    )
    attendance_type_id = fields.Many2one(
        "kami_sm.attendance.type",
        string="Tipo"
    )
    attendance_theme_id = fields.Many2one(
        "kami_sm.attendance.theme",
        string="Tema"
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Parceiro",
        copy=False,
        default=None
    )
    expected_audience = fields.Integer(string="Público Esperado")
    activity_date = fields.Date(string="Data da Atividade", copy=False)
    attendance_cost = fields.Monetary(
        string="Custo do Atendimento", currency_field="currency_id")
    extra_cost = fields.Monetary(
        string="Custo Extra", currency_field="currency_id")
    total_cost = fields.Monetary(
        string="Custo Total",
        currency_field="currency_id",
        compute="_compute_total_cost"
    )
    currency_id = fields.Many2one("res.currency", string="Currency")    
    description = fields.Text(string="Observações Relevantes")
    cancellation_reason = fields.Text(string="Motivo do Cancelamento")

    @api.depends("attendance_cost", "extra_cost")
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.attendance_cost + record.extra_cost

    def action_approve_attendance(self):
        for record in self:
            if record.state != "new":
                raise UserError("Somente Atendimentos Novos Podem Ser Aprovados!")
            else:
                record.state = "approved"

    def action_request_cancel(self):
        for record in self:
            if record.state not in ["new", "approved"]:
                raise UserError("Somente Atendimentos Novos ou Aprovados Podem ser Cancelados!")
            else:
                record.state = "waiting"

    def action_cancel_attendance(self):
        for record in self:
            if record.state != "waiting":
                raise UserError("Somente Atendimentos Aguardando Cancelamento Podem ser Cancelados!")
            else:
                record.state = "canceled"
