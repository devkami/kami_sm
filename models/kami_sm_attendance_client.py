# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class KamiSmAttendanceClient(models.Model):
    _name = "kami_sm.attendance.client"
    _description = "Attendance Client Model for Kami Service Manager Module"
    _order = "attendance_id"

    attendance_id = fields.Many2one(
      'kami_sm.attendance',
      string='Atendimento',      
    )
    partner_id = fields.Many2one(
      'res.partner',
      string='Cliente',
      copy=False,
      default=None
    )
    served_audience = fields.Integer(string='Público Atendido')
