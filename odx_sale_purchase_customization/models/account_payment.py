import ast

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    customer_currency_id = fields.Many2one('res.currency', string='Customer Currency')
    amount_in_currency = fields.Monetary('Amount In Currency',compute='_compute_amount')

    @api.depends('currency_id','customer_currency_id','amount','company_id','payment_date')
    def _compute_amount(self):
        for payment in self:
            if payment.company_id:
                payment.amount_in_currency = payment.currency_id._convert(payment.amount, payment.customer_currency_id,
                                                                              payment.company_id,
                                                                              payment.payment_date)

            else:
                payment.company_id = 0