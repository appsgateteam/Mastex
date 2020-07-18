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
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    sale_order_id = fields.Many2one(comodel_name="sale.order", string="SO#", copy=False)
    customer_id = fields.Many2one(comodel_name='res.partner', string="Customer")

    # Bill of Lading
    landing_line_ids = fields.One2many(comodel_name='purchase.landing.cost', inverse_name='purchase_id',
                                       string="Landing Costs")
    # Instructions
    colour_instructions = fields.Text(string="Colour Instructions")
    packing = fields.Text(string="Packing")
    face_stamp = fields.Text(string="Face Stamp on Paper and Booklet File")
    selvedge = fields.Text(string="Selvedge")
    shipping_mark = fields.Text(string="Shipping Mark")
    shipping_sample_book = fields.Text(string="Shipping Sample Book File")
    notes = fields.Text(string="Notes")

    # Other details
    shipment = fields.Char(string="Shipment")
    payment = fields.Char(string="Payment")
    insurance_id = fields.Many2one(comodel_name='res.insurance', string="Insurance")
    destination_id = fields.Many2one(comodel_name='res.destination', string='Destination')
    marks = fields.Char(string="Marks", )

    # Shipment details
    is_sample_customer = fields.Boolean(string='Sample received from customer')
    is_sample_vendor = fields.Boolean(string='Samples sent to supplier')
    is_vendor_sample_customer = fields.Boolean(string='Supplier initial Sample')
    is_sample_company = fields.Boolean(string='Supplier final samples')
    purchase_shipment_ids = fields.One2many('purchase.shipment', 'purchase_id', string="Shipment Details")

    # attachments
    attachment_ids = fields.One2many('ir.attachment', 'purchase_id', string='Attachment', copy=False)
    attachment_count = fields.Integer(compute='_compute_attachment_count')

    def photos(self):
        return {
            'name': 'Photos',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'ir.attachment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {'default_purchase_id': self.id},
            'domain': [('purchase_id', '=', self.id)]

        }

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for order in self:
            order.attachment_count = len(order.attachment_ids)

    @api.onchange('purchase_shipment_ids')
    def _onchange_type(self):
        for record in self:
            record.is_sample_customer = False
            record.is_sample_vendor = False
            record.is_vendor_sample_customer = False
            record.is_sample_company = False
            if record.purchase_shipment_ids:
                for shipment in record.purchase_shipment_ids:
                    if shipment.type:
                        if shipment.type == 'sample_customer':
                            record.is_sample_customer = True
                        elif shipment.type == 'sample_vendor':
                            record.is_sample_vendor = True
                        elif shipment.type == 'vendor_sample_customer':
                            record.is_vendor_sample_customer = True
                        elif shipment.type == 'sample_company':
                            record.is_sample_company = True

    def button_confirm(self):
        """ inherited to create sale order,
         first check for an existing sale order for the corresponding PO
         if does not exist, create a new sale order"""
        for record in self:
            res = super(PurchaseOrder, self).button_confirm()
            if not record.sale_order_id and record.customer_id:
                sale_order_lines = []
                attachment_ids = []
                sale_order_obj = self.env['sale.order']
                for attchment in record.attachment_ids:
                    attachment_ids.append((0, 0, {
                        'name': attchment.name,
                        'datas': attchment.datas,
                        "description": attchment.description,
                        "mimetype": attchment.mimetype,
                        'index_content': attchment.index_content,
                        "create_uid": attchment.create_uid.id,
                    }))
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
                                                    "actual_qty": line.actual_qty
                                                    }))
                vals = {
                    "partner_id": record.customer_id.id,
                    "vendor_id": record.partner_id.id,
                    "purchase_order_id": record.id,
                    "order_line": sale_order_lines,
                    "attachment_ids": attachment_ids,
                    "colour_instructions": record.colour_instructions,
                    "packing": record.packing,
                    "name": record.name,
                    "face_stamp": record.face_stamp,
                    "selvedge": record.selvedge,
                    "shipping_mark": record.shipping_mark,
                    "shipping_sample_book": record.shipping_sample_book,
                    "notes": record.notes,
                    "shipment": record.shipment,
                    "payment": record.payment,
                    "insurance_id": record.insurance_id.id,
                    "destination_id": record.destination_id.id,
                }
                sale_order = sale_order_obj.create(vals)
                record.sale_order_id = sale_order.id
            return res

    def action_view_invoice(self):
        res = super(PurchaseOrder, self).action_view_invoice()
        res['context'].update({'default_ref': self.name})
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
            customer = self.env['res.partner'].browse(values['customer_id'])
            if customer:
                if customer.customer_code:
                    code = customer.customer_code
        if values.get('name', _('New')) == _('New'):
            values['name'] = str(code) + " " + self.env['ir.sequence'].next_by_code('order.reference',
                                                                                    None) or _('New')
            values['marks'] = values['name']
        return super(PurchaseOrder, self).create(values)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    actual_qty = fields.Float(string='Actual Quantity', required=True
                              , default=0.0)
    attachment_ids = fields.Many2many(comodel_name="ir.attachment", string="Images")

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        res.update({'quantity': self.actual_qty})
        return res

    @api.model_create_multi
    def create(self, values):
        """
        Generates an error message when an additional line is created in PO, when the state
        is in purchase, done
        :param values:
        :return: new record
        """
        res = super(PurchaseOrderLine, self).create(values)
        states = ['purchase', 'done']
        if res.order_id.state in states:
            raise UserError(_('You can not create an additional purchase order line in a confirmed order '))
        return res


class LandingCost(models.Model):
    _name = 'purchase.landing.cost'
    _description = 'Purchase Landing Cost'

    name = fields.Char(string="AWB", required=True)
    landing_date = fields.Date(string='Date', required=True)
    landing_company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                         default=lambda self: self.env.company)
    landing_attachment = fields.Binary(string='Document', attachment=True)
    landing_attachment_name = fields.Char(string='Document Name')
    purchase_id = fields.Many2one(comodel_name='purchase.order', string="Purchase Order", ondelete='cascade')
    no_of_packages = fields.Char(string='No Of Packages')
    destination = fields.Char(string="Destination")
    marks = fields.Char(string="Marks")
    reference = fields.Char(string="Reference")


class PurchaseShipment(models.Model):
    _name = 'purchase.shipment'

    shipment_to = fields.Many2one(comodel_name='shipment.destination', string="Shipment To")
    shipment_from = fields.Many2one(comodel_name='shipment.destination', string="Shipment From")
    from_date = fields.Datetime(string='Start Date', copy=False, default=fields.Datetime.now, store=True)
    to_date = fields.Datetime(string='Expected Delivery Date', copy=False, store=True)
    reference = fields.Char(string="Reference")
    description = fields.Char(string="Description")
    status = fields.Selection([('sent', 'Sent'), ('received', 'Received'), ('cancel', 'Canceled')],
                              string='Status')
    type = fields.Selection([('sample_customer', 'Receive sample from customer'),
                             ('sample_vendor', 'Sent sample to vendor'),
                             ('vendor_sample_customer', 'Sent First Sample'),
                             ('sample_company', ' Sent Final Sample')],
                            string='Type')
    attachment = fields.Binary(string="Files", attachment=True)
    attachment_name = fields.Char(string="File Name")
    purchase_id = fields.Many2one('purchase.order', string="purchase Order", ondelete='cascade')


class ShippingDestination(models.Model):
    _name = 'shipment.destination'
    _description = 'Shipping Destination'

    name = fields.Char("Name", required=True)
