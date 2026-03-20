# from odoo import models, fields, api
# from odoo.exceptions import UserError, ValidationError
# from datetime import date, datetime, timedelta
# import datetime
#
#
#
# class PoultryPayment(models.Model):
#
#     _name = 'poultry.payment'
#     _description = 'Partner Payment'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#     _order = 'date desc'
#
#     # PARTNER INFO
#
#     partner_type = fields.Selection(related='partner_id.partner_type', store=True)
#     date = fields.Date(default=fields.Date.today, required=True)
#     amount = fields.Float(required=True)
#     note = fields.Text()
#
#     # CASH ACCOUNT
#
#     state = fields.Selection([('draft', 'Draft'),('posted', 'Posted')], default='draft')
#     partner_id = fields.Many2one(
#         'poultry.partner',
#         required=True,
#         domain="[('partner_type', '=', partner_type)]"
#     )
#
#     to_account_id = fields.Many2one('poultry.cash.account', required=True, string="To Account")
#
#     to_currency_type = fields.Selection(related='to_account_id.currency_type', store=True, readonly=True)
#     to_branch_id = fields.Many2one('poultry.branch', string="Branch", related='to_account_id.branch_id', store=True)
#     to_cashier_id = fields.Many2one('poultry.cashier', string="To Cashier")
#     to_account_balance = fields.Float(string="Account Balance", related='to_account_id.balance', readonly=True,
#                                       store=True)
#     to_account_type = fields.Selection(
#         [('main', 'Main'), ('marco', 'Marco'), ('bagram', 'Bagram'), ('cashier', 'Cashier')],
#         string="Account Type", required=True)
#
#     payment_status = fields.Selection([('new', 'New Payment'),('done', 'Payment Done')], default='new', tracking=True )
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
#         compute="_compute_partner_balance",
#         store=True
#     )
#
#     amount_paid = fields.Monetary(
#         string="Amount Paid",
#         currency_field='currency_id',
#         compute="_compute_partner_balance",
#         store=True
#     )
#
#     amount_due = fields.Monetary(
#         string="Amount Due",
#         currency_field='currency_id',
#         compute="_compute_partner_balance",
#         store=True
#     )
#     payment_month = fields.Selection(
#         [
#             ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
#             ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
#             ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
#         ],
#         string="Month",
#         compute="_compute_payment_year_month",
#         store=True,
#         index=True
#     )
#
#     payment_year = fields.Selection(
#         selection=lambda self: [(str(y), str(y)) for y in range(
#             datetime.date.today().year - 10,
#             datetime.date.today().year + 1
#         )],
#         string="Year",
#         compute="_compute_payment_year_month",
#         store=True,
#         index=True
#     )
#
#     # =======================
#     # CONSTRAINT: Amount > 0
#     # =======================
#     @api.constrains('amount')
#     def _check_amount_positive(self):
#         for rec in self:
#             if rec.amount <= 0:
#                 raise ValidationError("Payment amount must be greater than 0!")
#
#     @api.depends('date')
#     def _compute_payment_year_month(self):
#         for rec in self:
#             if rec.date:
#                 rec.payment_month = str(rec.date.month)
#                 rec.payment_year = str(rec.date.year)
#             else:
#                 rec.payment_month = False
#                 rec.payment_year = False
#
#     @api.depends('partner_id')
#     def _compute_partner_balance(self):
#
#         for rec in self:
#
#             total_amount = 0
#             total_paid = 0
#
#             if not rec.partner_id:
#                 rec.total_amount = 0
#                 rec.amount_paid = 0
#                 rec.amount_due = 0
#                 continue
#
#             # -------------------------
#             # CUSTOMER
#             # -------------------------
#
#             if rec.partner_id.partner_type == 'customer':
#
#                 sales = self.env['poultry.sale'].search([
#                     ('customer_id', '=', rec.partner_id.id),
#                     ('status', '=', 'sale_done')
#                 ])
#                 total_amount = sum(sales.mapped('total'))
#
#             # -------------------------
#             # SUPPLIER
#             # -------------------------
#
#             elif rec.partner_id.partner_type == 'supplier':
#
#                 purchases = self.env['poultry.purchase'].search([
#                     ('supplier_id', '=', rec.partner_id.id),
#                     ('status', '=', 'purchase_done')
#                 ])
#
#                 total_amount = sum(purchases.mapped('total'))
#
#             # -------------------------
#             # PAYMENTS (COMMON)
#             # -------------------------
#
#             payments = self.env['poultry.payment'].search([
#                 ('partner_id', '=', rec.partner_id.id),
#                 ('payment_status', '=', 'done')
#             ])
#
#             total_paid = sum(payments.mapped('amount'))
#
#             # -------------------------
#             # FINAL VALUES
#             # -------------------------
#
#             rec.total_amount = total_amount
#             rec.amount_paid = total_paid
#             rec.amount_due = total_amount - total_paid
#
#     # ======================
#     # POST PAYMENT
#     # ======================
#
#     def action_payment_done(self):
#         for rec in self:
#             # --- Validate positive amount ---
#             if rec.amount <= 0:
#                 raise ValidationError("Payment amount must be greater than 0!")
#
#             # --- Validate customer has debt ---
#             if rec.partner_type == 'customer' and rec.amount_due <= 0:
#                 raise ValidationError(
#                     f"Customer {rec.partner_id.name} has no outstanding debt. Payment not allowed."
#                 )
#
#             # --- Apply payment ---
#             if rec.partner_type == 'customer':
#                 rec.to_account_id.balance += rec.amount
#             elif rec.partner_type == 'supplier':
#                 rec.to_account_id.balance -= rec.amount
#
#             rec.payment_status = 'done'
#
#     def write(self, vals):
#
#         for rec in self:
#             old_amount = rec.amount
#             old_account = rec.to_account_id
#             res = super().write(vals)
#             if rec.payment_status == 'done':
#                 diff = rec.amount - old_amount
#                 if rec.partner_type == 'customer':
#                     old_account.balance += diff
#                 else:
#                     old_account.balance -= diff
#             return res
#


from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
import datetime



class PharmacyPayment(models.Model):

    _name = 'pharmacy.payment'
    _description = 'Partner Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    # PARTNER INFO

    partner_type = fields.Selection(related='partner_id.partner_type', store=True)
    date = fields.Date(default=fields.Date.today, required=True)
    amount = fields.Float(required=True)
    note = fields.Text()

    # CASH ACCOUNT

    state = fields.Selection([('draft', 'Draft'),('posted', 'Posted')], default='draft')
    partner_id = fields.Many2one(
        'pharmacy.partner',
        required=True,
        domain="[('partner_type', '=', partner_type)]"
    )

    to_account_id = fields.Many2one('pharmacy.cash.account', required=True, string="To Account")

    to_currency_type = fields.Selection(related='to_account_id.currency_type', store=True, readonly=True)
    to_cashier_id = fields.Many2one('pharmacy.cashier', string="To Cashier")
    to_account_balance = fields.Float(string="Account Balance", related='to_account_id.balance', readonly=True,
                                      store=True)
    to_account_type = fields.Selection(
        [('main', 'Main'), ('marco', 'Marco'), ('bagram', 'Bagram'), ('cashier', 'Cashier')],
        string="Account Type", required=True)

    payment_status = fields.Selection([('new', 'New Payment'),('done', 'Payment Done')], default='new', tracking=True )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    total_amount = fields.Monetary(
        string="Total Amount",
        currency_field='currency_id',
        compute="_compute_partner_balance",
        store=True
    )

    amount_paid = fields.Monetary(
        string="Amount Paid",
        currency_field='currency_id',
        compute="_compute_partner_balance",
        store=True
    )

    amount_due = fields.Monetary(
        string="Amount Due",
        currency_field='currency_id',
        compute="_compute_partner_balance",
        store=True
    )
    payment_month = fields.Selection(
        [
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ],
        string="Month",
        compute="_compute_payment_year_month",
        store=True,
        index=True
    )

    payment_year = fields.Selection(
        selection=lambda self: [(str(y), str(y)) for y in range(
            datetime.date.today().year - 10,
            datetime.date.today().year + 1
        )],
        string="Year",
        compute="_compute_payment_year_month",
        store=True,
        index=True
    )

    # =======================
    # CONSTRAINT: Amount > 0
    # =======================
    @api.constrains('amount')
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("Payment amount must be greater than 0!")

    @api.depends('date')
    def _compute_payment_year_month(self):
        for rec in self:
            if rec.date:
                rec.payment_month = str(rec.date.month)
                rec.payment_year = str(rec.date.year)
            else:
                rec.payment_month = False
                rec.payment_year = False

    @api.depends('partner_id')
    def _compute_partner_balance(self):

        for rec in self:

            total_amount = 0
            total_paid = 0

            if not rec.partner_id:
                rec.total_amount = 0
                rec.amount_paid = 0
                rec.amount_due = 0
                continue

            # -------------------------
            # CUSTOMER
            # -------------------------

            if rec.partner_id.partner_type == 'customer':

                sales = self.env['pharmacy.sale'].search([
                    ('customer_id', '=', rec.partner_id.id),
                    ('status', '=', 'sale_done')
                ])
                total_amount = sum(sales.mapped('total'))

            # -------------------------
            # SUPPLIER
            # -------------------------

            elif rec.partner_id.partner_type == 'supplier':

                purchases = self.env['pharmacy.purchase'].search([
                    ('supplier_id', '=', rec.partner_id.id),
                    ('status', '=', 'purchase_done')
                ])

                total_amount = sum(purchases.mapped('total'))

            # -------------------------
            # PAYMENTS (COMMON)
            # -------------------------

            payments = self.env['pharmacy.payment'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('payment_status', '=', 'done')
            ])

            total_paid = sum(payments.mapped('amount'))

            # -------------------------
            # FINAL VALUES
            # -------------------------

            rec.total_amount = total_amount
            rec.amount_paid = total_paid
            rec.amount_due = total_amount - total_paid

    # ======================
    # POST PAYMENT
    # ======================

    def action_payment_done(self):
        for rec in self:
            # --- Validate positive amount ---
            if rec.amount <= 0:
                raise ValidationError("Payment amount must be greater than 0!")

            # --- Validate customer has debt ---
            if rec.partner_type == 'customer' and rec.amount_due <= 0:
                raise ValidationError(
                    f"Customer {rec.partner_id.name} has no outstanding debt. Payment not allowed."
                )

            # --- Apply payment ---
            if rec.partner_type == 'customer':
                rec.to_account_id.balance += rec.amount
            elif rec.partner_type == 'supplier':
                rec.to_account_id.balance -= rec.amount

            rec.payment_status = 'done'

    def write(self, vals):

        for rec in self:
            old_amount = rec.amount
            old_account = rec.to_account_id
            res = super().write(vals)
            if rec.payment_status == 'done':
                diff = rec.amount - old_amount
                if rec.partner_type == 'customer':
                    old_account.balance += diff
                else:
                    old_account.balance -= diff
            return res