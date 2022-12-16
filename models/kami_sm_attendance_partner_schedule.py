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
    partner_ids = fields.Many2many(
      "res.partner",
      string='Parceiros'
    )
    start_time = fields.Selection([
      ('0', '00:00'),
      ('1', '01:00'),
      ('2', '02:00'),
      ('3', '03:00'),
      ('4', '04:00'),
      ('5', '05:00'),
      ('6', '06:00'),
      ('7', '07:00'),
      ('8', '08:00'),
      ('9', '09:00'),
      ('10', '10:00'),
      ('11', '11:00'),
      ('12', '12:00'),
      ('13', '13:00'),
      ('14', '14:00'),
      ('15', '15:00'),
      ('16', '16:00'),
      ('17', '17:00'),
      ('18', '18:00'),
      ('19', '19:00'),
      ('20', '20:00'),
      ('21', '21:00'),
      ('22', '22:00'),
      ('23', '23:00')],
      default=8,
      string="Hora Inicial",
      required=True,
    )
    duration = fields.Float(
        string="Duração",
        required=True
    )
    end_time = fields.Float(
      string="Término",
      compute="_compute_end_time"
    )

    def float_to_time(self, field):
      return '{0:02.0f}:{1:02.0f}'.format(*divmod(self[field] * 60, 60))

    def get_value_from(self, field):
      return dict(self._fields[field].selection).get(self[field])

    @api.depends('start_time','duration')
    def _compute_end_time(self):
      for schedule in self:
        schedule.end_time = float(schedule.start_time) + schedule.duration

    @api.depends('start_time', 'end_time')
    def _compute_default_name(self):
      for partner_schedule in self:
        partner_schedule.name = f"{partner_schedule.get_value_from('start_time')} - {partner_schedule.float_to_time('end_time')}"
