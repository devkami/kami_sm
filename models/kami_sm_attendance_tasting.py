from odoo import fields, models, api
from odoo.exceptions import UserError

class KamiSmAttendanceTasting(models.Model):
    _name = "kami_sm.attendance.tasting"
    _description = "Kami Model for Attendance Tasting"
    
    name = fields.Char(string="Nome")
    description = fields.Text(string="Descrição")
    active = fields.Boolean(default=True)

    color = fields.Integer("Color Index")
    
    

