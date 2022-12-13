from odoo import fields, models, api


class KamiSmAttendancePartnerSchedule(models.Model):
    _name = "kami_sm.attendance.partner.schedule"
    _description = "Kami Model From Attendance Parter Schedule"

    partner_id = fields.Many2many("res.partner", string= "Parceiro")
    start_time = fields.z(string="Hora Inicial")
    duration = fields.Float(string="Duração")
    end_time = fields.Float(string="Término", compute="_compute_end_time")

    @api.depends('start_time','duration')
    def _compute_end_time(self):
        for schedule in self:
            schedule.end_time = schedule.start_time + schedule.duration

