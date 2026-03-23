
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
import datetime


class PharmacyCashTransfer(models.Model):
    _name = 'pharmacy.cash.transfer'
    _description = 'Cash Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    # ---------------------------- BASIC DETAILS -------------------------------
    # Unique reference for the cash transfer, automatically generated via sequence
    name = fields.Char(
        default=lambda self: self.env['ir.sequence'].next_by_code('pharmacy.cash.transfer'),
        readonly=True
    )

    # -------------------------- FROM ACCOUNT DETAILS --------------------------
    # The account from which money will be transferred
    from_account_id = fields.Many2one('pharmacy.cash.account', string="From Account")

    # Currency type of the source account (derived from the related account)
    from_currency_type = fields.Selection(
        related='from_account_id.currency_type',
        store=True
    )


    # Cashier responsible for the source account
    from_cashier_id = fields.Many2one('pharmacy.cashier', string="From Cashier")

    # Current balance of the source account (read-only)
    from_account_balance = fields.Float(
        string="Account Balance",
        related='from_account_id.balance',
        readonly=True,
        store=True
    )

    # Type of the source account
    from_account_type = fields.Selection([
        ('main', 'Main'),
        ('marco', 'Marco'),
        ('bagram', 'Bagram'),
        ('cashier', 'Cashier'),
    ], string="Account Type", required=True)

    # -------------------------- TO ACCOUNT DETAILS ----------------------------
    # The account to which money will be transferred
    to_account_id = fields.Many2one('pharmacy.cash.account', string="To Account")

    # Currency type of the destination account (derived from the related account)
    to_currency_type = fields.Selection(
        related='to_account_id.currency_type',
        store=True,
        readonly=True
    )


    # Cashier responsible for the destination account
    to_cashier_id = fields.Many2one('pharmacy.cashier', string="To Cashier")

    # Current balance of the destination account (read-only)
    to_account_balance = fields.Float(
        string="Account Balance",
        related='to_account_id.balance',
        readonly=True,
        store=True
    )

    # Type of the destination account
    to_account_type = fields.Selection([
        ('main', 'Main'),
        ('marco', 'Marco'),
        ('bagram', 'Bagram'),
        ('cashier', 'Cashier'),
    ], string="Account Type", required=True)

    # ---------------------------- TRANSFER DETAILS ---------------------------
    # Amount to be transferred
    amount = fields.Float(required=True)
    date = fields.Date(default=fields.Date.today)
    note = fields.Text()
    status = fields.Selection(
        [
            ('new_transfer', 'New Transfer'),  # Newly created transfer
            ('transfer_done', 'Transfer Done'),  # Transfer has been completed
        ],
        string='Status',
        default='new_transfer',
        required=True,
        tracking=True
    )

    transfer_month = fields.Selection(
        [
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ],
        string="Month",
        compute="_compute_year_month",
        store=True
    )

    transfer_year = fields.Selection(
        selection=lambda self: [(str(y), str(y)) for y in
                                range(datetime.date.today().year - 10, datetime.date.today().year + 1)],
        string="Year",
        compute="_compute_year_month",
        store=True
    )

    @api.depends('date')
    def _compute_year_month(self):
        for rec in self:
            if rec.date:
                rec.transfer_month = str(rec.date.month)
                rec.transfer_year = str(rec.date.year)
            else:
                rec.transfer_month = False
                rec.transfer_year = False

    @api.constrains('from_account_id', 'to_account_id')
    def _check_accounts(self):
        for rec in self:
            if rec.from_account_id == rec.to_account_id:
                raise ValidationError("Source and destination accounts must be different.")

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("Amount must be greater than zero.")

    @api.constrains('from_account_id', 'to_account_id', 'amount')
    def _check_transfer_rules(self):
        for rec in self:
            if not rec.from_account_id or not rec.to_account_id:
                continue

            # ❌ Same account
            if rec.from_account_id.id == rec.to_account_id.id:
                raise ValidationError(
                    "You cannot transfer cash to the same account."
                )

            # ❌ Different currency
            if rec.from_currency_type != rec.to_currency_type:
                raise ValidationError(
                    "Currency mismatch. Source and destination accounts must have the same currency."
                )

            # ❌ Invalid amount
            if rec.amount <= 0:
                raise ValidationError(
                    "Transfer amount must be greater than zero."
                )

            # ❌ Insufficient balance
            if rec.from_account_id.balance < rec.amount:
                raise ValidationError(
                    "Insufficient balance in the source account."
                )

    def action_transfer_done(self):
        for rec in self:
            if rec.status == 'transfer_done':
                continue

            from_account = rec.from_account_id
            to_account = rec.to_account_id

            # Double safety (important)
            if from_account.balance < rec.amount:
                raise ValidationError(
                    "Insufficient balance in the source account."
                )

            # 🔄 Balance update
            from_account.balance -= rec.amount
            to_account.balance += rec.amount

            from_account.last_update = fields.Datetime.now()
            to_account.last_update = fields.Datetime.now()

            rec.status = 'transfer_done'