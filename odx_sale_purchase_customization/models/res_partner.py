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

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    customer_code = fields.Char('Customer code')
    _sql_constraints = [
        ('customer_code_uniq', 'unique (customer_code)', "Customer Code should be Unique !"),
    ]

    @api.depends('country_id')
    @api.depends_context('force_company')
    def _compute_product_pricelist(self):
        company = self.env.context.get('force_company', False)
        res = self.env['product.pricelist']._get_partner_pricelist_multi(self.ids, company_id=company)
        for p in self:
            if res:
                p.property_product_pricelist = res.get(p.id)
            else:
                p.property_product_pricelist = 2

    @api.depends('is_company', 'name','customer_code', 'parent_id.display_name', 'type', 'company_name')
    def _compute_display_name(self):
        res = super(ResPartner,self)._compute_display_name()
        return res

    def name_get(self):
        """adding sequence to the name"""
        result = []
        for r in self:
            if r.customer_code:
                result.append((r.id, u"%s-%s" % (r.name, r.customer_code)))
            else:
                result.append((r.id, u"%s" % (r.name)))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """modifying the name_search to include the sequence also in search"""
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search(['|', ('name', '=', name), ('customer_code', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search(['|', ('name', operator, name), ('customer_code', operator, name)] + args, limit=limit)
        return recs.name_get()
