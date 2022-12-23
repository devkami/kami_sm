# -*- coding: utf-8 -*-
from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    attendance_type_ids = fields.Many2many(
      "kami_sm.attendance.type",
      string="Tipo de Atendimento"
    )
    attendance_theme_ids = fields.Many2many(
      "kami_sm.attendance.theme",
      string="Tema do Atendimento"
    )
    seller_ids =  fields.Many2many(
      "res.users",
      string="Vendedores",
    )
    attendance_schedule_ids = fields.Many2many(
      "kami_sm.attendance.partner.schedule",
      string="Horários de atendimento"
    )
    is_salon = fields.Boolean(string="É Salão de Beleza?")
    cod_uno = fields.Char(string="Código do cliente")
    