# -*- coding: utf-8 -*-
import ast
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
    rating = fields.Float(string='Nível de Satisfação')


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
            'name': attendance.name,
            'start': attendance.start_date,
            'stop': attendance.stop_date,
            'user_id': attendance.seller_id.id,
            'partner_ids': [
                (4, attendance.partner_id.id),                        
            ],                    
            'location': attendance.client_id.contact_address,
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
                    'partner_id': attendance.partner_id,
                    'partner_bank_id': default_partner_account,
                    'invoice_date': fields.Datetime.today(),
                    'invoice_date_due': fields.Datetime.today() \
                        + timedelta(days=1),
                    'move_type': 'in_invoice',
                    'journal_id': journal.id,
                    'invoice_line_ids': [
                        ((0, 0,{
                            'name':attendance_cost.name,
                            'quantity': 1,
                            'price_unit': attendance_cost.cost,
                        })),
                    ],
                }
                self.env['account.move'].create(invoice_vals)
    
    def _create_attendance_rating(self, attendance):       
        
        rating_vals = {            
            'res_model_id': self.env.ref('kami_sm.model_kami_sm_attendance').id,
            'res_id': self.id,
            'rated_partner_id': attendance.seller_id.partner_id.id,
            'partner_id': attendance.partner_id.id,            
            'rating': attendance.rating,
            'feedback': attendance.feedback
        }        
        self.env['rating.rating'].create(rating_vals)
    
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
            attendance.name = f'{attendance.type_id.name}-\
            {attendance.theme_id.name}'    
    
    @api.depends('start_date')
    def _compute_stop_date(self):
        for attendance in self:
            attendance.stop_date = attendance.start_date + timedelta(hours=8)
    # ------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------

    def action_approve_attendance(self):
        for attendance in self:
            if attendance.state != 'new':
                raise UserError('Somente Atendimentos Novos Podem Ser Aprovados!')
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

    def action_finish_attendance(self):
        for attendance in self:   
            if attendance.state != 'approved':
                raise UserError('Somente Atendimentos Aprovados Podem ser Encerrados!')
            else:                            
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

    def action_rating_and_finish(self):
        for attendance in self:
            #envia email de avaliação para o cliente
            rating_template = self.env.ref('kami_sm.mail_template_attendance_rating')            
            attendance.rating_send_request(rating_template, force_send=True)
            #registra avaliação do educador
            self._create_attendance_rating(attendance)
            attendance.state = 'done'


        
    # ------------------------------------------------------------
    # PARTNERS DOMAIN FILTERS
    # ------------------------------------------------------------

    @api.onchange('type_id', 'theme_id', 'start_date')
    def _onchange_attendance_type_theme_start_id(self):
        for attendance in self:
            partner_types = attendance.type_id.partner_ids.mapped('id')
            partner_themes = attendance.theme_id.partner_ids.mapped('id')
            meetings = self.env['kami_sm.attendance'].search(
                [('start_date', '=', attendance.start_date)])            
            busy_partners = meetings.mapped('partner_id.id')
            
            return {'domain':
                {'partner_id':
                ['&', '&',
                    ('id', 'in', partner_types),
                    ('id', 'in', partner_themes),                    
                    ('id', 'not in', busy_partners),
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