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

    colour_instructions = fields.Text(string="Colour Instructions")
    packing = fields.Text(string="Packing")
    face_stamp = fields.Text(string="Face Stamp on Paper and Booklet File")
    selvedge = fields.Text(string="Selvedge")
    shipping_mark = fields.Text(string="Shipping Mark")
    shipping_sample_book = fields.Text(string="Shipping Sample Book File")
    notes = fields.Text(string="Notes")

    def button_confirm(self):
        """ inherited to create sale order,
         first check for an existing sale order for the corresponding PO
         if does not exist, create a new sale order"""
        for record in self:
            res = super(PurchaseOrder, self).button_confirm()
            if not record.sale_order_id and record.customer_id:
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
                                                    "actual_qty":line.actual_qty
                                                    }))
                vals = {
                    "partner_id": record.customer_id.id,
                    "vendor_id": record.partner_id.id,
                    "purchase_order_id": record.id,
                    "order_line": sale_order_lines,
                    "sequence_no": record.sequence_no,
                    "colour_instructions": record.colour_instructions,
                    "packing": record.packing,
                    "face_stamp": record.face_stamp,
                    "selvedge": record.selvedge,
                    "shipping_mark": record.shipping_mark,
                    "shipping_sample_book": record.shipping_sample_book,
                    "notes": record.notes,
                }
                sale_order = sale_order_obj.create(vals)
                record.sale_order_id = sale_order.id
            return res

    def action_view_invoice(self):
        print()
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        action = self.env.ref('account.action_move_in_invoice_type')
        result = action.read()[0]
        create_bill = self.env.context.get('create_bill', False)
        # override the context to get rid of the default filtering
        result['context'] = {
            'default_type': 'in_invoice',
            'default_company_id': self.company_id.id,
            'default_purchase_id': self.id,
            'default_ref': self.sequence_no,
        }
        # choose the view_mode accordingly
        if len(self.invoice_ids) > 1 and not create_bill:
            result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
        else:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                result['views'] = form_view
            # Do not set an invoice_id if we want to create a new bill.
            if not create_bill:
                result['res_id'] = self.invoice_ids.id or False
        result['context']['default_origin'] = self.name
        result['context']['default_reference'] = self.partner_ref
        return result

    @api.model
    def create(self, values):
        """
        adding values to the name from sequence
        :param values:
        :return: new record id
        """
        code = ''
        if values['partner_id']:
            customer = self.env['res.partner'].browse(values['customer_id'])
            if customer:
                code = customer.customer_code
        if values.get('sequence_no', _('New')) == _('New') and  values['customer_id']:
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

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        if self.product_qty:
            self.actual_qty = self.product_qty


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
    no_of_packages = fields.Char('No Of Packages')
    destination = fields.Char("Destination")
    marks = fields.Char("Marks")
    reference = fields.Char("Refrence")