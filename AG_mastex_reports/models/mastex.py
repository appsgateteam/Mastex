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
    _inherit = "sale.order"

    packages = fields.Float("No Of Packages",compute="get_packages",store=True)

    # @api.depends('invoice_origin')
    def get_packages(self):
        for rec in self:
            # rec.packages = 0

            packs = 0.0
            # sale = self.env['sale.order'].search([('name','in',rec.invoice_origin)])
            # for sa in sale:
            for line in rec.landing_line_ids:
                packa = line.no_of_packages.replace(' Bales', '').replace(' Bales-','').replace(' cartons-','').replace(' cartons','')
                pack = float(packa)
                packs += pack
            rec.packages = packs





# @api.multi
# def currency_text(self, sum, currency, language):
#     return currency_to_text(sum, currency, language)
