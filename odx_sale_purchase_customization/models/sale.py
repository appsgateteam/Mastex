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
import base64

from odoo import fields, models, api, _
# from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "Sales Order"
    _order = 'name desc'

    purchase_order_id = fields.Many2one(comodel_name="purchase.order", string="PO#", copy=False)
    
    billing_status = fields.Selection([         
        ('no', 'Nothing to Bill'),
        ('to invoice', 'To Bill'),
        ('invoiced', 'Fully Billed'),
    ], string='Billing Status', compute='_compute_bill_status', store=True, copy=False)
    
    vendor_id = fields.Many2one(comodel_name='res.partner', string="Vendor")

    landing_line_ids = fields.One2many(comodel_name='purchase.landing.cost', inverse_name='sale_id',
                                       string="Bill Of Ladings")
    purchase_shipment_ids = fields.One2many('purchase.shipment', 'sale_id', string="Shipment Details")
    # Instructions
    colour_instructions = fields.Text(string="Colour Instructions")
    packing = fields.Text(string="Packing")
    face_stamp = fields.Html(string="Face Stamp on Paper and Booklet File")
    selvedge = fields.Html(string="Selvedge")
    shipping_mark = fields.Html(string="Shipping Mark")
    shipping_sample_book = fields.Text(string="Shippment Sample")
    notes = fields.Text(string="Notes")

    # Other details
    shipment_date = fields.Date(string="Shipment Date")
    insurance_id = fields.Many2one(comodel_name='res.insurance', string="Insurance")
    destination_id = fields.Many2one(comodel_name='res.destination', string='Destination')
    marks = fields.Char(string="Marks")
    sale_landing_eta = fields.Date(string='ETA', compute='_compute_sale_eta')
    sale_landing_etd = fields.Date(string='ETD', compute='_compute_sale_eta')

    attachment_ids = fields.One2many('ir.attachment', 'sale_id', string='Attachment')
    attachment_count = fields.Integer(compute='_compute_attachment_count')
    actual_grand_total = fields.Float(string="Actual Grand Total", store=True,compute='_compute_grand_total')
    planned_total = fields.Float(string="Planned Total",store=True, compute='_compute_grand_total')
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string='Invoice Status', compute='_get_invoice_status', store=True, readonly=True)


    @api.depends('state', 'order_line.invoice_status')
    def _get_invoice_status(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.
        """
        unconfirmed_orders = self.filtered(lambda so: so.state not in ['sale', 'done'])
        unconfirmed_orders.invoice_status = 'no'
        confirmed_orders = self - unconfirmed_orders
        if not confirmed_orders:
            return
        line_invoice_status_all = [
            (d['order_id'][0], d['invoice_status'])
            for d in self.env['sale.order.line'].read_group([
                    ('order_id', 'in', confirmed_orders.ids),
                    ('is_downpayment', '=', False),
                    ('display_type', '=', False),
                ],
                ['order_id', 'invoice_status'],
                ['order_id', 'invoice_status'], lazy=False)]
        for order in confirmed_orders:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state not in ('sale', 'done'):
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
         
            elif line_invoice_status and all(invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'

    @api.depends('order_line')
    def _compute_grand_total(self):
        for record in self:
            grand_total = 0
            planned_total = 0
            for line in record.order_line:
                grand_total = grand_total + line.actual_net_amount
                planned_total = planned_total + line.price_subtotal
            record.actual_grand_total = grand_total
            record.planned_total = planned_total
    
    @api.depends('landing_line_ids')
    def _compute_sale_eta(self):
        for record in self:
            sale_eta = False
            sale_etd = False
            landing_ids = self.env['purchase.landing.cost'].search([('sale_id', '=', record.id)])
            for line in landing_ids:
                sale_eta = line.landing_date_eta
                sale_etd = line.landing_date_etd
            record.sale_landing_etd = sale_etd
            record.sale_landing_eta = sale_eta


        return False
  
    
    @api.depends('purchase_order_id.invoice_status')
    def _compute_bill_status(self):
        for record in self:
            bill_status_id = self.env['purchase.order'].search([('sale_order_id', '=', record.id)])
            record.billing_status = bill_status_id.invoice_status
        

    @api.onchange('colour_instructions')
    def _onchange_colour_instructions(self):
        if self.purchase_order_id:
            self.purchase_order_id.colour_instructions = self.colour_instructions

    @api.onchange('packing')
    def _onchange_packing(self):
        if self.purchase_order_id:
            self.purchase_order_id.packing = self.packing

    @api.onchange('face_stamp')
    def _onchange_face_stamp(self):
        if self.purchase_order_id:
            self.purchase_order_id.face_stamp = self.face_stamp

    @api.onchange('selvedge')
    def _onchange_selvedge(self):
        if self.purchase_order_id:
            self.purchase_order_id.selvedge = self.selvedge

    @api.onchange('shipping_mark')
    def _onchange_shipping_mark(self):
        if self.purchase_order_id:
            self.purchase_order_id.shipping_mark = self.shipping_mark

    @api.onchange('shipping_sample_book')
    def _onchange_shipping_sample_book(self):
        if self.purchase_order_id:
            self.purchase_order_id.shipping_sample_book = self.shipping_sample_book

    @api.onchange('notes')
    def _onchange_notes(self):
        if self.purchase_order_id:
            self.purchase_order_id.notes = self.notes

    @api.onchange('shipment_date')
    def _onchange_shipment_date(self):
        if self.purchase_order_id:
            self.purchase_order_id.shipment_date = self.shipment_date

    @api.onchange('destination_id')
    def _onchange_destination_id(self):
        if self.purchase_order_id and self.destination_id:
            self.purchase_order_id.destination_id = self.destination_id.id

    @api.onchange('marks')
    def _onchange_marks(self):
        if self.purchase_order_id:
            self.purchase_order_id.marks = self.marks

    @api.onchange('attachment_ids')
    def _onchange_attachment_ids(self):
        if self.purchase_order_id:
            for attachment in self.attachment_ids:
                attachment.purchase_id = self.purchase_order_id.id

    def photos(self):
        return {
            'name': 'Photos',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'ir.attachment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {'default_sale_id': self.id,
                        'default_purchase_id': self.purchase_order_id.id if self.purchase_order_id else ''},
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
                purchase_order_lines_obj = self.env['purchase.order.line']
                attachment_ids = []
                #landing_line_ids = []
                #purchase_shipment_ids = []
                purchase_order_obj = self.env['purchase.order']
                for attchment in record.attachment_ids:
                    attachment_ids.append((0, 0, {
                        'name': attchment.name,
                        'datas': attchment.datas,
                        "description": attchment.description,
                        "mimetype": attchment.mimetype,
                        'index_content': attchment.index_content,
                        "create_uid": attchment.create_uid.id,
                    }))


                vals = {
                    "partner_id": record.vendor_id.id,
                    "sale_order_id": record.id,
                    "customer_id": record.partner_id.id,
                    "attachment_ids": attachment_ids,
                    "colour_instructions": record.colour_instructions,
                    "packing": record.packing,
                    "face_stamp": record.face_stamp,
                    "name": record.name,
                    "selvedge": record.selvedge,
                    "shipping_mark": record.shipping_mark,
                    "shipping_sample_book": record.shipping_sample_book,
                    "notes": record.notes,
                    "marks": record.marks,
                    "shipment_date": record.shipment_date,
                    "destination_id": record.destination_id.id,
                    "currency_id": record.currency_id.id,


                }
                purchase = purchase_order_obj.create(vals)
                record.purchase_order_id = purchase.id
                for line in record.order_line:
                    taxes = line.product_id.supplier_taxes_id
                    fpos = record.fiscal_position_id
                    taxes_id = fpos.map_tax(taxes, line.product_id, record.vendor_id) if fpos else taxes
                    if taxes_id:
                        taxes_id = taxes_id.filtered(lambda x: x.company_id.id == record.company_id.id)

                    purchase_order_line = purchase_order_lines_obj.create({'product_id': line.product_id.id,
                                                                           'name': line.name,
                                                                           'product_qty': line.product_uom_qty,
                                                                           "date_planned": datetime.today(),
                                                                           "product_uom": line.product_uom.id,
                                                                           'price_unit': line.price_unit,
                                                                           "order_id": purchase.id,
                                                                           "actual_qty": line.actual_qty,
                                                                           "sale_order_line_id": line.id,
                                                                           # "discount": line.discount,
                                                                           'taxes_id': [(6, 0, taxes_id.ids)],
                                                                           })
                    line.purchase_order_line_id = purchase_order_line.id
            return res   

            

    @api.model
    def create(self, values):
        """
        adding values to the name from sequence
        :param values:
        :return: new record id
        """

        if values.get('name', _('New')) == _('New'):
            # values['name'] = self.env['ir.sequence'].next_by_code('sale.delivery')
            values['name'] = self.env['ir.sequence'].next_by_code('order.reference',
                                                                  None) or _('New')
            # values['marks'] = values['name']
        customer_code = ''
        if values.get('partner_id'):
            customer = self.env['res.partner'].browse(values.get('partner_id'))
            customer_code = customer.customer_code
        if values.get('marks'):
            marks_field = values.get('marks')
        else:
            marks_field = ' '

        values['marks'] = '%s %s %s' % (customer_code, values['name'], marks_field)

        return super(SaleOrder, self).create(values)

    def name_get(self):
        """adding SO to the name"""
        result = []
        for r in self:
            result.append((r.id, u"%s %s" % ('SO', r.name)))
        return result

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['reference'] = self.name
        res['sale_id'] = self.id
        res['ref'] = self.name
        res['is_order_to_invoice'] = True
        return res

    def create_invoices(self):
        if self.invoice_ids:
            raise UserError(_('Invoice is already created '))
        self._create_invoices(self)
        return self.action_view_invoice()

    def _create_invoices(self, grouped=False, final=False):
        res = super(SaleOrder, self)._create_invoices()
        return res

class LandingCost(models.Model):
    _name = 'sale.landing.cost'
    _description = 'Sale Landing Cost'

    sale_id = fields.Many2one(comodel_name='sale.order', string="sale Order", ondelete='cascade')
    name = fields.Char(string="B/L No", required=True)
    landing_date_etd = fields.Date(string='ETD', required=True)
    landing_date_eta = fields.Date(string='ETA', required=True)
    shipping_company_id = fields.Many2one('shipment.company', string='Shipping Line', required=True,
                                          )
    landing_attachment = fields.Binary(string='Document', attachment=True)
    landing_attachment_name = fields.Char(string='Document Name')
    no_of_packages = fields.Char(string='No Of Packages')
    destination = fields.Many2one(comodel_name='res.destination', string='Destination')
    marks = fields.Char(string="Marks")
    container_no = fields.Char(string="Container No")
    reference = fields.Char(string="Order Number")
    status = fields.Selection([('in_transit', 'In Transit'), ('discharged', 'Discharged')], string='Status')

class SalesShipment(models.Model):
    _name = 'sale.shipment'

    shipment_to = fields.Many2one(comodel_name='shipment.destination', string="Shipment To")
    shipment_from = fields.Many2one(comodel_name='shipment.destination', string="Shipment From")
    from_date = fields.Date(string='Dispatch Date', copy=False, default=fields.Date.today(), store=True)
    courier_company = fields.Many2one(comodel_name='courier.company', string="Courier Company")
    airway_bill_number = fields.Char(string='Airway Bill No')
    to_date = fields.Date(string='Expected Delivery Date', copy=False, store=True)
    reference = fields.Char(string="Airway Bill Number")
    description = fields.Char(string="Description")
    status = fields.Selection([('sent', 'Sent'), ('received', 'Received'), ('delivered', 'Delivered'),
                               ('cancel', 'Canceled')],
                              string='Status')
    type = fields.Selection([('sample_customer', 'Sample received from customer'),
                             ('sample_vendor', 'Samples sent to supplier'),
                             ('vendor_sample_customer', 'Supplier initial Sample'),
                             ('sample_company', ' Supplier final samples to Customer'),
                             ('sample_to_mastex','Supplier final samples to Mastex'),
                             ('receive_document_suppler','Receive documents from supplier'),
                             ('send_document_customer','Send documents to customer'),
                             ('others', ' Others')],
                            string='Type')
    attachment = fields.Binary(string="Files", attachment=True)
    attachment_name = fields.Char(string="File Name")
    sale_id = fields.Many2one('sale.order', string="Sale Order", ondelete='cascade')

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    actual_qty = fields.Float(string='Actual Quantity', required=True
                              , default=0.0, copy=False)
    purchase_order_line_id = fields.Many2one("purchase.order.line", string='Purchase Order Line')
    actual_net_amount = fields.Float(string='Actual NetAmount', compute='_compute_actual_net')
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string='Invoice Status', compute='_compute_invoice_status', store=True, readonly=True, default='no')


    @api.onchange('')
    def product_uom_change(self):
        res = res = super(SaleOrderLine, self).product_uom_change()
        return res


    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res.update({'quantity': self.actual_qty})
        return res

    @api.depends('actual_qty', 'price_unit')
    def _compute_actual_net(self):
        for record in self:
            record.actual_net_amount = record.actual_qty * record.price_unit

    @api.onchange('actual_qty')
    def _onchange_actual_qty(self):
        if self.purchase_order_line_id:
            self.purchase_order_line_id.actual_qty = self.actual_qty

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
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                
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

    @api.model
    def create(self, vals):
        if vals['order_id']:
            order = self.env['sale.order'].search([('id', '=', vals['order_id'])], limit=1)
            product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
            if order:
                if order.state == "sale" and vals['product_id'] != int(product_id):
                    raise UserError(_("You can not Create an order line once the sales order is confirmed."))
        return super(SaleOrderLine, self).create(vals)


class ResInsurance(models.Model):
    _name = 'res.insurance'

    name = fields.Char("Name", required=True)


class ResMarks(models.Model):
    _name = 'res.marks'

    name = fields.Char("Name", required=True)


class ResDestination(models.Model):
    _name = 'res.destination'

    name = fields.Char("Name", required=True)


class ResCurrency(models.Model):
    _inherit = "res.currency"

    name = fields.Char("Currency", size=8)
