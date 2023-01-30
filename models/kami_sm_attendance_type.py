# -*- coding: utf-8 -*-
from odoo import fields, models

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
    sequence = fields.Integer(default=1)
    partner_ids = fields.Many2many(
      "res.partner",
      string='Parceiros'
    )
    theme_ids = fields.Many2many(
      "kami_sm.attendance.theme",
      string='Temas'
    )
    generate_tasks = fields.Boolean(
      default=False,
      string='Gera Tarefas?'
    )
    project_id = fields.Many2one(
      'project.project',
      string='Projeto'
    )
