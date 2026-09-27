from odoo import models, fields, api
from odoo.exceptions import ValidationError


# ==========================================
# Wizard for Pharmacy Cash Account Report
# ==========================================
class PharmacyCashAccountReportWizard(models.TransientModel):
    _name = 'pharmacy.cash.account.report.wizard'
    _description = 'Pharmacy Cash Account Report Wizard'

    # Filter by account type
    account_type = fields.Selection([
        ('main', 'Main Account'),
        ('cashier', 'Cashier Account'),
    ], string="Cash Account Type")

    # Totals per currency
    total_afn = fields.Float(string="Total AFN", readonly=True)
    total_usd = fields.Float(string="Total USD", readonly=True)
    total_kaldar = fields.Float(string="Total Kaldar", readonly=True)

    # Deposit lines
    deposit_lines = fields.One2many(
        'pharmacy.cash.account.report.line',
        'wizard_id',
        string="Deposit Details",
        readonly=True
    )

    # -----------------------------
    # Generate Report
    # -----------------------------
    def generate_report(self):
        self.ensure_one()

        # Remove previous lines
        self.deposit_lines.unlink()

        total_afn = 0.0
        total_usd = 0.0
        total_kaldar = 0.0

        # Filter accounts by type
        domain = []
        if self.account_type:
            domain = [('account_type', '=', self.account_type)]

        accounts = self.env['pharmacy.cash.account'].search(domain)

        for account in accounts:
            for deposit in account.deposit_ids:
                self.env['pharmacy.cash.account.report.line'].create({
                    'wizard_id': self.id,
                    'date': deposit.date,
                    'account_no': account.account_no,
                    'account_type': account.account_type,
                    'currency_type': deposit.currency_type,
                    'amount': deposit.amount,
                    'user_id': deposit.user_id.id,
                    'note': deposit.note,
                })
                # Sum totals per currency
                if deposit.currency_type == 'afn':
                    total_afn += deposit.amount
                elif deposit.currency_type == 'usd':
                    total_usd += deposit.amount
                elif deposit.currency_type == 'kaldar':
                    total_kaldar += deposit.amount

        self.total_afn = total_afn
        self.total_usd = total_usd
        self.total_kaldar = total_kaldar

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    # -----------------------------
    # Print PDF Report
    # -----------------------------
    def print_pdf_report(self):
        self.generate_report()
        return self.env.ref('pharmacy.action_pharmacy_cash_account_report').report_action(self)


# ==========================================
# Wizard Lines for Pharmacy Cash Account
# ==========================================
class PharmacyCashAccountReportLine(models.TransientModel):
    _name = 'pharmacy.cash.account.report.line'
    _description = 'Pharmacy Cash Account Report Line'

    wizard_id = fields.Many2one('pharmacy.cash.account.report.wizard', ondelete='cascade')
    date = fields.Datetime(string="Deposit Date")
    account_no = fields.Char(string="Account No")
    account_type = fields.Selection([
        ('main', 'Main Account'),
        ('cashier', 'Cashier Account'),
    ], string="Account Type")
    currency_type = fields.Selection([
        ('afn', 'AFN'),
        ('usd', 'USD'),
        ('kaldar', 'Kaldar'),
    ], string="Currency")
    amount = fields.Float(string="Amount")
    user_id = fields.Many2one('res.users', string="Deposited By")
    note = fields.Text(string="Note")