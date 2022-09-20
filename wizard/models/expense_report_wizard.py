from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ExpenseReportWizard(models.TransientModel):
    _name = 'expense.report.wizard'
    _description = 'Expense Report Wizard'

    # Filters
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    # Summary
    total_expense_amount = fields.Float(
        string="Total Expenses",
        readonly=True
    )

    # Report lines
    expense_lines = fields.One2many(
        'expense.report.line',
        'wizard_id',
        string="Expense Details",
        readonly=True
    )

    # ----------------------------
    # Validations
    # ----------------------------
    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(
                    "End Date cannot be earlier than Start Date."
                )

    # ----------------------------
    # Domain Builder
    # ----------------------------
    def _get_domain(self):
        self.ensure_one()

        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]

        return domain

    # ----------------------------
    # Actions
    # ----------------------------
    def generate_report(self):
        self.ensure_one()

        Expense = self.env['pharmacy.expense']
        domain = self._get_domain()

        expenses = Expense.search(domain, order='date asc')

        # Clear previous data
        self.expense_lines.unlink()

        total = 0.0
        line_vals = []

        for exp in expenses:
            line_vals.append({
                'wizard_id': self.id,
                'expense_date': exp.date,
                'expense_type_id': exp.expense_type_id.id if exp.expense_type_id else False,
                'amount': exp.amount,
            })
            total += exp.amount

        if line_vals:
            self.env['expense.report.line'].create(line_vals)

        self.total_expense_amount = total

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'expense.report.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def print_pdf_report(self):
        self.generate_report()
        return self.env.ref(
            'pharmacy.action_expense_report'
        ).report_action(self)


# ======================================================
# Report Line Model
# ======================================================
class ExpenseReportLine(models.TransientModel):
    _name = 'expense.report.line'
    _description = 'Expense Report Line'

    wizard_id = fields.Many2one(
        'expense.report.wizard',
        string="Wizard",
        ondelete='cascade'
    )

    expense_date = fields.Date(string="Date")

    expense_type_id = fields.Many2one(
        'pharmacy.expense.type',
        string="Expense Type"
    )

    amount = fields.Float(string="Amount")