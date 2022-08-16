# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class KamiSmAttendanceTheme(models.Model):
    _name = "kami_sm.attendance.theme"
    _description = "Attendance Theme Model for Kami Service Manager Module"
    _order = "name"

    name = fields.Char(string="Tema", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)
    attendance_ids = fields.One2many(
        "kami_sm.attendance",
        "attendance_theme_id",
        string="Atendimentos"
    ) 
    sequence = fields.Integer(default=1)    
