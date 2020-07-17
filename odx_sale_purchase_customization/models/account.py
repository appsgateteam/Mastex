
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_default_reference(self):
        """:return PO reference"""

        if self._context.get('default_ref'):
            return self._context.get('default_ref')
        return False

    reference = fields.Char(string='Reference', copy=False, store=True, default=_get_default_reference)
