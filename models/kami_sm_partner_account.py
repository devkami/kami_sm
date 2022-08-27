# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class KamiSmAttendanceCost(models.Model):
    _name = "kami_sm.partner.account"
    _description = "Partner Payment Information Model for Kami Service Manager Module"
    _order = "id"
    
    name = fields.Text(string="Título")
    partner_id = fields.Many2one("res.partner", string="Parceiro")
    description = fields.Text(string="Descrição")
    active = fields.Boolean(default=True)    
    pix_key = fields.Char(string="Chave PIX")
    bank_code = fields.Char(string="Código do Banco")
    agency = fields.Char(string="Agência")
    account_number = fields.Char(string="Conta Corrente/Poupança")
    account_digit = fields.Char(string="Dígito")