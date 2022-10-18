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
    theme_id = fields.Many2one(
        'kami_sm.attendance.theme',
        string='Tema'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Parceiro',
        copy=False,
        default=None
    )
    expected_audience = fields.Integer(string='Público Esperado')    
    start_date = fields.Datetime(
        string='Ínicio',
        copy=False,
        default= lambda self: self._get_default_start_date()
    )
    stop_date = fields.Datetime(
        string='Término',
        copy=False,
        compute='_compute_stop_date'
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

    # ------------------------------------------------------------
    # PRIVATE UTILS
    # ------------------------------------------------------------

    def _get_user_timezone(self):
        return timezone(self.env.user.partner_id.tz)     
        
    def _convert_to_user_timezone(self, date_time):
        return fields.Datetime.to_string(timezone(
            self.env.user.partner_id.tz).localize(fields.Datetime.from_string(
            date_time), is_dst=None).astimezone(utc)
        )
 
    def _get_default_start_date(self):
        return self._convert_to_user_timezone( fields.Datetime.today().replace(
           hour=10, minute=00, second=00) + timedelta(days=4)
        )

    def _create_attendance_event(self, attendance):
        event_vals = {
            'name': f"{attendance.client_id.name} - {attendance.theme_id.name}",
            'start': attendance.start_date,
            'stop': attendance.stop_date,
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
    
    # ------------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------------

    @api.constrains('start_date')
    def _check_attendance_start(self):
        for attendance in self:
            minimum_antecedence = fields.Datetime.today() + timedelta(days=4)
            if(attendance.start_date < minimum_antecedence):
                raise ValidationError(' A antecedência mínima para o agendamento de um evento são 4 dias!')        

    # ------------------------------------------------------------
    # COMPUTES
    # ------------------------------------------------------------

    @api.depends('cost_ids')
    def _compute_attendance_total_cost(self):
        for attendance in self:
            attendance.total_cost = sum(attendance.cost_ids.mapped('cost'))

    @api.depends('type_id', 'theme_id', 'partner_id')
    def _compute_default_name(self):
      for attendance in self:
        attendance.name = f'{attendance.type_id.name}-{attendance.theme_id.name}'    
    
    @api.depends('start_date')
    def _compute_stop_date(self):
        for attendance in self:
            attendance.stop_date = attendance.start_date + timedelta(hours=8)
    
    def _compute_is_expired(self):
        for attendance in self:
            attendance.is_expired = attendance.state == 'approved'\
            and attendance.start_date < fields.Datetime.now()
        
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

    @api.onchange('type_id', 'theme_id', 'start_date')
    def _onchange_attendance_type_theme_start_id(self):
        for attendance in self:
            partner_attendances = []
            partner_types = attendance.type_id.partner_ids.mapped('id')
            partner_themes = attendance.theme_id.partner_ids.mapped('id')
            seller_partners = self.env.user.partner_ids.mapped('id')
            attendances = self.env['kami_sm.attendance'].search([                
                ('start_date', '=', attendance.start_date)                
            ])
            for att in attendances:
                if(att.partner_id.id):
                    partner_attendances.append(att.partner_id.id)

            partner_meetings = self.env['calendar.event'].search([
                '|', '&',
                ('start_date', '=', attendance.start_date),
                ('allday', '=', True),
                ('start_date', '=', attendance.start_date)
            ]).partner_ids.mapped('id')
          
            return {'domain':
                {'partner_id':
                [   ('id', 'in', partner_types),
                    ('id', 'in', partner_themes),
                    ('id', 'in', seller_partners),
                    ('id', 'not in', partner_meetings),
                    ('id', 'not in', partner_attendances)
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