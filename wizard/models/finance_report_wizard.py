from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PharmacyFinanceReport(models.TransientModel):
    _name = 'pharmacy.finance.report'
    _description = 'Comprehensive Pharmacy Finance Report Wizard'

    # -------------------------------------------------
    # Filters
    # -------------------------------------------------
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    # -------------------------------------------------
    # Totals
    # -------------------------------------------------
    total_sales = fields.Monetary(string="Total Sales", readonly=True)
    total_purchases = fields.Monetary(string="Total Purchases", readonly=True)
    total_salaries = fields.Monetary(string="Total Salaries", readonly=True)
    total_expenses = fields.Monetary(string="Total Expenses", readonly=True)
    total_income = fields.Monetary(string="Total Income", readonly=True)

    total_expense_by_type = fields.Monetary(string="Total Expenses (All Types)", readonly=True)
    total_expense_by_type_text = fields.Text(string="Expense Breakdown", readonly=True)

    net_profit = fields.Monetary(string="Net Profit", readonly=True)

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------
    def _validate_dates(self):
        if not self.start_date or not self.end_date:
            raise UserError(_("Please provide both start and end dates."))
        if self.start_date > self.end_date:
            raise UserError(_("Start date cannot be after end date."))

    # -------------------------------------------------
    # Domain Builder
    # -------------------------------------------------
    def _get_domain(self, date_field='date'):
        return [
            (date_field, '>=', self.start_date),
            (date_field, '<=', self.end_date),
        ]

    # -------------------------------------------------
    # Calculations
    # -------------------------------------------------
    def _calculate_sales(self):
        return self._sum_model('pharmacy.sale', self._get_domain('date'), 'total')

    def get_sales_by_customer(self):
        domain = self._get_domain('date')
        sales = self.env['pharmacy.sale'].search(domain)

        totals = {}

        for rec in sales:
            customer = rec.customer_id.name if rec.customer_id else "Unknown Customer"
            totals[customer] = totals.get(customer, 0) + rec.total

        return [{'customer': k, 'amount': v} for k, v in totals.items()]

    def _calculate_purchases(self):
        return self._sum_model('pharmacy.purchase', self._get_domain('date'), 'total')

    def get_purchase_by_supplier(self):
        domain = self._get_domain('date')
        purchases = self.env['pharmacy.purchase'].search(domain)

        totals = {}

        for rec in purchases:
            supplier = rec.supplier_id.name if rec.supplier_id else "Unknown Supplier"
            totals[supplier] = totals.get(supplier, 0) + rec.total

        return [{'supplier': k, 'amount': v} for k, v in totals.items()]

    def _calculate_salaries(self):
        self._validate_dates()

        payment_domain = [
            ('salary_date', '>=', self.start_date),
            ('salary_date', '<=', self.end_date),
        ]

        payments = self.env['salary.payment'].search(payment_domain)
        return sum(payments.mapped('amount'))

    def get_salary_by_employee(self):
        domain = [
            ('salary_date', '>=', self.start_date),
            ('salary_date', '<=', self.end_date),
        ]

        payments = self.env['salary.payment'].search(domain)

        totals = {}

        for rec in payments:
            employee = rec.employee_id.name if rec.employee_id else "Unknown Employee"
            totals[employee] = totals.get(employee, 0) + rec.amount

        return [{'employee': k, 'amount': v} for k, v in totals.items()]

    def _calculate_expenses(self):
        domain = self._get_domain('date')
        domain.append(('expense_status', '=', 'done'))

        expenses = self.env['pharmacy.expense'].search(domain)
        return sum(expenses.mapped('amount'))

    def get_expense_breakdown(self):
        domain = self._get_domain('date')
        domain.append(('expense_status', '=', 'done'))

        expenses = self.env['pharmacy.expense'].search(domain)

        totals = {}

        for exp in expenses:
            name = exp.expense_type_id.name if exp.expense_type_id else "Other"
            totals[name] = totals.get(name, 0) + exp.amount

        lines = []
        for k, v in totals.items():
            lines.append({
                'type': k,
                'amount': v
            })

        return lines

    def _calculate_income(self):
        return self._calculate_sales() - self._calculate_purchases()

    # -------------------------------------------------
    # Expense by Type
    # -------------------------------------------------
    def _compute_total_expense_by_type(self):
        for rec in self:
            rec.total_expense_by_type = 0.0
            rec.total_expense_by_type_text = ""

            if not rec.start_date or not rec.end_date:
                continue

            domain = [
                ('date', '>=', rec.start_date),
                ('date', '<=', rec.end_date),
                ('expense_status', '=', 'done'),
            ]

            expenses = self.env['pharmacy.expense'].search(domain)

            totals = {}
            total_amount = 0.0

            for exp in expenses:
                name = exp.expense_type_id.name if exp.expense_type_id else "Other"
                totals[name] = totals.get(name, 0.0) + exp.amount
                total_amount += exp.amount

            rec.total_expense_by_type = total_amount
            rec.total_expense_by_type_text = "\n".join(
                f"{k}: {v:.2f}" for k, v in totals.items()
            )

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def _sum_model(self, model_name, domain, field_name):
        grouped = self.env[model_name].read_group(domain, [field_name], [])
        return grouped[0][field_name] if grouped else 0.0

    # -------------------------------------------------
    # Main Logic
    # -------------------------------------------------
    def generate_report(self):
        self._validate_dates()

        self.total_sales = self._calculate_sales()
        self.total_purchases = self._calculate_purchases()
        self.total_salaries = self._calculate_salaries()
        self.total_expenses = self._calculate_expenses()
        self.total_income = self._calculate_income()

        self._compute_total_expense_by_type()

        # Correct formula (no double counting)
        self.net_profit = (
            self.total_sales
            - self.total_purchases
            - self.total_salaries
            - self.total_expenses
        )

    # -------------------------------------------------
    # Onchange
    # -------------------------------------------------
    @api.onchange('start_date', 'end_date')
    def _onchange_generate_report(self):
        if self.start_date and self.end_date:
            self.generate_report()

    # -------------------------------------------------
    # Buttons
    # -------------------------------------------------
    def compute_report(self):
        self.generate_report()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def print_pdf_report(self):
        self.ensure_one()
        self.generate_report()
        return self.env.ref(
            'pharmacy.action_pharmacy_finance_report'
        ).report_action(self)