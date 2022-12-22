# -*- coding: utf-8 -*-
from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.users"

    is_backoffice = fields.Boolean(string="Backoffice")
