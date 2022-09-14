# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools.misc import get_lang
from odoo.tools.translate import _
from odoo.addons.rating.controllers.main import Rating

import logging

_logger = logging.getLogger(__name__)

class FiveStarsRating(Rating):

    @http.route('/rating/<string:token>/<int:rate>', type='http', auth="public", website=True)
    def open_rating(self, token, rate, **kwargs):
        _logger.warning('/rating is deprecated, use /rate instead')
        assert rate in (1, 2, 3, 4, 5), "Incorrect rating"
        return self.action_open_rating(token, rate, **kwargs)

    @http.route(['/rating/<string:token>/submit_feedback'], type="http", auth="public", methods=['post'], website=True)
    def submit_rating(self, token, **kwargs):
        _logger.warning('/rating is deprecated, use /rate instead')
        rate = int(kwargs.get('rate'))
        assert rate in (1, 2, 3, 4, 5), "Incorrect rating"
        kwargs['rate'] = rate
        return self.action_submit_rating(token, **kwargs)

    @http.route('/rate/<string:token>/<int:rate>', type='http', auth="public", website=True)
    def action_open_rating(self, token, rate, **kwargs):
        assert rate in (1, 2, 3, 4, 5), "Incorrect rating"
        rating = request.env['rating.rating'].sudo().search([('access_token', '=', token)])
        if not rating:
            return request.not_found()
        rate_names = {
            1: _('Insatisfeito'),
            2: _('Pouco Satisfeito'),
            3: _('Satisfeito'),
            4: _('Muito Satisfeito'),
            5: _('Extremamente Satisfeito')            
        }
        rating.write({'rating': rate, 'consumed': True})
        lang = rating.partner_id.lang or get_lang(request.env).code
        return request.env['ir.ui.view'].with_context(lang=lang)._render_template('rating.rating_external_page_submit', {
            'rating': rating, 'token': token,
            'rate_names': rate_names, 'rate': rate
        })

    @http.route(['/rate/<string:token>/submit_feedback'], type="http", auth="public", methods=['post'], website=True)
    def action_submit_rating(self, token, **kwargs):
        rate = int(kwargs.get('rate'))
        assert rate in (1, 2, 3, 4, 5), "Incorrect rating"
        rating = request.env['rating.rating'].sudo().search([('access_token', '=', token)])
        if not rating:
            return request.not_found()
        record_sudo = request.env[rating.res_model].sudo().browse(rating.res_id)
        record_sudo.rating_apply(rate, token=token, feedback=kwargs.get('feedback'))
        lang = rating.partner_id.lang or get_lang(request.env).code
        return request.env['ir.ui.view'].with_context(lang=lang)._render_template('rating.rating_external_page_view', {
            'web_base_url': rating.get_base_url(),
            'rating': rating,
        })
