# -*- coding: utf-8 -*-
{
  'name': 'Kami_sm',
  'category': 'Services/Kami_sm',
  'summary': 'Kamico Service Manager',
  'version': '1.0',
  'license': 'GPL-3 or any later version',
  'depends': ['base', 'calendar', 'account', 'mail', 'rating',],
  'data': [
    'security/security.xml',
    'security/ir.model.access.csv',
    'views/res_partner_views.xml',
    'views/res_users_views.xml',
    'views/rating_template.xml',
    'views/rating_views.xml',
    'views/kami_sm_attendance_cost_views.xml',
    'views/kami_sm_attendance_type_views.xml', 
    'views/kami_sm_attendance_theme_views.xml',
    'views/kami_sm_attendance_views.xml',
    'views/kami_sm_menus.xml',
    'data/calendar_data.xml',   
    'data/user_data.xml',
    'data/mail_template_data.xml'
  ],
   
  'installable': True,
  'auto_install': False,
  'application': True,
  'author': 'Maicon de Menezes', 
}