# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class KamiSmAttendanceType(models.Model):
    _name = "kami_sm.attendance.type"
    _description = "Attendance Type Model for Kami Service Manager Module"
    _order = "name"

    name = fields.Char(string="Tipo", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)
    attendance_ids = fields.One2many(
        "kami_sm.attendance",
        "attendance_type_id",
        string="Atendimentos"
    )
    sequence = fields.Integer(default=1)    