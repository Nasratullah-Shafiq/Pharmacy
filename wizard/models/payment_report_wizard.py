from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PaymentReportWizard(models.TransientModel):
    _name = 'payment.report.wizard'
    _description = 'Payment Report Wizard'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    branch_id = fields.Many2one('poultry.branch', string="Branch")

    partner_type = fields.Selection([('customer','Customer'),('supplier','Supplier')], string="Partner Type")
    # partner_id = fields.Many2one('poultry.partner')
    customer_id = fields.Many2one('poultry.partner', string="Customer")
    supplier_id = fields.Many2one('poultry.partner', string="Supplier")

    total_amount = fields.Monetary(string="Total Paid", readonly=True)
    total_transaction = fields.Monetary(string="Total Transaction", readonly=True)
    total_due = fields.Monetary(string="Total Due", readonly=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, readonly=True)

    payment_lines = fields.One2many('payment.report.line', 'wizard_id', string="Payment Lines", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx_type = self.env.context.get('default_partner_type')
        if ctx_type:
            res['partner_type'] = ctx_type
        return res

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        if self.partner_type == 'customer':
            self.customer_id = False
            self.supplier_id = False
        elif self.partner_type == 'supplier':
            self.customer_id = False
            self.supplier_id = False

    @api.constrains('start_date','end_date')
    def _check_date_range(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError("End Date cannot be earlier than Start Date.")

    def _get_domain(self):
        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('partner_type','=',self.partner_type),
            ('payment_status','=','done')
        ]
        if self.branch_id:
            domain.append(('to_branch_id','=',self.branch_id.id))
        if self.partner_id:
            domain.append(('partner_id','=',self.partner_id.id))
        return domain


    def generate_report(self):
        self.ensure_one()
        Payment = self.env['poultry.payment']
        payments = Payment.search(self._get_domain(), order='date asc')
        self.payment_lines.unlink()

        total_payment = 0.0
        total_transaction = 0.0

        partners = payments.mapped('partner_id')
        for p in partners:
            partner_payments = payments.filtered(lambda pay: pay.partner_id == p)

            # Calculate transaction total from sales/purchases depending on partner_type
            if self.partner_type == 'customer':
                # Total sales for this customer
                partner_transactions = self.env['poultry.sale'].search([
                    ('customer_id', '=', p.id),
                    ('status', '=', 'sale_done')
                ])
                trans_total = sum(partner_transactions.mapped('total'))  # <-- total field from sales
            else:
                # Total purchases for this supplier
                partner_transactions = self.env['poultry.purchase'].search([
                    ('supplier_id', '=', p.id),
                    ('status', '=', 'purchase_done')
                ])
                trans_total = sum(partner_transactions.mapped('total'))  # <-- total field from purchases

            pay_total = sum(partner_payments.mapped('amount'))

            # Create report lines
            for pay in partner_payments:
                self.env['payment.report.line'].create({
                    'wizard_id': self.id,
                    'date': pay.date,
                    'partner_id': pay.partner_id.id,
                    'branch_id': pay.to_branch_id.id,
                    'account_id': pay.to_account_id.id,
                    'amount': pay.amount,
                    'note': pay.note,
                    'total_transaction': trans_total,
                })

            total_transaction += trans_total
            total_payment += pay_total

        self.total_transaction = total_transaction
        self.total_amount = total_payment
        self.total_due = total_transaction - total_payment

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'payment.report.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def print_pdf_report(self):
        self.ensure_one()
        self.generate_report()
        report_ref = 'poultry_farm.action_payment_report'
        return self.env.ref(report_ref).report_action(self)


class PaymentReportLine(models.TransientModel):
    _name = 'payment.report.line'
    _description = 'Payment Report Line'

    wizard_id = fields.Many2one('payment.report.wizard', ondelete='cascade')
    date = fields.Date(string="Date")
    # partner_id = fields.Many2one('poultry.partner', string="Partner")
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Supplier')], string="Partner Type")
    customer_id = fields.Many2one('poultry.partner', string="Customer")
    supplier_id = fields.Many2one('poultry.partner', string="Supplier")
    branch_id = fields.Many2one('poultry.branch', string="Branch")
    account_id = fields.Many2one('poultry.cash.account', string="Cash Account")
    amount = fields.Monetary(string="Paid Amount", currency_field='currency_id')
    total_transaction = fields.Monetary(string="Total Transaction", currency_field='currency_id')
    note = fields.Text(string="Note")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)