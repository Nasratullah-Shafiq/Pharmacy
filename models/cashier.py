from odoo import models, fields, api

class PharmacyCashier(models.Model):
    _name = 'pharmacy.cashier'
    _description = 'pharmacy Cashier'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # enable chatter & activities

    name = fields.Char("Cashier Name", required=True, tracking=True)
    phone = fields.Char("Phone")
    email = fields.Char("Email")

    active = fields.Boolean(default=True)
