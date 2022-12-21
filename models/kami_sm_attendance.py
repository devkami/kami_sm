# -*- coding: utf-8 -*-
import ast
from email.policy import default
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from pytz import timezone, utc

class KamiInEducationAttendance(models.Model):
    _name = 'kami_sm.attendance'
    _description = 'Attendance Model for Kami In Education Module'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'rating.mixin']

    name = fields.Char(
        string='Título',
        required=True,
        compute='_compute_default_name',
        readonly=True
    )
    active = fields.Boolean(default=True)
    state = fields.Selection(
        [('new', 'Aguardando Aprovação'),
        ('approved', 'Aprovado'),
        ('done', 'Encerrado'),
        ('waiting', 'Aguardando Cancelamento'),
        ('canceled', 'Cancelado')],
        string='Status',
        default='new',
        tracking=True
    )
    seller_id =  fields.Many2one(
        'res.users',
        string='Vendedor',
        default=lambda self: self.env.user
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        copy=False,
        default=None
    )
    type_id = fields.Many2one(
        'kami_sm.attendance.type',
        string='Tipo'
    )
    theme_ids = fields.Many2many(
        'kami_sm.attendance.theme',
        string='Tema',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Parceiro',
        copy=False,
        default=None
    )
    expected_audience = fields.Integer(string='Público Esperado')
    start_date = fields.Date(
        string='Ínicio',
        copy=False,
        default= lambda self: self._get_default_start_date()
    )
    cost_ids = fields.One2many(
        'kami_sm.attendance.cost',
        'attendance_id',
        string='Custos',
    )
    total_cost = fields.Monetary(
      string='Custo Total',
      currency_field='currency_id',
      compute='_compute_attendance_total_cost'
    )
    currency_id = fields.Many2one(
      'res.currency',
      string='Currency'
    )
    description = fields.Text(string='Observações Relevantes')
    cancellation_reason = fields.Text(string='Motivo do Cancelamento')
    has_product_cost = fields.Boolean(
      'Pagamento Com Produtos',
      default=False
    )
    feedback = fields.Text(string='Comentário')
    rating = fields.Selection(
        [('0', 'Insatisfeito'),
        ('1', 'Insatisfeito'),
        ('2', 'Pouco Satisfeito'),
        ('3', 'Satisfeito'),
        ('4', 'Muito Satisfeito'),
        ('5', 'Extremamente Satisfeito')],
        string='Nível de Satisfação',
        default='1'
    )
    is_expired = fields.Boolean(compute='_compute_is_expired')
    address = fields.Text(string='Endereço', compute='_compute_address')
    has_others_clients = fields.Boolean(string='Atendeu outros Clientes?')
    served_audience = fields.Integer(string='Público Atendido')
    client_ids = fields.One2many(
        'kami_sm.attendance.client',
        'attendance_id',
        string='Outros Clientes',
    )
    backoffice_user_id = fields.Many2one(
        'res.users',
        string='Responsavel BackOffice',
        copy=False,
        default=None
    )
    has_tasting = fields.Boolean(string="Tem degustação")
    _is_beauty_day = fields.Boolean(compute = "_compute_is_beauty_day")
    total_event_attendees = fields.Integer(string='Porte do evento')
    goal_ids = fields.Many2many(
        'kami_sm.attendance.goal',
        string='Objetivos'
    )
    available_space = fields.Boolean(string="Cliente possui estrutura de no mínimo 1,20cm de largura?")

    _is_facade = fields.Boolean(compute="_compute_is_facade")
    installation_images = fields.Image(string='Fotos da instalação')
    images_position = fields.Selection(
        string='Posição das imagens',
        selection=
        [('separeted', 'Separadas'),
        ('syde-by-syde', 'Lado a Lado')]
    )
    facade_width = fields.Float(string='Largura da Arte')
    facade_height= fields.Float(string='Altura da Arte')
    facade_has_ad=fields.Boolean(string='Solicitação de anúncio?')
    facade_ad_type = fields.Selection(
        string='Tipo de anúncio',
        selection=[
            ('truss_color','TRUSS Color'),
            ('high_liss','High Liss'),
            ('k_recovery','K Recovery'),
            ('work_station Miracle','Work Station Miracle'),
            ('fast_repais','Fast Repais'),
            ('shock_repais','Shock Repais'),
            ('8_xpowder','8 XPowder'),
            ('therapy','Therapy'),
            ('loucasportruss','LoucasporTRUSS'),
            ('trussman','TRUSSMan'),
            ('infusion_night_spa','Infusion & Night Spa'),
            ('blond','Blond'),
            ('net_mask','Net Mask'),
            ('perfect_blond','Perfect Blond'),
            ('shampoo_cond_blond','Shampoo/Cond.Blond'),
            ('linha_de_shampoos_con','Linha de Shampoos/Con.'),
            ('others', 'Outros'),
        ]
    )
    magazine_types = fields.Selection(
        selection=[
            ('professional', 'Profissional'),
            ('consumer', 'Consumidor'),
        ],
        string='Tipos de Revista',
    )
    partner_schedule_id = fields.Many2one(
        "kami_sm.attendance.partner.schedule",
        string="Horário de atendimento",
        copy=False,
        default=None
    )
    _has_partner = fields.Boolean(compute="_compute_partner_schedule")
    magazine_height = fields.Float(string='Altura da Revista (cm)')
    magazine_width = fields.Float(string='Largura da revista(cm)')
    magazine_format = fields.Selection(
        selection=[
            ('pdf', 'PDF'),
            ('jpg', 'JPG')
        ],
        string='Formato da revista'
    )
    has_cutting_edge = fields.Boolean(string='Sangria')
    cutting_edge_size = fields.Float(string='Sangria (mm)')
    has_safe_margin = fields.Boolean(string='Margem de Segurança ?')
    safe_margin_size = fields.Float(string='Margem de Segurança(mm)')
    has_digital_invite = fields.Boolean(string='Convite Digital?')
    invite_details = fields.Text(string='Detalhes do Convite')
    invite_image_logo = fields.Image(string="Logo")
    _is_degustation = fields.Boolean(compute="_compute_is_degustation")

    # ------------------------------------------------------------
    # PRIVATE UTILS
    # ------------------------------------------------------------

    def _get_default_start_date(self):
        return fields.Date.today() + timedelta(days=4)

    def _create_attendance_event(self, attendance):
        start_time = fields.datetime.strptime(
            attendance.partner_schedule_id.get_value_from('start_time'), '%H:%M'
        ).time()
        event_vals = {
            'name': f"{attendance.client_id.name} - {attendance.type_id.name}",
            'start_date': fields.datetime.combine(attendance.start_date, start_time),
            'duration': attendance.partner_schedule_id.duration,
            'user_id': attendance.seller_id.id,
            'partner_ids': [
                (4, attendance.partner_id.id),
            ],
            'location': attendance.address,
            'description': attendance.description
        }
        self.env['calendar.event'].create(event_vals)

    def _create_attendance_invoice(self, attendance):
        for attendance_cost in attendance.cost_ids:
            if attendance_cost.cost_type == 'cash':
                journal = self.env['account.move']\
                .with_context(default_move_type='in_invoice')\
                ._get_default_journal()

                default_partner_account = attendance.partner_id.bank_ids.\
                search([('active', '=', True)], limit=1)

                invoice_vals = {
                    'name':f'ATENDIMENTO/EDUCAÇÃO/{attendance.id}',
                    'partner_id': attendance.partner_id,
                    'create_uid': self.env.user.id,
                    'partner_bank_id': default_partner_account,
                    'invoice_date': fields.Datetime.today(),
                    'invoice_date_due': fields.Datetime.today() \
                        + timedelta(days=3),
                    'move_type': 'in_invoice',
                    'journal_id': journal.id,
                    'narration': f"Data de Execução: {attendance.start_date.strftime('%d/%m/%Y')}",
                    'invoice_line_ids': [
                        ((0, 0,{
                            'name':attendance_cost.name,
                            'quantity': 1,
                            'price_unit': attendance_cost.cost,
                        })),
                    ],
                }
                account_move = self.env['account.move'].create(invoice_vals)
                attendance_cost.invoice_id = account_move.id

    def _create_attendance_rating(self, attendance):
        rating_vals = {}

        if(attendance.partner_id == self.env.user.partner_id):
            rating_vals['res_model_id'] = self.env.ref('kami_sm.model_kami_sm_attendance').id
            rating_vals['res_id'] = self.id
            rating_vals['rated_partner_id'] = attendance.seller_id.partner_id.id
            rating_vals['partner_id'] = attendance.partner_id.id
            rating_vals['rating'] = attendance.rating
            rating_vals['feedback'] = attendance.feedback
            rating_vals['display_name'] = 'Educador'

        elif(attendance.seller_id == self.env.user):
            rating_vals['res_model_id'] = self.env.ref('kami_sm.model_kami_sm_attendance').id
            rating_vals['res_id'] = self.id
            rating_vals['rated_partner_id'] = attendance.partner_id.id
            rating_vals['partner_id'] = attendance.seller_id.partner_id.id
            rating_vals['rating'] = attendance.rating
            rating_vals['feedback'] = attendance.feedback
            rating_vals['Vendedor'] = 'Vendedor'

        self.env['rating.rating'].create(rating_vals)

    def _create_attendance_client(self, attendance):
        client_vals = {}
        client_vals['attendance_id'] = attendance.id
        client_vals['partner_id'] = attendance.client_id
        client_vals['served_audience'] = attendance.served_audience

        self.env['rating.rating'].create(client_vals)

    @api.depends('type_id')
    def _compute_is_beauty_day(self):
        for attendance in self:
            attendance._is_beauty_day = attendance.type_id.name != None \
            and 'Beleza' in str(attendance.type_id.name)

    @api.depends('type_id')
    def _compute_is_facade(self):
        for attendance in self:
            attendance._is_facade = attendance.type_id.name != None \
            and 'Fachada' in str(attendance.type_id.name)

    @api.depends('type_id')
    def _compute_is_degustation(self):
        for attendance in self:
            attendance._is_degustation = attendance.type_id.name != None \
            and 'Degustação' in str(attendance.type_id.name)

    # ------------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------------

    @api.constrains('start_date')
    def _check_attendance_start(self):
        for attendance in self:
            minimum_antecedence = fields.Date.today() + timedelta(days=4)
            if(attendance.start_date < minimum_antecedence):
                raise ValidationError(' A antecedência mínima para o agendamento de um evento são 4 dias!')

    # ------------------------------------------------------------
    # COMPUTES
    # ------------------------------------------------------------
    @api.depends('partner_id')
    def _compute_partner_schedule(self):
        for attendance in self:
            if attendance.partner_id:
                attendance._has_partner = True
            else:
                attendance._has_partner = False

    @api.depends('cost_ids')
    def _compute_attendance_total_cost(self):
        for attendance in self:
            attendance.total_cost = sum(attendance.cost_ids.mapped('cost'))

    @api.depends('type_id', 'theme_ids', 'partner_id')
    def _compute_default_name(self):
      for attendance in self:
        attendance.name = f'{attendance.type_id.name}-{attendance.theme_ids.name}'

    @api.depends('state', 'start_date')
    def _compute_is_expired(self):
        for attendance in self:
            attendance.is_expired = attendance.state == 'approved'\
            and attendance.start_date < fields.Date.today()

    @api.depends('client_id')
    def _compute_address(self):
        for attendance in self:
            attendance.address = f'{attendance.client_id.street} - {attendance.client_id.street2}, {attendance.client_id.city}, {attendance.client_id.state_id.name}, CEP: {attendance.client_id.zip}'

    # ------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------

    def action_approve_attendance(self):
        for attendance in self:
            if attendance.state != 'new':
                raise UserError('Somente Novos Atendimentos Podem Ser Aprovados!')
            else:
                attendance.state = 'approved'
                self._create_attendance_invoice(attendance)
                self._create_attendance_event(attendance)

    def action_request_cancel(self):
        for attendance in self:
            if attendance.state not in ['new', 'approved']:
                raise UserError('Somente Atendimentos Novos ou Aprovados Podem ser Cancelados!')
            else:
                attendance.state = 'waiting'

    def action_open_request_cancel(self):
        return {
            'res_model': 'kami_sm.attendance',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('kami_sm.kami_sm_attendance_view_popup_form').id,
            'target': 'new'
        }

    def action_cancel_popup_attendance(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel_attendance(self):
        for attendance in self:
            if attendance.state != 'waiting':
                raise UserError('Somente Atendimentos Aguardando Cancelamento Podem ser Cancelados!')
            else:
                attendance.state = 'canceled'

    def action_rating_attendance(self):
        for attendance in self:
            if attendance.state not in ['approved', 'done']:
                raise UserError('Somente Atendimentos Aprovados Podem ser Avaliados/Encerrados!')
            else:
                attendance.rating = '0'
                attendance.feedback = ''
                return {
                    'res_model': 'kami_sm.attendance',
                    'res_id': self.id,
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': self.env.ref('kami_sm.kami_sm_attendance_rating_view_popup_form').id,
                    'target': 'new'
                }

    def action_get_ratings(self):
        action = self.env['ir.actions.act_window']._for_xml_id('rating.rating_rating_view')
        return dict(
            action,
            domain=[('res_id', 'in', self.ids), ('res_model', '=', 'kami_sm.attendance')],
        )

    def action_rating_or_finish(self):
        for attendance in self:
            if(attendance.partner_id == self.env.user.partner_id):
                #envia email de avaliação para o cliente
                rating_template = self.env.ref('kami_sm.mail_template_attendance_rating')
                attendance.rating_send_request(rating_template, force_send=True)
                #registra avaliação do educador
                self._create_attendance_rating(attendance)
                attendance.state = 'done'
            elif(attendance.seller_id == self.env.user):
                #registra avaliação do vendedor
                self._create_attendance_rating(attendance)

    # ------------------------------------------------------------
    # PARTNERS DOMAIN FILTERS
    # ------------------------------------------------------------

    @api.onchange('type_id', 'theme_ids', 'start_date')
    def _onchange_attendance_theme_start_id(self):
        for attendance in self:
            partner_types = attendance.type_id.partner_ids.mapped('id')
            partner_themes = self.env['kami_sm.attendance.theme'].search([
                ('type_ids', '=', attendance.type_id.id)]).partner_ids.mapped('id')
            partner_attendances = self.env['kami_sm.attendance'].search([
                ('start_date', '=', attendance.start_date)
            ]).mapped('partner_id.id')
            partner_meetings = self.env['calendar.event'].search([
                '|', '&',
                ('start_date', '=', attendance.start_date),
                ('allday', '=', True),
                ('start_date', '=', attendance.start_date)
            ]).partner_ids.mapped('id')
            return {'domain':
                {'partner_id':[
                    ('id', 'in', partner_types),
                    ('id', 'in', partner_themes),
                    ('id', 'not in', partner_meetings),
                    ('id', 'not in', partner_attendances)
                ]}}

    @api.onchange('type_id')
    def _onchange_attendance_type_id(self):
        for attendance in self:
            return {'domain':
                {'theme_ids': [
                    ('id', 'in', attendance.type_id.theme_ids.mapped('id'))
                ]}}

    # ------------------------------------------------------------
    # RATING MIXIN
    # ------------------------------------------------------------

    def rating_get_partner_id(self):
        if self.client_id:
            return self.client_id
        return self.env['res.partner']

    def rating_get_rated_partner_id(self):
        if self.partner_id.user_id:
            return self.partner_id.user_id
        return self.env['res.users']

    # ------------------------------------------------------------
    # ONCHANGES
    # ------------------------------------------------------------

    @api.onchange('cost_ids')
    def _onchange_cost_ids(self):
        for attendance in self:
            for attendance_cost in attendance.cost_ids:
                if not attendance_cost.invoice_id:
                    self._create_attendance_invoice(attendance)
