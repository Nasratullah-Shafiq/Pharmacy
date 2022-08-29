# from odoo import models, fields, api
# from odoo.exceptions import ValidationError, UserError
#
#
#
# class PoultryPartner(models.Model):
#     _name = 'poultry.partner'
#     _description = 'Partner (Customer/Supplier)'
#
#     name = fields.Char(string="Name", required=True)
#     partner_type = fields.Selection([
#         ('customer', 'Customer'),
#         ('supplier', 'Supplier')
#     ], string="Partner Type", required=True)
#     email = fields.Char(string="Email")
#     phone = fields.Char(string="Phone")
#     address = fields.Text(string="Address")
#     note = fields.Text(string="Notes")
#
#     # CUSTOMER SALES
#     sale_ids = fields.One2many('poultry.sale', 'customer_id', string='Sales')
#
#     # SUPPLIER PURCHASES
#     purchase_ids = fields.One2many('poultry.purchase', 'supplier_id', string='Purchases')
#
#
#     payment_ids = fields.One2many('poultry.payment', 'partner_id', string='Payments')
#
#
#     # ACCOUNTING FIELDS
#     currency_id = fields.Many2one(
#         'res.currency',
#         string='Currency',
#         default=lambda self: self.env.company.currency_id,
#         required=True
#     )
#
#     total_amount = fields.Monetary(
#         string="Total Amount",
#         currency_field='currency_id',
#         compute="_compute_accounting",
#         store=True
#     )
#
#     amount_paid = fields.Monetary(
#         string="Amount Paid",
#         currency_field='currency_id',
#         compute="_compute_accounting",
#         store=True
#     )
#
#     amount_due = fields.Monetary(
#         string="Amount Due",
#         currency_field='currency_id',
#         compute="_compute_accounting",
#         store=True
#     )
#
#     # COMPUTE METHOD
#
#     @api.depends('sale_ids.total', 'purchase_ids.total', 'payment_ids.amount')
#     def _compute_amounts(self):
#
#         for partner in self:
#             if partner.partner_type == 'customer':
#                 total = sum(partner.sale_ids.mapped('total'))
#                 paid = sum(
#                     partner.payment_ids.filtered(
#                         lambda p: p.partner_type == 'customer'
#                     ).mapped('amount')
#                 )
#             elif partner.partner_type == 'supplier':
#                 total = sum(partner.purchase_ids.mapped('total'))
#                 paid = sum(
#                     partner.payment_ids.filtered(
#                         lambda p: p.partner_type == 'supplier'
#                     ).mapped('amount')
#                 )
#             else:
#                 total = 0
#                 paid = 0
#             partner.total_amount = total
#             partner.amount_paid = paid
#             partner.amount_due = total - paid
#
#
#


from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError



class PharmacyPartner(models.Model):
    _name = 'pharmacy.partner'
    _description = 'Partner (Customer/Supplier)'

    name = fields.Char(string="Name", required=True)
    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Supplier')
    ], string="Partner Type", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    address = fields.Text(string="Address")
    note = fields.Text(string="Notes")

    # CUSTOMER SALES
    sale_ids = fields.One2many('pharmacy.sale', 'customer_id', string='Sales')

    # SUPPLIER PURCHASES
    purchase_ids = fields.One2many('pharmacy.purchase', 'supplier_id', string='Purchases')


    payment_ids = fields.One2many('pharmacy.payment', 'partner_id', string='Payments')


    # ACCOUNTING FIELDS
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    total_amount = fields.Monetary(
        string="Total Amount",
        currency_field='currency_id',
        compute="_compute_accounting",
        store=True
    )

    amount_paid = fields.Monetary(
        string="Amount Paid",
        currency_field='currency_id',
        compute="_compute_accounting",
        store=True
    )

    amount_due = fields.Monetary(
        string="Amount Due",
        currency_field='currency_id',
        compute="_compute_accounting",
        store=True
    )

    # COMPUTE METHOD

    @api.depends('sale_ids.total', 'purchase_ids.total', 'payment_ids.amount')
    def _compute_amounts(self):

        for partner in self:
            if partner.partner_type == 'customer':
                total = sum(partner.sale_ids.mapped('total'))
                paid = sum(
                    partner.payment_ids.filtered(
                        lambda p: p.partner_type == 'customer'
                    ).mapped('amount')
                )
            elif partner.partner_type == 'supplier':
                total = sum(partner.purchase_ids.mapped('total'))
                paid = sum(
                    partner.payment_ids.filtered(
                        lambda p: p.partner_type == 'supplier'
                    ).mapped('amount')
                )
            else:
                total = 0
                paid = 0
            partner.total_amount = total
            partner.amount_paid = paid
            partner.amount_due = total - paid
