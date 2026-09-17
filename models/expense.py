
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import datetime


class PharmacyExpense(models.Model):
    _name = 'pharmacy.expense'
    _description = 'Pharmacy Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Expense Description", required=True, tracking=True)

    cash_account_id = fields.Many2one(
        'pharmacy.cash.account',
        string="Main Cash Account",
        readonly=True,
        tracking=True
    )

    cash_balance = fields.Float(
        string="Current Cash Balance",
        related='cash_account_id.balance',
        readonly=True,
        store=False
    )

    expense_type_id = fields.Many2one(
        'pharmacy.expense.type',
        string="Expense Type",
        required=True,
        tracking=True
    )

    amount = fields.Float(string="Amount", required=True, tracking=True)

    date = fields.Date(
        string="Date",
        default=fields.Date.today,
        required=True,
        tracking=True
    )

    user_id = fields.Many2one(
        'res.users',
        string="Recorded By",
        default=lambda self: self.env.user,
        readonly=True
    )

    note = fields.Text(string="Note")

    expense_status = fields.Selection(
        [
            ('new', 'New Expense'),
            ('done', 'Expense Done')
        ],
        string="Expense Status",
        default='new',
        tracking=True
    )

    # -------------------------
    # Search Panel / Filters
    # -------------------------
    expense_month = fields.Selection(
        [
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ],
        string="Month",
        compute="_compute_year_month",
        store=True
    )

    expense_year = fields.Selection(
        selection="_get_year_selection",
        string="Year",
        compute="_compute_year_month",
        store=True
    )

    # -------------------------
    # Business Actions
    # -------------------------
    def action_expense_done(self):
        for rec in self:
            if rec.expense_status != 'done':
                rec.write({'expense_status': 'done'})

    # -------------------------
    # Validations
    # -------------------------
    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("Expense amount must be greater than zero!")

    # -------------------------
    # Compute Month / Year
    # -------------------------
    @api.depends('date')
    def _compute_year_month(self):
        for rec in self:
            if rec.date:
                rec.expense_month = str(rec.date.month)
                rec.expense_year = str(rec.date.year)
            else:
                rec.expense_month = False
                rec.expense_year = False

    def _get_year_selection(self):
        current_year = datetime.date.today().year
        return [(str(y), str(y)) for y in range(current_year - 10, current_year + 1)]

    # -------------------------
    # Main Cash Account Helper
    # -------------------------
    def _get_main_cash_account(self):
        """
        Fetch the main cash account.
        Priority:
        1. is_main = True   (recommended if your model has this field)
        2. fallback to first available account
        """
        CashAccount = self.env['pharmacy.cash.account']

        # Preferred: if your cash account model has is_main field
        if 'is_main' in CashAccount._fields:
            main_account = CashAccount.search([('is_main', '=', True)], limit=1)
            if main_account:
                return main_account

        # Fallback: first available cash account
        main_account = CashAccount.search([], limit=1)

        if not main_account:
            raise ValidationError("No main cash account found. Please create a main cash account first.")

        return main_account

    # -------------------------
    # Create
    # -------------------------
    @api.model
    def create(self, vals):
        # Validate amount
        amount = vals.get('amount', 0.0)
        if amount <= 0:
            raise ValidationError("Expense amount must be greater than zero.")

        # Get main cash account automatically
        main_account = self._get_main_cash_account()

        # Check available balance
        if main_account.balance < amount:
            raise ValidationError(
                f"Insufficient balance in main cash account '{main_account.name}'. "
                f"Available balance is {main_account.balance}."
            )

        # Set cash account automatically
        vals['cash_account_id'] = main_account.id

        # Deduct amount from main cash account
        main_account.write({
            'balance': main_account.balance - amount,
            'last_update': fields.Datetime.now()
        })

        # Create expense
        return super(PharmacyExpense, self).create(vals)

class PharmacyExpenseType(models.Model):
    _name = "pharmacy.expense.type"
    _description = "Expense Type"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Expense Type", required=True, tracking=True)


    _sql_constraints = [
        ("unique_name", "unique(name)", "Expense Type name must be unique!")
    ]
