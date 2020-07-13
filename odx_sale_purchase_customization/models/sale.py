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
from datetime import datetime

from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "Sales Order"

    purchase_order_id = fields.Many2one(comodel_name="purchase.order", string="PO#", copy=False)
    vendor_id = fields.Many2one(comodel_name='res.partner', string="Vendor")
    sequence_no = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                              default=lambda self: _('New'))
    colour_instructions = fields.Text(string="Colour Instructions")
    packing = fields.Text(string="Packing")
    face_stamp = fields.Text(string="Face Stamp on Paper and Booklet File")
    selvedge = fields.Text(string="Selvedge")
    shipping_mark = fields.Text(string="Shipping Mark")
    shipping_sample_book = fields.Text(string="Shipping Sample Book File")
    notes = fields.Text(string="Notes")

    def action_confirm(self):
        """ inherited to create sale order,
         first check for an existing sale order for the corresponding SO
         if does not exist, create a new purchase order"""
        for record in self:
            res = super(SaleOrder, self).action_confirm()
            if not record.purchase_order_id and record.vendor_id:
                purchase_order_lines = []
                purchase_order_obj = self.env['purchase.order']
                for line in record.order_line:
                    taxes = line.product_id.supplier_taxes_id
                    fpos = record.fiscal_position_id
                    taxes_id = fpos.map_tax(taxes, line.product_id, record.vendor_id) if fpos else taxes
                    if taxes_id:
                        taxes_id = taxes_id.filtered(lambda x: x.company_id.id == record.company_id.id)

                    purchase_order_lines.append((0, 0, {'product_id': line.product_id.id,
                                                        'name': line.name,
                                                        'product_qty': line.product_uom_qty,
                                                        "date_planned": datetime.today(),
                                                        "product_uom": line.product_uom.id,
                                                        'price_unit': line.price_unit,
                                                        'taxes_id': [(6, 0, taxes_id.ids)],
                                                        }))
                vals = {
                    "partner_id": record.vendor_id.id,
                    "sale_order_id": record.id,
                    "customer_id": record.partner_id.id,
                    "order_line": purchase_order_lines,
                    "sequence_no": record.sequence_no
                }
                purchase = purchase_order_obj.create(vals)
                record.purchase_order_id = purchase.id
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
        return super(SaleOrder, self).create(values)


    def name_get(self):
        """adding sequence to the name"""
        return [(r.id, u"%s-%s" % (r.name, r.sequence_no)) for r in self]


#
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    actual_qty = fields.Float(string='Actual Quantity', required=True
                              , default=1.0)

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()

        res.update({'quantity': self.actual_qty})

        return res

    @api.onchange('product_uom_qty')
    def _onchange_qty_uom(self):
        if self.product_uom_qty:
            self.actual_qty = self.product_uom_qty