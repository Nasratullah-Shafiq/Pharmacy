from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PharmacyPurchaseReport(models.TransientModel):
    _name = 'pharmacy.purchase.report'
    _description = 'Pharmacy Purchase Report Wizard'

    # -------------------------------------------------
    # Filters
    # -------------------------------------------------
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    # -------------------------------------------------
    # Totals
    # -------------------------------------------------
    total_quantity = fields.Float(string="Total Quantity", readonly=True)
    total_amount = fields.Monetary(string="Total Purchase", readonly=True)

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )

    purchase_lines = fields.One2many(
        'pharmacy.purchase.report.line',
        'wizard_id',
        string="Purchase Details",
        readonly=True
    )

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------
    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError("End Date cannot be earlier than Start Date.")

    # -------------------------------------------------
    # Domain Builder
    # -------------------------------------------------
    def _get_domain(self):
        self.ensure_one()
        return [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]

    # -------------------------------------------------
    # Main Logic
    # -------------------------------------------------
    def generate_report(self):
        self.ensure_one()

        domain = self._get_domain()
        purchases = self.env['pharmacy.purchase'].search(domain, order='date asc')

        # Clear previous lines safely
        if self.purchase_lines:
            self.purchase_lines.unlink()

        total_qty = 0.0
        total_amount = 0.0

        for purchase in purchases:
            self.env['pharmacy.purchase.report.line'].create({
                'wizard_id': self.id,
                'date': purchase.date,
                'product_type': purchase.product_type,
                'quantity': purchase.quantity,
                'unit_price': purchase.purchase_price,
                'total': purchase.total,
                'supplier_id': purchase.supplier_id.id if purchase.supplier_id else False,
                'currency_id': self.currency_id.id,
            })

            total_qty += purchase.quantity or 0.0
            total_amount += purchase.total or 0.0

        self.write({
            'total_quantity': total_qty,
            'total_amount': total_amount,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    # -------------------------------------------------
    # PDF
    # -------------------------------------------------
    def print_pdf_report(self):
        self.generate_report()
        return self.env.ref('pharmacy.action_pharmacy_purchase_report').report_action(self)


class PharmacyPurchaseReportLine(models.TransientModel):
    _name = 'pharmacy.purchase.report.line'
    _description = 'Pharmacy Purchase Report Line'

    wizard_id = fields.Many2one(
        'pharmacy.purchase.report',
        string="Wizard",
        ondelete='cascade'
    )

    date = fields.Date(string="Date")

    product_type = fields.Selection([
        ('medicine', 'Medicine'),
        ('equipment', 'Equipment'),
        ('supply', 'Supply'),
        ('other', 'Other'),
    ], string="Product Type")

    quantity = fields.Float(string="Quantity")
    unit_price = fields.Monetary(string="Unit Price", currency_field='currency_id')
    total = fields.Monetary(string="Total", currency_field='currency_id')

    supplier_id = fields.Many2one('pharmacy.partner', string="Supplier")

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )