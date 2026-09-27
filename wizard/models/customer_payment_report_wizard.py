from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CustomerPaymentReportWizard(models.TransientModel):
    _name = 'customer.payment.report.wizard'
    _description = 'Customer Payment Report Wizard'

    # Filters
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    customer_id = fields.Many2one(
        'pharmacy.partner',
        string="Customer",
        domain=[('partner_type', '=', 'customer')]
    )

    # Totals
    total_sale = fields.Monetary(string="Total Sale", readonly=True)
    total_payment = fields.Monetary(string="Total Payment", readonly=True)
    total_due = fields.Monetary(string="Total Due", readonly=True)
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id.id,
        readonly=True,
        required=True
    )

    # Payment details lines
    payment_lines = fields.One2many(
        'customer.payment.report.line',
        'wizard_id',
        string="Payment Details",
        readonly=True
    )

    # -----------------------------
    # Validation
    # -----------------------------
    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError("End Date cannot be earlier than Start Date.")

    # -----------------------------
    # Build payment domain
    # -----------------------------
    def _get_domain(self):
        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('partner_type', '=', 'customer'),
            ('payment_status', '=', 'done')
        ]
        if self.customer_id:
            domain.append(('partner_id', '=', self.customer_id.id))
        return domain

    # -----------------------------
    # Generate Report
    # -----------------------------
    def generate_report(self):
        self.ensure_one()
        Payment = self.env['pharmacy.payment']
        payments = Payment.search(self._get_domain(), order='date asc')

        # Remove previous lines
        self.payment_lines.unlink()

        total_sale = 0.0
        total_payment = 0.0

        # Loop through unique customers
        customers = payments.mapped('partner_id')
        for cust in customers:
            # Total sale
            customer_sales = self.env['pharmacy.sale'].search([
                ('customer_id', '=', cust.id),
                ('status', '=', 'sale_done')
            ])
            sale_total = sum(customer_sales.mapped('total'))

            # Payments in date range
            customer_payments = payments.filtered(lambda p: p.partner_id == cust)
            payment_total = sum(customer_payments.mapped('amount'))

            # Create report lines safely
            for pay in customer_payments:
                self.env['customer.payment.report.line'].create({
                    'wizard_id': self.id,
                    'date': pay.date,
                    'partner_id': pay.partner_id.id if pay.partner_id else False,
                    'account_id': pay.to_account_id.id if pay.to_account_id else False,
                    'amount': pay.amount or 0.0,
                    'note': pay.note or '',
                    'currency_id': self.currency_id.id,
                })

            total_sale += sale_total
            total_payment += payment_total

        # Update totals
        self.total_sale = total_sale
        self.total_payment = total_payment
        self.total_due = total_sale - total_payment

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'customer.payment.report.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    # -----------------------------
    # Print PDF Report
    # -----------------------------
    def print_pdf_report(self):
        self.ensure_one()
        self.generate_report()
        return self.env.ref('pharmacy.action_customer_payment_report').report_action(self)


class CustomerPaymentReportLine(models.TransientModel):
    _name = 'customer.payment.report.line'
    _description = 'Customer Payment Report Line'
    # _rec_name = 'partner_id'  # ensures display name in One2many

    wizard_id = fields.Many2one(
        'customer.payment.report.wizard',
        string="Wizard",
        ondelete='cascade'
    )
    date = fields.Date(string="Date")
    partner_id = fields.Many2one('pharmacy.partner', string="Customer")
    account_id = fields.Many2one('pharmacy.cash.account', string="Cash Account")
    amount = fields.Monetary(string="Amount", currency_field='currency_id')
    note = fields.Text(string="Note")
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id.id
    )