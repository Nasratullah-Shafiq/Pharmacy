from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PharmacyPurchase(models.Model):
    _name = 'pharmacy.purchase'
    _description = 'Pharmacy Purchase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today,
        tracking=True
    )

    product_id = fields.Many2one(
        'pharmacy.product',
        string="Product",
        required=True,
        tracking=True
    )

    product_type = fields.Selection(
        related='product_id.product_type',
        string="Product Type",
        store=True,
        readonly=True,
        tracking=True
    )

    quantity = fields.Integer(
        string="Quantity",
        default=1,
        required=True,
        tracking=True
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
        default=lambda self: self.env.ref('uom.product_uom_unit'),
        tracking=True
    )

    purchase_price = fields.Monetary(
        string="Purchase Price",
        currency_field='currency_id',
        required=True,
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.ref('pharmacy.currency_afn')
    )

    supplier_id = fields.Many2one(
        'pharmacy.partner',
        string="Supplier",
        domain="[('partner_type', '=', 'supplier')]",
        context={'default_partner_type': 'supplier'},
        required=True,
        tracking=True
    )

    total = fields.Monetary(
        string="Total",
        currency_field='currency_id',
        compute='_compute_total',
        store=True
    )

    status = fields.Selection(
        [
            ('new', 'New'),
            ('purchase_done', 'Purchase Done'),
        ],
        string='Status',
        default='new',
        required=True,
        tracking=True
    )

    # ---------------------------------
    # COMPUTE METHODS
    # ---------------------------------
    @api.depends('quantity', 'purchase_price')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.quantity * rec.purchase_price

    # ---------------------------------
    # ACTION METHODS
    # ---------------------------------
    def action_purchase_done(self):
        for rec in self:
            if rec.status == 'purchase_done':
                continue

            rec._update_stock()
            rec.status = 'purchase_done'

    # ---------------------------------
    # STOCK UPDATE LOGIC
    # ---------------------------------
    def _update_stock(self):
        stock_model = self.env['pharmacy.stock']

        for rec in self:
            stock = stock_model.search([
                ('product_id', '=', rec.product_id.id)
            ], limit=1)

            if stock:
                stock.write({
                    'total_quantity': stock.total_quantity + rec.quantity,
                    'cost_amount': stock.cost_amount + (rec.purchase_price * rec.quantity),
                    'cost': rec.purchase_price,
                    'uom_id': rec.uom_id.id,
                    'currency_id': rec.currency_id.id,
                    'last_updated': fields.Datetime.now(),
                })
            else:
                stock_model.create({
                    'product_id': rec.product_id.id,
                    'uom_id': rec.uom_id.id,
                    'cost': rec.purchase_price,
                    'cost_amount': rec.purchase_price * rec.quantity,
                    'total_quantity': rec.quantity,
                    'currency_id': rec.currency_id.id,
                    'last_updated': fields.Datetime.now(),
                })

    # ---------------------------------
    # VALIDATIONS
    # ---------------------------------
    @api.constrains('quantity', 'purchase_price')
    def _check_values(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError('Quantity must be greater than zero.')

            if rec.purchase_price <= 0:
                raise ValidationError('Purchase price must be greater than zero.')