import ast

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    customer_currency_id = fields.Many2one('res.currency', string='Customer Currency')
    amount_in_currency = fields.Monetary('Amount In Currency',compute='_compute_amount')

    @api.depends('currency_id', 'customer_currency_id')
    def _compute_amount(self):
        for payment in self:
            payment.amount_in_currency = payment.customer_currency_id._convert(payment.amount, payment.currency_id,
                                                                              payment.company_id,
                                                                              payment.payment_date)
