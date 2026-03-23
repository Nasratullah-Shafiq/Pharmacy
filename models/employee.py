# # poultry_farm_management/models/employee.py
# from odoo import models, fields, api
# from odoo.exceptions import UserError
# from datetime import date
#
# class PoultryEmployee(models.Model):
#     _name = 'poultry.employee'
#     _description = 'Poultry Farm Employee'
#     _inherit = ['mail.thread', 'mail.activity.mixin']  # Enable chatter
#
#     name = fields.Char(required=True)
#     employee_code = fields.Char(string='Employee Code', readonly=True, copy=False)
#     branch_id = fields.Many2one('poultry.branch', string='Branch', required=True)
#     job_title = fields.Char(string = "Job Title", required=True)
#     phone = fields.Char(string="Phone", required=True)
#     address = fields.Text()
#     hire_date = fields.Date(string="Hire Date", required=True)
#     salary = fields.Monetary(currency_field='currency_id', required=True)
#     currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
#     farm_id = fields.Many2one('poultry.farm.house', string="Farm", domain="[('branch_id', '=', branch_id)]")
#     image_1920 = fields.Image(string='Employee Photo', max_width=1920, max_height=1920)
#
#     employee_status = fields.Selection(
#         [
#             ('new', 'New Employee'),
#             ('hired', 'Hired Employee'),
#             ('fired', 'Fired Employee'),
#         ],
#         string='Employee Status',
#         compute='_compute_employee_status',
#         store=True,
#         tracking=True
#     )
#
#     # Attendance placeholder field: a simple counter or last sign-in
#     last_attendance = fields.Datetime()
#     active = fields.Boolean(default=True)
#
#     @api.depends('salary', 'active')
#     def _compute_employee_status(self):
#         for rec in self:
#             salary = rec.salary or 0.0
#
#             if not rec.active:
#                 rec.employee_status = 'fired'
#             elif salary > 0:
#                 rec.employee_status = 'hired'
#             else:
#                 rec.employee_status = 'new'
#
#     @api.constrains('salary')
#     def _check_salary_not_zero(self):
#         for rec in self:
#             if rec.salary <= 0:
#                 raise UserError(
#                     "Please assign employee salary. Salary must be greater than zero."
#                 )
#
#     @api.model
#     def create(self, vals):
#         if not vals.get('employee_code') and vals.get('name'):
#             vals['employee_code'] = self._generate_employee_code(vals['name'])
#
#         return super().create(vals)
#
#     def write(self, vals):
#         for record in self:
#             # Assign code only if missing
#             if not record.employee_code:
#                 name = vals.get('name', record.name)
#                 if name and 'employee_code' not in vals:
#                     vals['employee_code'] = self._generate_employee_code(name)
#
#         return super().write(vals)
#
#     def _generate_employee_code(self, name):
#         """
#         Example: NAS-001, NAS-002
#         Prefix = first 3 letters of employee name (no spaces, uppercase)
#         """
#         prefix = name.replace(' ', '').upper()[:3]
#
#         last_employee = self.search(
#             [('employee_code', 'like', f'{prefix}-%')],
#             order='id desc',
#             limit=1
#         )
#
#         if last_employee and last_employee.employee_code:
#             try:
#                 last_number = int(last_employee.employee_code.split('-')[1])
#             except Exception:
#                 last_number = 0
#             new_number = str(last_number + 1).zfill(3)
#         else:
#             new_number = '001'
#
#         return f'{prefix}-{new_number}'
#


# pharmacy_farm_management/models/employee.py
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date

class PharmacyEmployee(models.Model):
    _name = 'pharmacy.employee'
    _description = 'Pharmacy Farm Employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Enable chatter

    name = fields.Char(required=True)
    employee_code = fields.Char(string='Employee Code', readonly=True, copy=False)
    job_title = fields.Char(string = "Job Title", required=True)
    phone = fields.Char(string="Phone", required=True)
    address = fields.Text()
    hire_date = fields.Date(string="Hire Date", required=True)
    salary = fields.Monetary(currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    image_1920 = fields.Image(string='Employee Photo', max_width=1920, max_height=1920)

    employee_status = fields.Selection(
        [
            ('new', 'New Employee'),
            ('hired', 'Hired Employee'),
            ('fired', 'Fired Employee'),
        ],
        string='Employee Status',
        compute='_compute_employee_status',
        store=True,
        tracking=True
    )

    # Attendance placeholder field: a simple counter or last sign-in
    last_attendance = fields.Datetime()
    active = fields.Boolean(default=True)

    @api.depends('salary', 'active')
    def _compute_employee_status(self):
        for rec in self:
            salary = rec.salary or 0.0

            if not rec.active:
                rec.employee_status = 'fired'
            elif salary > 0:
                rec.employee_status = 'hired'
            else:
                rec.employee_status = 'new'

    @api.constrains('salary')
    def _check_salary_not_zero(self):
        for rec in self:
            if rec.salary <= 0:
                raise UserError(
                    "Please assign employee salary. Salary must be greater than zero."
                )

    @api.model
    def create(self, vals):
        if not vals.get('employee_code') and vals.get('name'):
            vals['employee_code'] = self._generate_employee_code(vals['name'])

        return super().create(vals)

    def write(self, vals):
        for record in self:
            # Assign code only if missing
            if not record.employee_code:
                name = vals.get('name', record.name)
                if name and 'employee_code' not in vals:
                    vals['employee_code'] = self._generate_employee_code(name)

        return super().write(vals)

    def _generate_employee_code(self, name):
        """
        Example: NAS-001, NAS-002
        Prefix = first 3 letters of employee name (no spaces, uppercase)
        """
        prefix = name.replace(' ', '').upper()[:3]

        last_employee = self.search(
            [('employee_code', 'like', f'{prefix}-%')],
            order='id desc',
            limit=1
        )

        if last_employee and last_employee.employee_code:
            try:
                last_number = int(last_employee.employee_code.split('-')[1])
            except Exception:
                last_number = 0
            new_number = str(last_number + 1).zfill(3)
        else:
            new_number = '001'

        return f'{prefix}-{new_number}'