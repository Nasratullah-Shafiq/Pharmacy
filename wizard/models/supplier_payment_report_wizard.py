from odoo import models, fields, api
from odoo.exceptions import ValidationError

# ==========================================
# Supplier Payment Report Wizard
# ==========================================
class SupplierPaymentReportWizard(models.TransientModel):
    _name = 'supplier.payment.report.wizard'
    _description = 'Supplier Payment Report Wizard'

    # Filter fields
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    supplier_id = fields.Many2one(
        'pharmacy.partner',
        string="Supplier",
        domain=[('partner_type', '=', 'supplier')]
    )

    # Totals
    total_purchase = fields.Monetary(string="Total Purchase", readonly=True)
    total_payment = fields.Monetary(string="Total Paid", readonly=True)
    total_due = fields.Monetary(string="Total Due", readonly=True)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )

    # Report lines
    payment_lines = fields.One2many(
        'supplier.payment.report.line',
        'wizard_id',
        string="Payment Details",
        readonly=True
    )

    # -----------------------------
    # Validation: Ensure end_date >= start_date
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
        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('partner_type', '=', 'supplier'),
            ('payment_status', '=', 'done')
        ]
        if self.supplier_id:
            domain.append(('partner_id', '=', self.supplier_id.id))
        return domain

    # -----------------------------
    # Generate Report
    # -----------------------------
    def generate_report(self):
        self.ensure_one()
        Payment = self.env['pharmacy.payment']
        payments = Payment.search(self._get_domain(), order='date asc')

        # Clear previous report lines
        self.payment_lines.unlink()
        total_payment = 0.0
        total_purchase = 0.0

        # Loop through unique suppliers
        suppliers = payments.mapped('partner_id')
        for sup in suppliers:
            # Calculate total purchase for this supplier
            supplier_purchases = self.env['pharmacy.purchase'].search([
                ('supplier_id', '=', sup.id),
                ('status', '=', 'purchase_done')
            ])
            purchase_total = sum(supplier_purchases.mapped('total'))

            # Calculate total payments in date range
            supplier_payments = payments.filtered(lambda p: p.partner_id == sup)
            payment_total = sum(supplier_payments.mapped('amount'))

            # Create report lines
            for pay in supplier_payments:
                self.env['supplier.payment.report.line'].create({
                    'wizard_id': self.id,
                    'date': pay.date,
                    'supplier_id': pay.partner_id.id,
                    'account_id': pay.to_account_id.id,
                    'amount': pay.amount,
                    'note': pay.note,
                    'total_purchase': purchase_total,
                })

            total_payment += payment_total
            total_purchase += purchase_total

        # Update totals in wizard
        self.total_payment = total_payment
        self.total_purchase = total_purchase
        self.total_due = total_purchase - total_payment

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.payment.report.wizard',
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
        return self.env.ref('pharmacy.action_supplier_payment_report').report_action(self)
# pharmacy.report_supplier_payment_template

# ==========================================
# Supplier Payment Report Lines
# ==========================================
class SupplierPaymentReportLine(models.TransientModel):
    _name = 'supplier.payment.report.line'
    _description = 'Supplier Payment Report Line'

    wizard_id = fields.Many2one(
        'supplier.payment.report.wizard',
        ondelete='cascade'
    )
    date = fields.Date(string="Date")
    supplier_id = fields.Many2one('pharmacy.partner', string="Supplier")
    account_id = fields.Many2one('pharmacy.cash.account', string="Cash Account")
    amount = fields.Monetary(string="Paid Amount", currency_field='currency_id')
    total_purchase = fields.Monetary(string="Total Purchase", currency_field='currency_id')
    note = fields.Text(string="Note")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)