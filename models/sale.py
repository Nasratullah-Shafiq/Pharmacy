from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PharmacySale(models.Model):
    _name = 'pharmacy.sale'
    _description = 'Pharmacy Sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ---------------------------
    # Basic Sale Information
    # ---------------------------
    date = fields.Date(string="Date", required=True, default=fields.Date.today)

    product_id = fields.Many2one('pharmacy.product', string='Product', required=True)
    product_type = fields.Selection(
        related='product_id.product_type',
        string="Product Type",
        store=True,
        readonly=True,
        tracking=True
    )

    quantity = fields.Integer(string="Quantity for Sale", default=1, required=True)
    sale_price = fields.Monetary(string="Sale Price", currency_field='currency_id', required=True)
    purchase_price = fields.Monetary(string='Purchase Price', currency_field='currency_id', readonly=True)

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
        default=lambda self: self.env.ref('uom.product_uom_unit')
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.ref('pharmacy.currency_afn')
    )

    customer_id = fields.Many2one(
        'pharmacy.partner',
        string="Customer",
        domain="[('partner_type','=','customer')]",
        context={'default_partner_type': 'customer'},
        required=True
    )

    # ---------------------------
    # Computed Fields
    # ---------------------------
    total = fields.Monetary(
        currency_field='currency_id',
        compute='_compute_total',
        string="Total",
        store=True
    )

    available_quantity = fields.Integer(
        string="Available Quantity",
        compute='_compute_available_quantity',
        store=True
    )

    status = fields.Selection(
        [('new', 'New Sale'), ('sale_done', 'Sale Done')],
        string="Status",
        default='new',
        tracking=True
    )

    # ---------------------------
    # Actions
    # ---------------------------
    def action_sale_done(self):
        """Confirm the sale and subtract stock once."""
        for rec in self:
            if rec.total <= 0:
                raise ValidationError("Sale total must be greater than zero.")

            if rec.quantity <= 0:
                raise ValidationError("Sale quantity must be greater than zero.")

            if rec.status != 'sale_done':
                rec._update_stock(subtract=True)
                rec.status = 'sale_done'

    # ---------------------------
    # Constraints & Validations
    # ---------------------------
    @api.constrains('customer_id')
    def _check_customer(self):
        for rec in self:
            if not rec.customer_id:
                raise UserError("Customer is required. Please select a customer.")

    @api.constrains('sale_price')
    def _check_sale_price(self):
        for rec in self:
            if rec.sale_price <= 0:
                raise ValidationError("Unit price must be greater than zero.")

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            latest_purchase = self.env['pharmacy.purchase'].search(
                [('product_id', '=', self.product_id.id)],
                order='date desc, id desc',
                limit=1
            )
            self.purchase_price = latest_purchase.purchase_price if latest_purchase else 0
        else:
            self.purchase_price = 0

    @api.depends('product_id')
    def _compute_available_quantity(self):
        for rec in self:
            if rec.product_id:
                stock = self.env['pharmacy.stock'].search([
                    ('product_id', '=', rec.product_id.id)
                ], limit=1)
                rec.available_quantity = stock.total_quantity if stock else 0
            else:
                rec.available_quantity = 0

    @api.depends('quantity', 'sale_price')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.quantity * rec.sale_price

    # ---------------------------
    # Create / Write Overrides
    # ---------------------------
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        # Stock will only be subtracted when sale is marked done
        return rec

    def write(self, vals):
        old_quantities = {rec.id: rec.quantity for rec in self}
        old_products = {rec.id: rec.product_id for rec in self}
        old_statuses = {rec.id: rec.status for rec in self}

        res = super().write(vals)

        for rec in self:
            old_qty = old_quantities.get(rec.id, 0)
            old_product = old_products.get(rec.id)
            old_status = old_statuses.get(rec.id)

            # If sale is still new, no stock has been deducted yet
            if rec.status == 'new':
                continue

            # If already confirmed sale is edited, restore old stock then subtract new stock
            if old_status == 'sale_done':
                rec._update_stock(
                    old_qty=old_qty,
                    old_product=old_product,
                    subtract=True
                )

        return res

    # ---------------------------
    # Stock Management
    # ---------------------------
    def _update_stock(self, old_qty=0, old_product=None, subtract=True):
        """
        Update stock safely:
        - Restore old stock if record was edited after confirmation
        - Subtract new stock only when confirming or re-confirming edited sale
        """
        for rec in self:
            # Restore old stock if editing a confirmed sale
            if old_product and old_qty > 0:
                old_stock = self.env['pharmacy.stock'].search([
                    ('product_id', '=', old_product.id)
                ], limit=1)

                if old_stock:
                    old_stock.total_quantity += old_qty

            # Current stock
            stock = self.env['pharmacy.stock'].search([
                ('product_id', '=', rec.product_id.id)
            ], limit=1)

            if not stock:
                raise UserError("No stock found for this product!")

            if subtract:
                if stock.total_quantity < rec.quantity:
                    raise ValidationError(
                        f"Not enough stock for product '{rec.product_id.name}'. "
                        f"Available: {stock.total_quantity}, Requested: {rec.quantity}"
                    )

                stock.total_quantity -= rec.quantity