# from odoo import models, fields, api
# from odoo.exceptions import UserError, ValidationError
# from datetime import date, datetime, timedelta
# import datetime
#
# class PoultryExpense(models.Model):
#     _name = 'poultry.expense'
#     _description = 'Branch Expense'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#
#     name = fields.Char(string="Expense Description", required=True)
#     branch_id = fields.Many2one('poultry.branch', string="Branch", required=True)
#     cash_account_id = fields.Many2one('poultry.cash.account', string="Cash Account", readonly=True)
#     cash_balance = fields.Float(
#         string="Current Cash Balance",
#         related='cash_account_id.balance',
#         readonly=True,
#         store=False  # you can set store=True if you want it stored in DB
#     )
#     expense_type_id = fields.Many2one('poultry.expense.type', string="Expense Type", required=True)
#     amount = fields.Float(string="Amount", required=True)
#     date = fields.Date(default=fields.Date.today)
#     user_id = fields.Many2one('res.users', string="Recorded By", default=lambda self: self.env.user)
#     note = fields.Text(string="Note")
#     expense_status = fields.Selection(
#         [('new', 'New Expense'),
#          ('done', 'Expense Done')],
#         string="Expense Status",
#         default='new',
#         tracking=True
#     )
#
#     farm_id = fields.Many2one(
#         'poultry.farm.house',
#         string="Farm",
#         domain="[('branch_id', '=', branch_id)]"
#     )
#
#     # Computed month and year for search panel
#     expense_month = fields.Selection(
#         [
#             ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
#             ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
#             ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
#         ],
#         string="Month",
#         compute="_compute_year_month",
#         store=True
#     )
#
#     expense_year = fields.Selection(
#         selection="_get_year_selection",
#         string="Year",
#         compute="_compute_year_month",
#         store=True
#     )
#
#     def action_expense_done(self):
#         for rec in self:
#             if rec.expense_status != 'done':
#                 rec.write({'expense_status': 'done'})
#
#     # Prevent saving zero or negative amounts
#     # -------------------------
#     # Onchange Methods
#     # -------------------------
#
#     @api.onchange('branch_id')
#     def _onchange_branch_id(self):
#         if self.branch_id:
#             # Check if branch has a linked cash account
#             cash_accounts = self.env['poultry.cash.account'].search([('branch_id', '=', self.branch_id.id)])
#             if not cash_accounts:
#                 # Show warning in form
#                 return {
#                     'warning': {
#                         'title': "No Cash Account!",
#                         'message': "This branch has no cash account. Please create a cash account first."
#                     }
#                 }
#             elif len(cash_accounts) == 1:
#                 # If only one cash account, auto-fill
#                 self.cash_account_id = cash_accounts.id
#             else:
#                 # Multiple accounts, let user choose
#                 self.cash_account_id = False
#
#
#
#     @api.constrains('amount')
#     def _check_amount(self):
#         for record in self:
#             if record.amount <= 0:
#                 raise ValidationError("Expense amount must be greater than 0!")
#
#     # Compute month and year from date
#     @api.depends('date')
#     def _compute_year_month(self):
#         for rec in self:
#             if rec.date:
#                 rec.expense_month = str(rec.date.month)
#                 rec.expense_year = str(rec.date.year)
#             else:
#                 rec.expense_month = False
#                 rec.expense_year = False
#
#     # Selection method for years
#     def _get_year_selection(self):
#         current_year = datetime.date.today().year
#         return [(str(y), str(y)) for y in range(current_year - 10, current_year + 1)]
#
#     @api.constrains('amount')
#     def _check_amount(self):
#         for rec in self:
#             if rec.amount <= 0:
#                 raise ValidationError("Expense amount must be greater than zero!")
#
#     @api.onchange('branch_id')
#     def _onchange_branch_id(self):
#         if self.branch_id:
#             account = self.env['poultry.cash.account'].search([('branch_id', '=', self.branch_id.id)], limit=1)
#             if account:
#                 self.cash_account_id = account.id
#
#     @api.model
#     def create(self, vals):
#         # Dynamically set cash_account_id if missing
#         if not vals.get('cash_account_id'):
#             # Example: get the cash account for the selected branch
#             if vals.get('branch_id'):
#                 cash_account = self.env['poultry.cash.account'].search([('branch_id', '=', vals['branch_id'])], limit=1)
#                 if not cash_account:
#                     raise ValidationError("No cash account found for this branch.")
#                 vals['cash_account_id'] = cash_account.id
#             else:
#                 raise ValidationError("Cash account or branch must be selected.")
#
#         # Check amount
#         if vals.get('amount', 0) <= 0:
#             raise ValidationError("Expense amount must be greater than zero.")
#
#         # Deduct from cash account
#         account = self.env['poultry.cash.account'].browse(vals['cash_account_id'])
#         if account.balance < vals['amount']:
#             raise ValidationError(f"Insufficient balance in account {account.name}.")
#
#         account.write({
#             'balance': account.balance - vals['amount'],
#             'last_update': fields.Datetime.now()
#         })
#
#         return super(PoultryExpense, self).create(vals)
#
#
# class PoultryExpenseType(models.Model):
#     _name = "poultry.expense.type"
#     _description = "Expense Type"
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#
#     name = fields.Char(string="Expense Type", required=True, tracking=True)
#
#
#     _sql_constraints = [
#         ("unique_name", "unique(name)", "Expense Type name must be unique!")
#     ]


from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
import datetime

class PharmacyExpense(models.Model):
    _name = 'pharmacy.expense'
    _description = 'Branch Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Expense Description", required=True)
    cash_account_id = fields.Many2one('pharmacy.cash.account', string="Cash Account", readonly=True)
    cash_balance = fields.Float(
        string="Current Cash Balance",
        related='cash_account_id.balance',
        readonly=True,
        store=False  # you can set store=True if you want it stored in DB
    )
    expense_type_id = fields.Many2one('pharmacy.expense.type', string="Expense Type", required=True)
    amount = fields.Float(string="Amount", required=True)
    date = fields.Date(default=fields.Date.today)
    user_id = fields.Many2one('res.users', string="Recorded By", default=lambda self: self.env.user)
    note = fields.Text(string="Note")
    expense_status = fields.Selection(
        [('new', 'New Expense'),
         ('done', 'Expense Done')],
        string="Expense Status",
        default='new',
        tracking=True
    )

    farm_id = fields.Many2one(
        'pharmacy.farm.house',
        string="Farm",
        domain="[('branch_id', '=', branch_id)]"
    )

    # Computed month and year for search panel
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

    def action_expense_done(self):
        for rec in self:
            if rec.expense_status != 'done':
                rec.write({'expense_status': 'done'})

    # Prevent saving zero or negative amounts
    # -------------------------
    # Onchange Methods
    # -------------------------

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        if self.branch_id:
            # Check if branch has a linked cash account
            cash_accounts = self.env['pharmacy.cash.account'].search([('branch_id', '=', self.branch_id.id)])
            if not cash_accounts:
                # Show warning in form
                return {
                    'warning': {
                        'title': "No Cash Account!",
                        'message': "This branch has no cash account. Please create a cash account first."
                    }
                }
            elif len(cash_accounts) == 1:
                # If only one cash account, auto-fill
                self.cash_account_id = cash_accounts.id
            else:
                # Multiple accounts, let user choose
                self.cash_account_id = False



    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError("Expense amount must be greater than 0!")

    # Compute month and year from date
    @api.depends('date')
    def _compute_year_month(self):
        for rec in self:
            if rec.date:
                rec.expense_month = str(rec.date.month)
                rec.expense_year = str(rec.date.year)
            else:
                rec.expense_month = False
                rec.expense_year = False

    # Selection method for years
    def _get_year_selection(self):
        current_year = datetime.date.today().year
        return [(str(y), str(y)) for y in range(current_year - 10, current_year + 1)]

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("Expense amount must be greater than zero!")

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        if self.branch_id:
            account = self.env['pharmacy.cash.account'].search([('branch_id', '=', self.branch_id.id)], limit=1)
            if account:
                self.cash_account_id = account.id

    @api.model
    def create(self, vals):
        # Dynamically set cash_account_id if missing
        if not vals.get('cash_account_id'):
            # Example: get the cash account for the selected branch
            if vals.get('branch_id'):
                cash_account = self.env['pharmacy.cash.account'].search([('branch_id', '=', vals['branch_id'])], limit=1)
                if not cash_account:
                    raise ValidationError("No cash account found for this branch.")
                vals['cash_account_id'] = cash_account.id
            else:
                raise ValidationError("Cash account or branch must be selected.")

        # Check amount
        if vals.get('amount', 0) <= 0:
            raise ValidationError("Expense amount must be greater than zero.")

        # Deduct from cash account
        account = self.env['pharmacy.cash.account'].browse(vals['cash_account_id'])
        if account.balance < vals['amount']:
            raise ValidationError(f"Insufficient balance in account {account.name}.")

        account.write({
            'balance': account.balance - vals['amount'],
            'last_update': fields.Datetime.now()
        })

        return super(PharmacyExpense, self).create(vals)


class PharmacyExpenseType(models.Model):
    _name = "pharmacy.expense.type"
    _description = "Expense Type"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Expense Type", required=True, tracking=True)


    _sql_constraints = [
        ("unique_name", "unique(name)", "Expense Type name must be unique!")
    ]