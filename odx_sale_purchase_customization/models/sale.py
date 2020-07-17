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
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "Sales Order"

    purchase_order_id = fields.Many2one(comodel_name="purchase.order", string="PO#", copy=False)
    vendor_id = fields.Many2one(comodel_name='res.partner', string="Vendor")

    # Instructions
    colour_instructions = fields.Text(string="Colour Instructions", related="purchase_order_id.colour_instructions")
    packing = fields.Text(string="Packing", related="purchase_order_id.packing")
    face_stamp = fields.Text(string="Face Stamp on Paper and Booklet File", related="purchase_order_id.face_stamp")
    selvedge = fields.Text(string="Selvedge", related="purchase_order_id.selvedge")
    shipping_mark = fields.Text(string="Shipping Mark", related="purchase_order_id.shipping_mark")
    shipping_sample_book = fields.Text(string="Shipping Sample Book File", related="purchase_order_id.shipping_sample_book")
    notes = fields.Text(string="Notes", related="purchase_order_id.notes")

    # Other details
    shipment = fields.Char(string="Shipment", related="purchase_order_id.shipment")
    payment = fields.Char(string="Payment", related="purchase_order_id.payment")
    insurance_id = fields.Many2one(comodel_name='res.insurance', string="Insurance",
                                   related="purchase_order_id.insurance_id")
    destination_id = fields.Many2one(comodel_name='res.destination', string='Destination',
                                     related='purchase_order_id.destination_id')
    marks = fields.Char(string="Marks")

    attachment_ids = fields.One2many('ir.attachment', 'sale_id', string='Attachment')
    attachment_count = fields.Integer(compute='_compute_attachment_count')

    def photos(self):
        return {
            'name': 'Photos',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'ir.attachment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {'default_sale_id': self.id},
            'domain': [('sale_id', '=', self.id)]

        }

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for order in self:
            order.attachment_count = len(order.attachment_ids)

    def action_confirm(self):
        """ inherited to create sale order,
         first check for an existing sale order for the corresponding SO
         if does not exist, create a new purchase order"""
        for record in self:
            res = super(SaleOrder, self).action_confirm()
            if not record.purchase_order_id and record.vendor_id:
                purchase_order_lines = []
                attachment_ids = []
                purchase_order_obj = self.env['purchase.order']
                for attchment in record.attachment_ids:
                    attachment_ids.append((0, 0, {
                        'name': attchment.name,
                        'datas': attchment.datas,
                        "description":attchment.description,
                        "mimetype": attchment.mimetype,
                        'index_content': attchment.index_content,
                        "create_uid": attchment.create_uid.id,
                    }))
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
                                                        "actual_qty": line.actual_qty,
                                                        'taxes_id': [(6, 0, taxes_id.ids)],
                                                        }))

                vals = {
                    "partner_id": record.vendor_id.id,
                    "sale_order_id": record.id,
                    "customer_id": record.partner_id.id,
                    "order_line": purchase_order_lines,
                    "attachment_ids": attachment_ids,
                    "colour_instructions": record.colour_instructions,
                    "packing": record.packing,
                    "face_stamp": record.face_stamp,
                    "name": record.name,
                    "selvedge": record.selvedge,
                    "shipping_mark": record.shipping_mark,
                    "shipping_sample_book": record.shipping_sample_book,
                    "notes": record.notes,
                    "shipment": record.shipment,
                    "payment": record.payment,
                    "insurance_id": record.insurance_id.id,
                    "destination_id": record.destination_id.id,

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
                if customer:
                    code = customer.customer_code

        if values.get('name', _('New')) == _('New'):
            # values['name'] = self.env['ir.sequence'].next_by_code('sale.delivery')
            values['name'] = str(code) + " " + self.env['ir.sequence'].next_by_code('order.reference',
                                                                                    None) or _('New')
            values['marks'] = values['name']
        return super(SaleOrder, self).create(values)

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['reference'] = self.name
        res['ref'] = self.name
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    actual_qty = fields.Float(string='Actual Quantity', required=True
                              , default=1.0)

    # attachment_ids = fields.Many2many(comodel_name="ir.attachment", string="Images")

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res.update({'quantity': self.actual_qty})
        return res

    @api.depends('state', 'actual_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.

        ***Additional Customization***
            Overriden base function to change the dependency of the the  product quantity to actual quantity
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.state not in ('sale', 'done'):
                line.invoice_status = 'no'
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and \
                    float_compare(line.qty_delivered, line.actual_qty, precision_digits=precision) == 1:
                print(line.qty_delivered, line.actual_qty)
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.actual_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    @api.depends('qty_invoiced', 'qty_delivered', 'actual_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the actual quantity. Otherwise, the quantity delivered is used.

        ***Additional Customization***
            Overriden base function to change the dependency of the the  product quantity to actual quantity
        """
        for line in self:
            if line.order_id.state in ['sale', 'done']:

                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.actual_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.model_create_multi
    def create(self, values):
        """
        Generates an error message when an additional line is created in SO, when the state
        is in sale, done
        :param values:
        :return: new record
        """
        res = super(SaleOrderLine, self).create(values)
        states = ['sale', 'done']
        if res.state in states:
            raise UserError(_('You can not create an additional sale order line in a confirmed sale order '))
        return res


class ResInsurance(models.Model):
    _name = 'res.insurance'

    name = fields.Char("Name", required=True)


class ResMarks(models.Model):
    _name = 'res.marks'

    name = fields.Char("Name", required=True)


class ResDestination(models.Model):
    _name = 'res.destination'

    name = fields.Char("Name", required=True)
