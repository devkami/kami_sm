# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class KamiSmAttendanceType(models.Model):
    _name = 'kami_sm.attendance.type'
    _description = 'Attendance Type Model for Kami Service Manager Module'
    _order = 'name'

    name = fields.Char(string='Tipo', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    attendance_ids = fields.One2many(
        'kami_sm.attendance',
        'type_id',
        string='Atendimentos'
    )
    sequence = fields.Integer(
      default=1
    )
    partner_ids = fields.Many2many(
      comodel_name="res.partner",
      relation="partner_attendance_type_table",
      column1="table_to_partner_col",
      column2="partner_to_table_col",
      string='Parceiros'
    )
    theme_ids = fields.Many2many(
      comodel_name="kami_sm.attendance.theme",
      relation="type_to_theme_table",
      column1="type_to_theme_col",
      column2="theme_to_type_col",
      string='Temas'
    )
