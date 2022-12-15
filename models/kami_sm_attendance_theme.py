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
        "theme_ids",
        string="Atendimentos"
    )
    sequence = fields.Integer(
      default=1
    )
    partner_ids = fields.Many2many(
      comodel_name="res.partner",
      relation="partner_attendance_theme_table",
      column1="table_to_partner_col",
      column2="partner_to_table_col",
      string='Parceiros'
    )
    type_ids = fields.Many2many(
      comodel_name="kami_sm.attendance.type",
      relation="type_to_theme_table",
      column1="theme_to_type_col",
      column2="type_to_theme_col",
      string='Tipos'
    )

    color = fields.Integer("Color Index")
