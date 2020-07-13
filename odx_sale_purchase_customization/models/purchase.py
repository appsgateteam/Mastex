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
from odoo import fields, models, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    sale_order_id = fields.Many2one(comodel_name="sale.order", string="SO#", copy=False)
    customer_id = fields.Many2one(comodel_name='res.partner', string="Customer")
    sequence_no = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                              default=lambda self: _('New'))

    landing_line_ids = fields.One2many('purchase.landing.cost', 'purchase_id', string="Landing Costs")

    def button_confirm(self):
        """ inherited to create sale order,
         first check for an existing sale order for the corresponding PO
         if does not exist, create a new sale order"""
        for record in self:
            res = super(PurchaseOrder, self).button_confirm()
            if not record.sale_order_id:
                sale_order_lines = []
                sale_order_obj = self.env['sale.order']
                for line in record.order_line:
                    taxes = line.product_id.taxes_id
                    fpos = record.fiscal_position_id
                    taxes_id = fpos.map_tax(taxes, line.product_id, record.partner_id) if fpos else taxes
                    if taxes_id:
                        taxes_id = taxes_id.filtered(lambda x: x.company_id.id == record.company_id.id)
                    sale_order_lines.append((0, 0, {'product_id': line.product_id.id,
                                                    'name': line.name,
                                                    'tax_id': [(6, 0, taxes_id.ids)],
                                                    'product_uom_qty': line.product_qty,
                                                    "product_uom": line.product_uom.id,
                                                    'price_unit': line.price_unit,
                                                    }))
                vals = {
                    "partner_id": record.customer_id.id,
                    "vendor_id": record.partner_id.id,
                    "purchase_order_id": record.id,
                    "order_line": sale_order_lines,
                    "sequence_no": record.sequence_no
                }
                sale_order = sale_order_obj.create(vals)
                record.sale_order_id = sale_order.id
            return res

    @api.model
    def create(self, values):
        """
        adding values to the name from sequence
        :param values:
        :return: new record id
        """
        code = ''
        if values['partner_id']:
            customer = self.env['res.partner'].browse(values['partner_id'])
            if customer:
                code = customer.customer_code
        if values.get('sequence_no', _('New')) == _('New'):
            # values['name'] = self.env['ir.sequence'].next_by_code('sale.delivery')
            values['sequence_no'] = str(code) + " " + self.env['ir.sequence'].next_by_code('order.reference',
                                                                                           None) or _('New')
        return super(PurchaseOrder, self).create(values)

    def name_get(self):
        """adding sequence to the name"""
        return [(r.id, u"%s-%s" % (r.name, r.sequence_no)) for r in self]


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    actual_qty = fields.Float(string='Actual Quantity', required=True
                              , default=1.0)

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)

        res.update({'quantity': self.actual_qty})

        return res


class LandingCost(models.Model):
    _name = 'purchase.landing.cost'
    _description = 'Purchase Landing Cost'

    name = fields.Char("AWB", required=True)
    landing_date = fields.Date('Date', required=True)
    landing_company = fields.Char("Company", required=True)
    landing_amount = fields.Float('Amount', required=True)
    landing_attachment = fields.Binary('Document',  attachment=True)
    landing_attachment_name = fields.Char('Document Name')
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", ondelete='cascade')