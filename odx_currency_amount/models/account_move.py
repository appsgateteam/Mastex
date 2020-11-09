from odoo import models, api, fields


class AccountMove(models.Model):
    _inherit = "account.move.line"

    @api.onchange('debit')
    def _onchange_debit(self):
        if self.debit:
            self.credit = 0.0
            if self.currency_id:
                self.amount_currency = self.env.company.currency_id._convert(self.debit, self.currency_id, self.env.company, fields.Date.today())
                print(self.amount_currency)
        self._onchange_balance()

    @api.onchange('credit')
    def _onchange_credit(self):
        if self.credit:
            self.debit = 0.0
            if self.currency_id:
                self.amount_currency = self.env.company.currency_id._convert(-self.credit, self.currency_id, self.env.company, fields.Date.today())
        self._onchange_balance()