from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import ValidationError
import datetime


class PharmacySalary(models.Model):
    _name = 'salary.payment'
    _description = 'Employee Salary Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one(
        'pharmacy.employee', string='Employee', required=True
    )
    salary_date = fields.Date(string='Salary Date', required=True)
    amount = fields.Monetary(string='Amount To be paid', required=True)
    amount_remaining = fields.Monetary(
        string='Amount Remaining',
        compute='_compute_amount_remaining',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id.id
    )
    total_salary = fields.Monetary(
        string='Total Salary',
        related='employee_id.salary',
        store=True
    )

    payment_status = fields.Selection(
        [
            ('not_paid', 'Not Paid'),
            ('partially_paid', 'Partially Paid'),
            ('paid', 'Paid'),
        ],
        string='Payment Status',
        compute='_compute_payment_status',
        store=True
    )

    notes = fields.Text(string='Notes')

    salary_month = fields.Selection(
        [
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ],
        string="Month",
        compute="_compute_year_month",
        store=True
    )

    paid_this_month_display = fields.Monetary(
        string='',
        compute='_compute_previous_paid_amount',
        store=False  # no need to store since it’s dynamic
    )

    paid_month_label = fields.Char(
        compute='_compute_month_label',
        store=False
    )


    @api.depends('salary_date')
    def _compute_month_label(self):
        for rec in self:
            if rec.salary_date:
                month_name = rec.salary_date.strftime('%B')
                rec.paid_month_label = f"{month_name} Payment"
            else:
                rec.paid_month_label = "Paid This Month"

    # Year field as Selection
    def _get_year_selection(self):
        current_year = datetime.date.today().year
        return [(str(y), str(y)) for y in range(current_year - 10, current_year + 1)]

    salary_year = fields.Selection(
        selection=_get_year_selection,
        string="Year",
        compute="_compute_year_month",
        store=True
    )
    @api.depends('total_salary', 'amount', 'paid_this_month_display')
    def _compute_amount_remaining(self):
        for rec in self:
            # Remaining salary = total_salary - (previous paid + current payment)
            rec.amount_remaining = max(rec.total_salary - (rec.paid_this_month_display + rec.amount), 0)

    @api.depends('salary_date')
    def _compute_year_month(self):
        for rec in self:
            if rec.salary_date:
                rec.salary_year = str(rec.salary_date.year)
                rec.salary_month = str(rec.salary_date.month)
            else:
                rec.salary_year = False
                rec.salary_month = False



    @api.depends('employee_id', 'salary_date', 'amount')
    def _compute_previous_paid_amount(self):
        for rec in self:
            if not rec.employee_id or not rec.salary_date:
                rec.paid_this_month_display = 0  # <-- assign here
                rec.paid_this_month_display = "0"
                continue

            salary_date = rec.salary_date
            month_start = salary_date.replace(day=1)
            next_month = (month_start + timedelta(days=31)).replace(day=1)
            month_end = next_month - timedelta(days=1)

            # Calculate total paid in this month
            payments = self.env['salary.payment'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('salary_date', '>=', month_start),
                ('salary_date', '<=', month_end),
                ('id', '!=', rec.id or 0),
            ])

            total_paid = sum(payments.mapped('amount'))

            rec.paid_this_month_display = total_paid

            # only the number
            rec.paid_this_month_display = str(total_paid)

    @api.depends('amount_remaining', 'total_salary')
    def _compute_payment_status(self):
        for rec in self:
            total = rec.total_salary or 0
            remaining = rec.amount_remaining or 0

            if remaining == total:
                rec.payment_status = 'not_paid'
            elif remaining > 0:
                rec.payment_status = 'partially_paid'
            else:
                rec.payment_status = 'paid'


    @api.constrains('amount', 'employee_id', 'salary_date')
    def _check_salary_payment_limit(self):
        """
        Enforce per-employee, per-month salary limits:

        - Multiple partial payments are allowed within a month.
        - The month may only become "fully paid" once. If it's already fully paid,
          no new payment that keeps the month fully-paid (or overpays) is allowed.
        - Overpayments are blocked.
        """
        for rec in self:
            # skip incomplete records
            if not rec.employee_id or not rec.salary_date:
                continue

            # 0 or negative payment is not allowed
            if rec.amount <= 0:
                raise ValidationError(
                    "You cannot pay 0. Please enter an amount greater than 0."
                )
            if not rec.total_salary or rec.total_salary <= 0:
                # If total_salary is not set, block to be safe (or you can skip)
                f"Salary for {rec.employee_id.name} is not set. Please set the salary before recording a payment."

            # Compute month range
            month_start = rec.salary_date.replace(day=1)
            next_month = (month_start + timedelta(days=31)).replace(day=1)
            month_end = next_month - timedelta(days=1)

            # Existing payments in the same month for the employee (exclude current record)
            existing_payments = self.env['salary.payment'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('salary_date', '>=', month_start),
                ('salary_date', '<=', month_end),
                ('id', '!=', rec.id or 0),
            ])

            existing_sum = sum(existing_payments.mapped('amount') or [0])
            new_total = existing_sum + (rec.amount or 0)

            # 1) Overpayment not allowed
            if new_total > rec.total_salary:
                month_name = rec.salary_date.strftime('%B')
                raise ValidationError(
                    f"You cannot pay an amount greater than the total salary ({rec.total_salary})."
                )

            # 2) If month is already fully paid (existing_sum == total_salary), block any further payment
            if existing_sum == rec.total_salary:
                month_name = rec.salary_date.strftime('%B')
                raise ValidationError(
                    f"The total salary for {month_name} has already been paid for {rec.employee_id.name}."
                )