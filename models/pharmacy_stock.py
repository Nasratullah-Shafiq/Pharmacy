from odoo import models, fields, api
from odoo.exceptions import UserError

#
# class PoultryProduct(models.Model):
#     _name = 'poultry.product'
#     _description = 'Product'
#     _rec_name = 'name'
#     _inherit = ['mail.thread', 'mail.activity.mixin']  # Enable chatter
#
#     name = fields.Char(string="Item", required=True)
#     purchase_cost = fields.Monetary(
#         string="Purchase Cost",
#         currency_field='currency_id',
#         tracking=True,
#         help="Average or last purchase cost"
#     )
#
#     sale_price = fields.Monetary(
#         string="Sale Price",
#         currency_field='currency_id',
#         tracking=True
#     )
#     product_type = fields.Selection([
#         ('chicken', 'Chicken'),
#         ('feed', 'Feed'),
#         ('medicine', 'Medicine'),
#     ], string="Product Type", required=True, tracking=True, default='medicine')
#
#     currency_id = fields.Many2one(
#         'res.currency',
#         string="Currency",
#         default=lambda self: self.env.company.currency_id,
#         required=True
#     )
#
#     description = fields.Text(string="Description")
#     product_status = fields.Selection(
#         [
#             ('new', 'New Product'),
#             ('saved', 'Saved Product')
#         ],
#         default='new',
#         tracking=True
#     )
#
#     def action_product_saved(self):
#         for record in self:
#             record.product_status = 'saved'
#
#
# class PoultryStock(models.Model):
#     _name = 'poultry.stock'
#     _description = 'Poultry Stock Overview'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#
#     branch_id = fields.Many2one('poultry.branch', string='Branch', required=True)
#
#     product_type = fields.Selection(related='product_id.product_type', store=True)
#     farm_id = fields.Many2one('poultry.farm.house', string='Farm', required=True)
#     product_id = fields.Many2one('poultry.product', string="Product", required=True, ondelete='cascade', tracking=True)
#
#     expiry_date = fields.Date(string="Expiry Date", tracking=True)
#     cost = fields.Monetary(string="Cost", currency_field='currency_id', tracking=True)
#     sale_price = fields.Monetary(string="Sale Price", currency_field='currency_id', tracking=True)
#     cost_amount = fields.Monetary(string="Cost Amount", store=True, currency_field='currency_id')
#     price_amount = fields.Monetary(string="Price Amount", store=True, currency_field='currency_id')
#     currency_id = fields.Many2one(
#         'res.currency',
#         string="Currency",
#         default=lambda self: self.env.company.currency_id,
#         required=True
#     )
#
#     total_quantity = fields.Integer(string="Current Quantity", default=0, tracking=True)
#     uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True,
#                              default=lambda self: self.env.ref('uom.product_uom_unit'))
#     last_updated = fields.Datetime(string="Last Updated", default=fields.Datetime.now)
#
#     @api.model
#     def create(self, vals):
#         """Override create to update stock after record creation"""
#         rec = super(PoultryStock, self).create(vals)
#         rec._update_stock()
#         return rec
#
#     def _update_stock(self):
#         """Update total_quantity by adding purchases and subtracting deaths"""
#         for record in self:
#             # Total purchased quantity for this branch and item type
#             purchases = self.env['poultry.purchase'].search([
#                 ('branch_id', '=', record.branch_id.id),
#                 # ('item_type_id', '=', record.item_type_id.id)
#             ])
#             total_purchased = sum(p.quantity for p in purchases)
#
#             # Total deaths for this branch and item type
#             deaths = self.env['poultry.death'].search([
#                 ('branch_id', '=', record.branch_id.id),
#                 # ('item_type_id', '=', record.item_type_id.id)
#             ])
#             total_deaths = sum(d.quantity for d in deaths)
#
#             # Calculate net stock
#             net_quantity = total_purchased - total_deaths
#             if net_quantity < 0:
#                 net_quantity = 0  # prevent negative stock
#
#             record.total_quantity = net_quantity
#             record.last_updated = fields.Datetime.now()




class PharmacyProduct(models.Model):
    _name = 'pharmacy.product'
    _description = 'Product'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Enable chatter

    name = fields.Char(string="Item", required=True)
    purchase_cost = fields.Monetary(
        string="Purchase Cost",
        currency_field='currency_id',
        tracking=True,
        help="Average or last purchase cost"
    )

    sale_price = fields.Monetary(
        string="Sale Price",
        currency_field='currency_id',
        tracking=True
    )
    product_type = fields.Selection([
        ('medicine', 'Medicine'),
        ('equipment', 'Equipment'),
        ('consumable', 'Consumable'),
    ], string="Product Type", required=True, tracking=True, default='medicine')

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    description = fields.Text(string="Description")
    product_status = fields.Selection(
        [
            ('new', 'New Product'),
            ('saved', 'Saved Product')
        ],
        default='new',
        tracking=True
    )

    def action_product_saved(self):
        for record in self:
            record.product_status = 'saved'


class PharmacyStock(models.Model):
    _name = 'pharmacy.stock'
    _description = 'Pharmacy Stock Overview'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    product_type = fields.Selection(related='product_id.product_type', store=True)
    pharmacy_id = fields.Many2one('pharmacy.store', string='Pharmacy', required=True)
    product_id = fields.Many2one('pharmacy.product', string="Product", required=True, ondelete='cascade', tracking=True)

    expiry_date = fields.Date(string="Expiry Date", tracking=True)
    cost = fields.Monetary(string="Cost", currency_field='currency_id', tracking=True)
    sale_price = fields.Monetary(string="Sale Price", currency_field='currency_id', tracking=True)
    cost_amount = fields.Monetary(string="Cost Amount", store=True, currency_field='currency_id')
    price_amount = fields.Monetary(string="Price Amount", store=True, currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    total_quantity = fields.Integer(string="Current Quantity", default=0, tracking=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True,
                             default=lambda self: self.env.ref('uom.product_uom_unit'))
    last_updated = fields.Datetime(string="Last Updated", default=fields.Datetime.now)

    @api.model
    def create(self, vals):
        """Override create to update stock after record creation"""
        rec = super(PharmacyStock, self).create(vals)
        rec._update_stock()
        return rec

    def _update_stock(self):
        """Update total_quantity by adding purchases and subtracting consumptions/losses"""
        for record in self:
            # Total purchased quantity for this branch and product
            purchases = self.env['pharmacy.purchase'].search([
                ('branch_id', '=', record.branch_id.id),
            ])
            total_purchased = sum(p.quantity for p in purchases)

            # Total consumed/lost for this branch and product
            losses = self.env['pharmacy.loss'].search([
                ('branch_id', '=', record.branch_id.id),
            ])
            total_losses = sum(l.quantity for l in losses)

            # Calculate net stock
            net_quantity = total_purchased - total_losses
            if net_quantity < 0:
                net_quantity = 0  # prevent negative stock

            record.total_quantity = net_quantity
            record.last_updated = fields.Datetime.now()