from odoo import models, api, fields


class AccountMove(models.Model):
    _inherit = "account.move.line"

    @api.onchange('debit')
    def _onchange_debit(self):
        if self.debit:
            self.credit = 0.0
            if self.currency_id:
                self.amount_currency = self.env.company.currency_id._convert(self.debit, self.currency_id,
                                                                             self.env.company,fields.Date.today())
        self._onchange_balance()


    @api.onchange('credit')
    def _onchange_credit(self):
        if self.credit:
            self.debit = 0.0
            if self.currency_id:
              self.amount_currency = self.env.company.currency_id._convert(-self.credit, self.currency_id,
                                                                           self.env.company, fields.Date.today())
        self._onchange_balance()


    def _recompute_debit_credit_from_amount_currency(self):
        for line in self:
            # Recompute the debit/credit based on amount_currency/currency_id and date.
            company_currency = line.account_id.company_id.currency_id
            balance = line.amount_currency
            if line.currency_id and company_currency and line.currency_id != company_currency:
                if line.debit:
                    balance1 = company_currency._convert(line.debit, line.currency_id ,line.account_id.company_id, line.move_id.date or fields.Date.today())

                    line.amount_currency = balance1
                elif line.credit:
                    balance2 = company_currency._convert(-line.credit, line.currency_id ,line.account_id.company_id, line.move_id.date or fields.Date.today())

                    line.amount_currency = balance2

    # ------------------------------------------------------------