from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PharmacySaleReportWizard(models.TransientModel):
    _name = 'pharmacy.sale.report.wizard'
    _description = 'Pharmacy Sale Report Wizard'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    total_quantity = fields.Float(
        string="Total Quantity",
        readonly=True
    )

    total_revenue = fields.Monetary(
        string="Total Sale",
        readonly=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )

    sale_lines = fields.One2many(
        'pharmacy.sale.report.line',
        'wizard_id',
        string="Sale Details",
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
    # Domain Builder
    # -----------------------------
    def _get_domain(self):
        self.ensure_one()
        return [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ]

    # -----------------------------
    # Generate Report
    # -----------------------------
    def generate_report(self):
        self.ensure_one()

        sales = self.env['pharmacy.sale'].search(self._get_domain(), order='date asc')

        # Remove previous report lines
        if self.sale_lines:
            self.sale_lines.unlink()

        total_qty = 0.0
        total_revenue = 0.0

        for sale in sales:
            self.env['pharmacy.sale.report.line'].create({
                'wizard_id': self.id,
                'date': sale.date,
                'product_type': sale.product_type,
                'quantity': sale.quantity,
                'unit_price': sale.sale_price,
                'total': sale.total,
                'customer_id': sale.customer_id.id if sale.customer_id else False,
                'currency_id': self.currency_id.id,
            })

            total_qty += sale.quantity or 0.0
            total_revenue += sale.total or 0.0

        self.write({
            'total_quantity': total_qty,
            'total_revenue': total_revenue,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pharmacy.sale.report.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    # -----------------------------
    # Print PDF
    # -----------------------------
    def print_pdf_report(self):
        self.generate_report()
        return self.env.ref('pharmacy.action_pharmacy_sale_report').report_action(self)


class PharmacySaleReportLine(models.TransientModel):
    _name = 'pharmacy.sale.report.line'
    _description = 'Pharmacy Sale Report Line'

    wizard_id = fields.Many2one(
        'pharmacy.sale.report.wizard',
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

    unit_price = fields.Monetary(
        string="Unit Price",
        currency_field='currency_id'
    )

    total = fields.Monetary(
        string="Total",
        currency_field='currency_id'
    )

    customer_id = fields.Many2one(
        'pharmacy.partner',
        string="Customer"
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )