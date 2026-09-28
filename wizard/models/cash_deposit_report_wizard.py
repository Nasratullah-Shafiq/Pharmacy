from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CashDepositReportWizard(models.TransientModel):
    _name = 'cash.deposit.report.wizard'
    _description = 'Cash Deposit Report Wizard'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    cash_account_id = fields.Many2one(
        'pharmacy.cash.account',
        string="Cash Account"
    )

    # Currency-wise totals
    total_afn = fields.Monetary(
        string="Total Afghani Deposit",
        readonly=True,
        currency_field='currency_afn_id'
    )
    total_usd = fields.Monetary(
        string="Total USD Deposit",
        readonly=True,
        currency_field='currency_usd_id'
    )
    total_kld = fields.Monetary(
        string="Total Kaldar Deposit",
        readonly=True,
        currency_field='currency_kld_id'
    )

    currency_afn_id = fields.Many2one(
        'res.currency',
        string="AFN Currency",
        default=lambda self: self.env['res.currency'].search([('name', '=', 'AFN')], limit=1),
        readonly=True
    )

    currency_usd_id = fields.Many2one(
        'res.currency',
        string="USD Currency",
        default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')], limit=1),
        readonly=True
    )

    currency_kld_id = fields.Many2one(
        'res.currency',
        string="KLD Currency",
        default=lambda self: self.env['res.currency'].search([('name', '=', 'KLD')], limit=1),
        readonly=True
    )

    deposit_lines = fields.One2many(
        'cash.deposit.report.line',
        'wizard_id',
        string="Deposit Details",
        readonly=True
    )

    # -----------------------------
    # Validations
    # -----------------------------
    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError("End Date cannot be earlier than Start Date.")

    # -----------------------------
    # Domain Builder
    # -----------------------------
    def _get_domain(self):
        self.ensure_one()

        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]

        if self.cash_account_id:
            domain.append(('cash_account_id', '=', self.cash_account_id.id))

        return domain

    # -----------------------------
    # Generate Report
    # -----------------------------
    def generate_report(self):
        self.ensure_one()

        deposits = self.env['pharmacy.cash.deposit'].search(
            self._get_domain(),
            order='date asc'
        )

        # Clear previous lines
        self.deposit_lines.unlink()

        # Initialize totals
        total_afn = 0.0
        total_usd = 0.0
        total_kld = 0.0

        for dep in deposits:
            currency = False

            if dep.currency_type == 'afn':
                currency = self.currency_afn_id
                total_afn += dep.amount
            elif dep.currency_type == 'usd':
                currency = self.currency_usd_id
                total_usd += dep.amount
            elif dep.currency_type == 'kaldar':
                currency = self.currency_kld_id
                total_kld += dep.amount

            self.env['cash.deposit.report.line'].create({
                'wizard_id': self.id,
                'date': dep.date,
                'cash_account_id': dep.cash_account_id.id,
                'account_type': dep.account_type,
                'amount': dep.amount,
                'user_id': dep.user_id.id,
                'currency_id': currency.id if currency else False,
                'note': dep.note,
            })

        # Set totals
        self.total_afn = total_afn
        self.total_usd = total_usd
        self.total_kld = total_kld

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    # -----------------------------
    # PDF Report
    # -----------------------------
    def print_pdf_report(self):
        self.generate_report()
        return self.env.ref('pharmacy.action_cash_deposit_report').report_action(self)


class CashDepositReportLine(models.TransientModel):
    _name = 'cash.deposit.report.line'
    _description = 'Cash Deposit Report Line'

    wizard_id = fields.Many2one(
        'cash.deposit.report.wizard',
        ondelete='cascade'
    )

    date = fields.Datetime(string="Date")

    cash_account_id = fields.Many2one(
        'pharmacy.cash.account',
        string="Account No"
    )

    account_type = fields.Selection([
        ('main', 'Main Account'),
        ('cashier', 'Cashier Account'),
    ], string="Cash Account Type")

    amount = fields.Monetary(
        string="Amount",
        currency_field='currency_id'
    )

    user_id = fields.Many2one(
        'res.users',
        string="Deposited By"
    )

    note = fields.Text(string="Note")

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency"
    )