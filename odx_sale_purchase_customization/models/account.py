# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2020 Odox SoftHub LLP(<www.odoxsofthub.com>)
#    Author: Albin Mathew(<albinmathew07@outlook.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
import ast

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_amount(self):

        invoice_ids = [move.id for move in self if move.id and move.is_invoice(include_receipts=True)]
        self.env['account.payment'].flush(['state'])
        if invoice_ids:
            self._cr.execute(
                '''
                    SELECT move.id
                    FROM account_move move
                    JOIN account_move_line line ON line.move_id = move.id
                    JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
                    JOIN account_move_line rec_line ON
                        (rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
                        OR
                        (rec_line.id = part.debit_move_id AND line.id = part.credit_move_id)
                    JOIN account_payment payment ON payment.id = rec_line.payment_id
                    JOIN account_journal journal ON journal.id = rec_line.journal_id
                    WHERE payment.state IN ('posted', 'sent')
                    AND journal.post_at = 'bank_rec'
                    AND move.id IN %s
                ''', [tuple(invoice_ids)]
            )
            in_payment_set = set(res[0] for res in self._cr.fetchall())
        else:
            in_payment_set = {}

        for move in self:
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            currencies = set()
            total_commission = 0.0
            for line in move.line_ids:
                if line.currency_id:
                    currencies.add(line.currency_id)

                # Untaxed amount.
                if (move.is_invoice(include_receipts=True) and not line.exclude_from_invoice_tab) \
                        or (move.type == 'entry' and line.debit and not line.tax_line_id):
                    total_untaxed += line.balance
                    total_untaxed_currency += line.amount_currency
                    total_commission += line.com_amount

                # Tax amount.
                if line.tax_line_id:
                    total_tax += line.balance
                    total_tax_currency += line.amount_currency

                # Residual amount.
                if move.type == 'entry' or line.account_id.user_type_id.type in ('receivable', 'payable'):
                    total_residual += line.amount_residual
                    total_residual_currency += line.amount_residual_currency

            total = total_untaxed + total_tax
            total_currency = total_untaxed_currency + total_tax_currency
            if move.type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_discount = sum(
                (line.quantity * line.price_unit * line.discount) / 100 for line in move.invoice_line_ids)
            move.amount_commission = sum(
                (line.quantity * line.price_unit * line.commission) / 100 for line in move.invoice_line_ids)
            move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed) + sum(
                (line.quantity * line.price_unit * line.discount) / 100 for line in move.invoice_line_ids)
            move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            move.amount_total = sign * (total_currency if len(currencies) == 1 else total) - total_commission
            move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = -total
            move.amount_residual_signed = total_residual

            currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
            is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual

            # Compute 'invoice_payment_state'.
            if move.state == 'posted' and is_paid:
                if move.id in in_payment_set:
                    move.invoice_payment_state = 'in_payment'
                else:
                    move.invoice_payment_state = 'paid'
            else:
                move.invoice_payment_state = 'not_paid'

    sale_id = fields.Many2one('sale.order', string="Sale Order", store=True, readonly=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', store=True, readonly=True)
    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount Type',
                                     readonly=True, states={'draft': [('readonly', False)]}, default='percent')
    discount_rate = fields.Float('Discount Amount', digits=(16, 2), readonly=True,
                                 states={'draft': [('readonly', False)]})
    amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_compute_amount',
                                      track_visibility='always')
    amount_commission = fields.Monetary(string='Commission', store=True, readonly=True, compute='_compute_amount',
                                        track_visibility='always')

    @api.onchange('discount_type', 'discount_rate', 'invoice_line_ids')
    def supply_rate(self):
        for inv in self:
            if inv.discount_type == 'percent':
                for line in inv.line_ids:
                    print(line.exclude_from_invoice_tab)
                    if line.exclude_from_invoice_tab:
                        continue
                    line.discount = inv.discount_rate
                    line._onchange_price_subtotal()
            else:
                total = discount = 0.0
                for line in inv.invoice_line_ids:
                    total += (line.quantity * line.price_unit)
                if inv.discount_rate != 0:
                    discount = (inv.discount_rate / total) * 100
                else:
                    discount = inv.discount_rate
                for line in inv.invoice_line_ids:
                    line.discount = discount
                    line._onchange_price_subtotal()
        self._recompute_dynamic_lines()

    def button_dummy(self):
        self.supply_rate()
        return True

    def _get_default_reference(self):
        """:return PO reference"""

        if self._context.get('default_ref'):
            return self._context.get('default_ref')
        return False

    reference = fields.Char(string='Reference', copy=False, store=True, default=_get_default_reference)

    def _recompute_commission_lines(self):
        """ thi function is used to create journal item for commission"""
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _prepare_commission_move_line(self):
            """
            This function searches a specific product i.e, commission and
            returns field values required in purchase journal entry line.
            The whole purpose is to add a new product for commission from
            the product configured in account.move.line
            :return:{dict} containing {field: value} for the account.move.line
            """
            self.ensure_one()
            get_param = self.env['ir.config_parameter'].sudo().get_param
            account = get_param('odx_sale_purchase_customization.commission_account_id')
            if not account:
                raise UserError(_("Please configure a account for commission in settings."))
            account = ast.literal_eval(account)
            account_id = self.env["account.account"].search([('id', '=', account)], limit=1)
            commission_amount = 00.0
            amount_currency = 0.0
            for line in self.invoice_line_ids:
                print(line.com_amount)
                commission_amount += line.com_amount
            if self.currency_id != self.company_id.currency_id:
                amount_currency = abs(commission_amount)
                commission_amount = self.currency_id._convert(amount_currency, self.company_currency_id,
                                                              self.company_id,
                                                              self.date)

            commission_move_line = {
                'debit': commission_amount < 0.0 and - commission_amount or 0.0,
                'credit': commission_amount > 0.0 and commission_amount or 0.0,
                'name': '%s: %s' % (self.reference, 'Commission'),
                'move_id': self.id,
                'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                'account_id': account_id.id,
                'exclude_from_invoice_tab': True,
                'partner_id': self.partner_id.id,
                'amount_currency': -amount_currency,
                'quantity': 1.0,
                'is_commission_line': True

            }
            return commission_move_line

        get_param = self.env['ir.config_parameter'].sudo().get_param
        account = get_param('odx_sale_purchase_customization.commission_account_id')
        if not account:
            raise UserError(_("Please configure a account for commission in settings."))
        account = ast.literal_eval(account)
        account_id = self.env["account.account"].search([('id', '=', account)], limit=1)

        existing_commission_lines = self.line_ids.filtered(lambda line: line.account_id == account_id)
        if existing_commission_lines:
            self.line_ids -= existing_commission_lines
        commission_move_line = _prepare_commission_move_line(self)
        create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
            'account.move.line'].create
        new_commission_line = create_method(commission_move_line)
        if in_draft_mode:
            new_commission_line._onchange_amount_currency()
            new_commission_line._onchange_balance()
            # new_commission_line._onchange_commission()

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        ''' Recompute all lines that depend of others.

        For example, tax lines depends of base lines (lines having tax_ids set). This is also the case of cash rounding
        lines that depend of base lines or tax lines depending the cash rounding strategy. When a payment term is set,
        this method will auto-balance the move with payment term lines.

        :param recompute_all_taxes: Force the computation of taxes. If set to False, the computation will be done
                                    or not depending of the field 'recompute_tax_line' in lines.
        '''
        for invoice in self:
            # Dispatch lines and pre-compute some aggregated values like taxes.
            for line in invoice.line_ids:
                if line.recompute_tax_line:
                    recompute_all_taxes = True
                    line.recompute_tax_line = False

            # Compute taxes.
            if recompute_all_taxes:
                invoice._recompute_tax_lines()
            if recompute_tax_base_amount:
                invoice._recompute_tax_lines(recompute_tax_base_amount=True)

            if invoice.is_invoice(include_receipts=True):

                # Compute cash rounding.
                invoice._recompute_cash_rounding_lines()

                # additional line
                # compute commission line
                invoice._recompute_commission_lines()

                # Compute payment terms.
                invoice._recompute_payment_terms_lines()

                # Only synchronize one2many in onchange.
                if invoice != invoice._origin:
                    invoice.invoice_line_ids = invoice.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    commission = fields.Float(string='Commission %')
    total = fields.Float(string="Total")
    com_amount = fields.Float(string="Com.Amount")
    is_commission_line = fields.Boolean(string="Is commission Line")
    discount = fields.Float(string='Discount (%)', digits=(16, 20), default=0.0)

    @api.onchange('commission', 'price_unit', 'quantity', 'price_subtotal')
    def _onchange_commission(self):
        total = self.price_unit * self.quantity
        if self.commission:
            self.com_amount = (total * self.commission) / 100
            self.total = self.price_subtotal - self.com_amount
