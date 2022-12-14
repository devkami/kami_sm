from odoo import fields, models, api


class KamiSmAttendancePartnerSchedule(models.Model):
    _name = "kami_sm.attendance.partner.schedule"
    _description = "Kami Model From Attendance Parter Schedule"

    name = fields.Text(
      string='Título',
      required=True,
      compute='_compute_default_name',
      readonly=True
    )
    partner_id = fields.Many2many(
      "res.partner",
      string="Parceiro"
    )
    start_time = fields.Float(string="Hora Inicial")
    duration = fields.Float(string="Duração")
    end_time = fields.Float(
      string="Término",
      compute="_compute_end_time"
    )

    def _float_to_time(self, number):
        return '{0:02.0f}:{1:02.0f}'.format(*divmod(number * 60, 60))

    @api.depends('start_time','duration')
    def _compute_end_time(self):
      for schedule in self:
        schedule.end_time = schedule.start_time + schedule.duration

    @api.depends('start_time', 'end_time')
    def _compute_default_name(self):
      for partner_schedule in self:
        partner_schedule.name = f"{self._float_to_time(partner_schedule.start_time)} - {self._float_to_time(partner_schedule.end_time)}"


