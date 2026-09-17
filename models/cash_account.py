from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


# ==========================================
# Pharmacy Cash Account
# ==========================================
class PharmacyCashAccount(models.Model):
    _name = "pharmacy.cash.account"
    _description = "Pharmacy Cash Account"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'account_no'

    account_no = fields.Char(string="Account No", readonly=True)
    balance = fields.Float(string="Cash Balance", tracking=True, default=0.0)

    account_type = fields.Selection([
        ('main', 'Main Account'),
        ('cashier', 'Cashier Account'),
    ], string="Account Type", required=True, tracking=True)

    cashier_id = fields.Many2one('pharmacy.cashier', string="Cashier")

    last_update = fields.Datetime(string="Last Updated", default=fields.Datetime.now)

    currency_type = fields.Selection([
        ('usd', 'USD'),
        ('afn', 'AFN'),
        ('kaldar', 'Kaldar')
    ], string="Currency", required=True, default='afn', tracking=True)

    deposit_ids = fields.One2many('pharmacy.cash.deposit', 'cash_account_id', string="Deposits")
    expense_ids = fields.One2many('pharmacy.expense', 'cash_account_id', string='Expenses')

    status = fields.Selection(
        [('new_account', 'New Account'), ('account_created', 'Account Created')],
        string="Status",
        default='new_account',
        tracking=True
    )

    def action_mark_created(self):
        for rec in self:
            rec.status = 'account_created'

    @api.constrains('account_type', 'cashier_id', 'currency_type')
    def _check_unique_currency_account(self):
        for rec in self:
            # Main account: only one per currency
            if rec.account_type == 'main':
                domain = [
                    ('id', '!=', rec.id),
                    ('account_type', '=', 'main'),
                    ('currency_type', '=', rec.currency_type),
                ]

                if self.search_count(domain):
                    raise ValidationError(
                        f"A Main account with currency {rec.currency_type.upper()} already exists."
                    )

            # Cashier account: only one per cashier + currency
            if rec.account_type == 'cashier':
                if not rec.cashier_id:
                    raise ValidationError("Cashier account must have a cashier.")

                domain = [
                    ('id', '!=', rec.id),
                    ('cashier_id', '=', rec.cashier_id.id),
                    ('currency_type', '=', rec.currency_type),
                    ('account_type', '=', 'cashier'),
                ]

                if self.search_count(domain):
                    raise ValidationError(
                        f"Cashier '{rec.cashier_id.name}' already has a {rec.currency_type.upper()} account."
                    )

    @api.model
    def create(self, vals):
        # Generate account number for Main account
        if vals.get('account_type') == 'main' and vals.get('currency_type'):
            currency_order = {'usd': 1, 'afn': 2, 'kaldar': 3}[vals['currency_type']]
            currency_code = 'KLD' if vals['currency_type'] == 'kaldar' else vals['currency_type'].upper()

            vals['account_no'] = f"M{str(currency_order).zfill(3)}{currency_code}"

        # Generate account number for Cashier account
        elif vals.get('account_type') == 'cashier' and vals.get('cashier_id') and vals.get('currency_type'):
            cashier = self.env['pharmacy.cashier'].browse(vals['cashier_id'])
            if not cashier.exists():
                raise ValidationError("Invalid cashier selected.")

            cashier_code = (cashier.name or 'XXX')[:3].upper()
            currency_order = {'usd': 1, 'afn': 2, 'kaldar': 3}[vals['currency_type']]
            currency_code = 'KLD' if vals['currency_type'] == 'kaldar' else vals['currency_type'].upper()

            vals['account_no'] = f"{cashier_code}{str(currency_order).zfill(3)}{currency_code}"

        return super().create(vals)


# ==========================================
# Pharmacy Cash Deposit
# ==========================================
class PharmacyCashDeposit(models.Model):
    _name = "pharmacy.cash.deposit"
    _description = "Cash Deposit to Pharmacy Account"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    cash_account_id = fields.Many2one('pharmacy.cash.account', string="Account No", required=True)
    amount = fields.Float(string="Deposit Amount", required=True)
    date = fields.Datetime(string="Deposit Date", default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string="Deposited By", default=lambda self: self.env.user)

    cashier_id = fields.Many2one('pharmacy.cashier', string="From Cashier")

    account_type = fields.Selection([
        ('main', 'Main Account'),
        ('cashier', 'Cashier Account'),
    ], string="Account Type", required=True)

    currency_type = fields.Selection(
        related='cash_account_id.currency_type',
        store=True,
        readonly=True
    )

    note = fields.Text(string="Note")

    deposit_month = fields.Selection(
        [(str(i), m) for i, m in enumerate(
            ['January', 'February', 'March', 'April', 'May', 'June',
             'July', 'August', 'September', 'October', 'November', 'December'], 1)],
        string="Month",
        compute="_compute_year_month",
        store=True
    )

    deposit_year = fields.Selection(
        selection="_get_year_selection",
        string="Year",
        compute="_compute_year_month",
        store=True
    )

    status = fields.Selection(
        [('new_deposit', 'New Deposit'), ('deposit_done', 'Deposit Done')],
        string='Status',
        default='new_deposit',
        required=True,
        tracking=True
    )

    @api.depends('date')
    def _compute_year_month(self):
        for rec in self:
            if rec.date:
                rec.deposit_month = str(rec.date.month)
                rec.deposit_year = str(rec.date.year)
            else:
                rec.deposit_month = False
                rec.deposit_year = False

    def _get_year_selection(self):
        current_year = datetime.today().year
        return [(str(y), str(y)) for y in range(current_year - 10, current_year + 1)]

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("Deposit amount must be greater than 0!")

    def action_deposit_done(self):
        for rec in self:
            rec.status = 'deposit_done'

    @api.model
    def create(self, vals):
        record = super().create(vals)
        account = record.cash_account_id

        if not account:
            raise ValidationError("No Cash Account found for the selected Account Type.")

        account.balance += record.amount
        account.last_update = fields.Datetime.now()
        return record