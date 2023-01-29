# -*- coding: utf-8 -*-
import ast
from email.policy import default
from odoo import fields, models, api, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from pytz import timezone, utc
from . import connection


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
    facade_ad_type_id = fields.Many2one(
        'kami_sm.attendance.ad_type',
        string='Tipos de Anúncio'
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
    invite_image_logo_preview = fields.Image(
      string='Pré-Vizualizção',
      related='invite_image_logo',
      readonly=True
    )
    _is_degustation = fields.Boolean(compute="_compute_is_degustation")
    parent_id = fields.Many2one(
        'kami_sm.attendance',
        string='Atendimento Pai',
        index=True
    )
    child_ids = fields.One2many(
        'kami_sm.attendance',
        'parent_id',
        string="Dependências",
    )
    _has_subattendances = fields.Boolean(compute = "_compute_has_subattendances")
    _has_childs = fields.Boolean(compute = "_compute_has_childs")
    _is_child = fields.Boolean(default=False)
    _has_educator = fields.Boolean(compute = "_compute_has_educator")
    _is_childs_approved = fields.Boolean(compute = "_compute_is_childs_approved")

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
            if attendance_cost.cost_type == 'cash' and not attendance_cost.invoice_id:
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

    def _convert_attendance_to_dict(self, attendance_id):
        attendance_obj = self.env['kami_sm.attendance']
        return attendance_obj.search_read(
            [('id', '=', attendance_id)], limit=1)[0]

    def _create_sub_attendance(self, attendance, theme_id):
        sub_attendance = {}
        sub_attendance['backoffice_user_id'] = attendance.backoffice_user_id.id
        sub_attendance['client_id'] = attendance.client_id.id
        sub_attendance['currency_id'] = attendance.currency_id.id
        sub_attendance['parent_id'] = attendance.id         
        sub_attendance['has_tasting'] = attendance.has_tasting
        sub_attendance['seller_id'] = attendance.seller_id.id
        sub_attendance['type_id'] = attendance.type_id.id
        sub_attendance['theme_ids'] = [(6, 0, [theme_id])]        
        sub_attendance['start_date'] = attendance.start_date
        sub_attendance['_is_child'] = True
        return sub_attendance

    def _create_sub_attendances(self, attendance):
        for theme_id in attendance.theme_ids:
            sub_attendance = self._create_sub_attendance(attendance, theme_id.id)
            self.env['kami_sm.attendance'].create(sub_attendance)

    def _get_state_value(self, state_key):
        return dict(self._fields['state'].selection).get(state_key)

    def _check_childs_state(self, attendance, state_key):        
        for child in attendance.child_ids:
            if child.state != state_key:
                return False
        return True
    
    def _create_attendance_task(self, attendance):
      task_name = attendance.name if not attendance.has_digital_invite else f'Convite Digital Para:{attendance.name}'
      
      project_id = attendance.type_id.project_id.id \
        if not attendance.has_digital_invite \
        else self.env.ref('kami_sm.digital_invite_project').id
      
      task_description = self._get_task_details(attendance)
      task_vals = {}
      task_vals['project_id'] = project_id
      task_vals['name'] = task_name
      task_vals['date_deadline'] = attendance.start_date
      task_vals['description'] = task_description
      
      self.env['project.task'].create(task_vals)
    
    def _get_image_url(self, model, obj_id, image_field):
      base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
      img_url = f"""{base_url}/web/image?model={model}&id={obj_id}&field={image_field}"""
      return img_url
    
    def _get_image_html_tag(self, model, obj_id, image_field):
      img_url = self._get_image_url(model, obj_id, image_field)
      return f"""\
        <div class="w-auto hover-text">
          <a target="_blank" rel="noopener noreferrer" href="{img_url}">
            <img
              class="w-100"
              title="Abrir a Imagem Original!"                            
              src="{img_url}"
            />            
          </a>
        <div>"""

    def _get_task_details(self, attendance):
      description = '<div class="w-auto"><ul>'      
      
      if attendance.has_digital_invite:
          description += (
            f"""<li>Detalhes do convite:\n{attendance.invite_details}</li>"""
            f"""<li>Logo do convite:\n{self._get_image_html_tag(
              'kami_sm.attendance', str(attendance.id), 'invite_image_logo')}
            </li>""")
      
      if attendance._is_facade:
          description += (
          f"""<li>Largura da Arte :{attendance.facade_width} - {attendance.name_get()}</li>"""
          f"""<li>Fotos da instalação :{self._get_image_html_tag(
              'kami_sm.attendance', str(attendance.id), 'installation_images')}</li>"""
          f"""<li>Largura da Arte :{attendance.facade_width}</li>"""
          f"""<li>Altura da Arte :{attendance.facade_height}</li>""")
          
          if attendance.facade_has_ad:
            description += f"""<li>Tipo de Anúncio :{attendance.facade_ad_type_id.name}</li>"""
          
          description += (
          f"""<li>Tipo de Revista :{attendance.magazine_types}</li>"""
          f"""<li>Altura da Revista (cm) :{attendance.magazine_height}</li>"""
          f"""<li>Largura da revista(cm) :{attendance.magazine_width}</li>"""
          f"""<li>Formato da revista :{attendance.magazine_format}</li>""")
          
          if attendance.has_cutting_edge:
            description += f"""<li>Sangria (mm) :{attendance.cutting_edge_size}</li>"""

          if attendance.has_safe_margin:
            description += f"""<li>Margem de Segurança(mm) :{attendance.safe_margin_size}</li>"""

      description += f"""<li>{str(attendance.description)}</li></ul></div>"""
      return description

    # ------------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------------

    @api.constrains('start_date')
    def _check_attendance_start(self):
        for attendance in self:
            minimum_antecedence = fields.Date.today() + timedelta(days=4)
            if(not attendance._has_subattendances and attendance.start_date < minimum_antecedence):
                raise ValidationError(' A antecedência mínima para o agendamento de um evento são 4 dias!')

    # ------------------------------------------------------------
    # COMPUTES
    # ------------------------------------------------------------
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
        attendance.name = f'{attendance.type_id.name}-{attendance.client_id.name}'

    @api.depends('state', 'start_date')
    def _compute_is_expired(self):
        for attendance in self:
            attendance.is_expired = attendance.state == 'approved'\
            and attendance.start_date < fields.Date.today()

    @api.depends('client_id')
    def _compute_address(self):
        for attendance in self:
            attendance.address = f'{attendance.client_id.street} - {attendance.client_id.street2}, {attendance.client_id.city}, {attendance.client_id.state_id.name}, CEP: {attendance.client_id.zip}'

    @api.depends('has_tasting', '_is_degustation', 'theme_ids')
    def _compute_has_subattendances(self):
        for attendance in self:
            attendance._has_subattendances = attendance.has_tasting or (attendance._is_degustation and len(attendance.theme_ids) > 1)

    @api.depends('child_ids')
    def _compute_has_childs(self):
        for attendance in self:
            attendance._has_childs = len(attendance.child_ids) > 0

    @api.depends('type_id')
    def _compute_has_educator(self):
        for attendance in self:
            attendance._has_educator = ('Treinamento' in attendance.type_id.name \
            or 'Dia da Beleza' in attendance.type_id.name)\
            if attendance.type_id else False
    
    @api.depends('child_ids')
    def _compute_is_childs_approved(self):
      for attendance in self:
            attendance._is_childs_approved = \
            self._check_childs_state(attendance, 'approved')

    # ------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------

    def action_approve_attendance(self):
        for attendance in self:
            if attendance.state != 'new':
                raise UserError('Somente Novos Atendimentos Podem Ser Aprovados!')
            if not attendance._is_childs_approved:
                raise UserError('Atendimentos Com Dependências Somente Serão Aprovados Se Todas As Dependências Forem Aprovadas!')
            
            attendance.state = 'approved'
            if attendance.type_id.generate_tasks or attendance.has_digital_invite:
              self._create_attendance_task(attendance)                
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
            if attendance._has_childs:
                self._check_childs_state(attendance, 'approved')

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

    def action_value_attendance(self):
        for attendance in self:
            value = connection.return_customer_spend_month(attendance.client_id.cod_uno)
            raise ValueError(value)

    def action_create_subattendances(self):
        for attendance in self:
            self._create_sub_attendances(attendance)

    # ------------------------------------------------------------
    # PARTNERS DOMAIN FILTERS
    # ------------------------------------------------------------

    @api.onchange('type_id', 'theme_ids', 'start_date')
    def _onchange_attendance_theme_start_id(self):                
        for attendance in self:
            domain = {}
            no_themes_type = attendance.type_id and (
              'Dia da Beleza' in attendance.type_id.name
              or 'Fachada' in attendance.type_id.name
            )
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

            if no_themes_type:
                domain = {'domain':
                {'partner_id':[
                    ('id', 'in', partner_types),
                    ('id', 'not in', partner_meetings),
                    ('id', 'not in', partner_attendances)
                ]}}
            else:
                domain = {'domain':
                {'partner_id':[
                    ('id', 'in', partner_types),
                    ('id', 'in', partner_themes),
                    ('id', 'not in', partner_meetings),
                    ('id', 'not in', partner_attendances)
                ]}}

            return domain

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
              if not attendance_cost.invoice_id and attendance.state == 'approved':
                    self._create_attendance_invoice(attendance)
