# -*- coding: utf-8 -*-
from odoo import fields, models

class ResPartner(models.Model):    
    _inherit = 'res.partner'

    attendance_type_id = fields.Many2one(
      'kami_sm.attendance.type',
      string='Tipo de Atendimento'
    )
    attendance_theme_id = fields.Many2one(
      'kami_sm.attendance.theme',
      string='Tema do Atendimento'
    )
    seller_ids =  fields.Many2many(
      'res.users',
      string='Vendedores',
    )