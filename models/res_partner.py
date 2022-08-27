# -*- coding: utf-8 -*-
from odoo import fields, models

class ResPartner(models.Model):    
    _inherit = "res.partner"

    attendance_type_ids = fields.Many2many(
      comodel_name="kami_sm.attendance.type",
      relation="partner_attendance_type_table",
      column1="partner_to_table_col",
      column2="table_to_partner_col",
      string="Tipo de Atendimento"
    )
    attendance_theme_ids = fields.Many2many(
      comodel_name="kami_sm.attendance.theme",
      relation="partner_attendance_theme_table",
      column1="partner_to_table_col",
      column2="table_to_partner_col",
      string="Tema do Atendimento"
    )
    seller_ids =  fields.Many2many(      
      comodel_name="res.users",
      relation="partner_seller_table",
      column1="partner_to_table_col",
      column2="table_to_partner_col",
      string="Vendedores",
    )
    account_info_ids = fields.One2many(
      "kami_sm.partner.account",
      "partner_id",
      string="Informações de Pagamento"
    )