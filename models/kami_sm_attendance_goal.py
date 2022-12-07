from odoo import fields, models

class KamiSmAttendanceGoal(models.Model):
    _name = "kami_sm.attendance.goal"
    _description = "Kami Model For Attendance Goal"

    name = fields.Char(
        "Nome"
    )
    description = fields.Text(
        "Descrição"
    )
    active = fields.Boolean(
    
    )
