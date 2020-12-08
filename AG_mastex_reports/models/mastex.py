# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools ,_
from odoo.exceptions import except_orm, ValidationError,UserError
from odoo.exceptions import  AccessError, UserError, RedirectWarning,Warning
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta , date
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import odoo.exceptions
import re 

class accountmove(models.Model):
    _inherit = "account.move"

    packages = fields.Float("No Of Packages",compute="get_packages",store=True)

    @api.depends('sale_id')
    def get_packages(self):
        for rec in self:
            if rec.sale_id:
                packs = 0.0
                for line in rec.sale_id.landing_line_ids:
                    pack = float(line.no_of_packages)
                    packs += pack
                rec.packages = packs
                    
            else:
                rec.packages = 0





# @api.multi
# def currency_text(self, sum, currency, language):
#     return currency_to_text(sum, currency, language)
