# -*- coding: utf-8 -*-
from odoo import fields, models

class ResUsers(models.Model):    
    _inherit = 'res.users'

    partner_ids = fields.Many2many(
      comodel_name="res.partner",
      relation="partner_seller_table",
      column1="table_to_partner_col",
      column2="partner_to_table_col",
      string='Parceiros'
    )