# -*- coding: utf-8 -*-
from odoo import fields, models, api, Command
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import timedelta


class KamiInEducationAttendance(models.Model):
    _name = "kami_sm.attendance"
    _description = "Attendance Model for Kami In Education Module"
    _order = "id desc"

    name = fields.Char(
        string="Title", 
        required=True,
        compute="_compute_default_name",
        readonly=True
    )
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
    attendance_start = fields.Datetime(
        string="Ínicio",
        copy=False,
        default=lambda self: fields.Datetime.today() + timedelta(days=4)
    )
    attendance_stop = fields.Datetime(
        string="Término",
        copy=False,
        default=lambda self: fields.Datetime.today() + timedelta(days=4, hours=4)
    )
    duration = fields.Float(
        string="Duração",
        compute="_compute_duration",
        readonly=True
    )
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


    # ------------------------------------------------------------
    # PRIVATE UTILS
    # ------------------------------------------------------------

    def _get_duration(self, start, stop):
        """ Get the duration value between the 2 given dates. """
        if not start or not stop:
            return 0
        duration = (stop - start).total_seconds() / 3600
        return round(duration, 2)
    
    # ------------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------------

    @api.constrains("attendance_start")
    def _check_attendance_start(self):
        for record in self:
            minimum_antecedence = fields.Datetime.today() + timedelta(days=4)
            if(record.attendance_start < minimum_antecedence):
                raise ValidationError(" A antecedência mínima para o agendamento de um evento são 4 dias!")
            meetings_start = record.partner_id.meeting_ids.mapped('start')
            meetings_stop = record.partner_id.meeting_ids.mapped('stop')
            for meeting_start, meeting_stop in zip(meetings_start, meetings_stop):
                if (meeting_start == record.attendance_start) or (meeting_stop == record.attendance_stop):
                    raise ValidationError(" O parceiro já possui um evento na mesma data!")

    # ------------------------------------------------------------
    # COMPUTES
    # ------------------------------------------------------------

    @api.depends("attendance_cost", "extra_cost")
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.attendance_cost + record.extra_cost

    @api.depends("attendance_type_id", "attendance_theme_id", "partner_id")
    def _compute_default_name(self):
        for record in self:
            record.name = f"{record.attendance_type_id.name} - \
              {record.attendance_theme_id.name} - \
              {record.partner_id.name}"

    @api.depends("attendance_stop", "attendance_start")
    def _compute_duration(self):
        for record in self:
            record.duration = self._get_duration(record.attendance_start, record.attendance_stop)
    
    # ------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------

    def action_approve_attendance(self):
        for record in self:
            if record.state != "new":
                raise UserError("Somente Atendimentos Novos Podem Ser Aprovados!")
            else:
                record.state = "approved"                
                event_vals = {
                    "name": record.name,
                    "start": record.attendance_start,
                    "stop": record.attendance_stop,                    
                    "user_id": record.seller_id.id,
                    "partner_ids": [
                        (4, record.partner_id.id),
                        (4, record.client_id.id),
                    ],                    
                    "location": record.client_id.contact_address,
                    "description": record.description
                }            
                self.env["calendar.event"].create(event_vals)
                

    def action_request_cancel(self):
        for record in self:
            if record.state not in ["new", "approved"]:
                raise UserError("Somente Atendimentos Novos ou Aprovados Podem ser Cancelados!")
            else:
                record.state = "waiting"
    
    def action_open_request_cancel(self):
        return {
            "res_model": "kami_sm.attendance",
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref("kami_sm.kami_sm_attendance_view_popup_form").id,
            "target": "new"
        }
    
    def action_cancel_popup_attendance(self):
        return {"type": "ir.actions.act_window_close"}

    def action_cancel_attendance(self):
        for record in self:
            if record.state != "waiting":
                raise UserError("Somente Atendimentos Aguardando Cancelamento Podem ser Cancelados!")
            else:
                record.state = "canceled" 
                

    # ------------------------------------------------------------
    # DOMAINS FILTER
    # ------------------------------------------------------------

    @api.onchange('attendance_type_id')
    def _onchange_attendance_type_id(self):
        for record in self:
            return {'domain':
                {'partner_id':
                [('id', 'in', record.attendance_type_id.partner_ids.mapped('id'))]}}

    @api.onchange('attendance_theme_id')
    def _onchange_attendance_theme_id(self):
        for record in self:
            return {'domain':
                {'partner_id':
                [('id', 'in', record.attendance_theme_id.partner_ids.mapped('id'))]}}

    
    