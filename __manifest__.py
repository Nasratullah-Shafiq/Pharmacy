# pharmacy_management/__manifest__.py
{
    'name': 'Pharmacy Management',
    'version': '17.0.1.0.0',
    'category': 'Healthcare',
    # 'sequence': -20,
    'summary': 'Manage pharmacy purchases, sales, medicine, HR and finance for multi-branch pharmacies',
    'description': """
        Pharmacy Management system:
        - Human Resources (employees, attendance placeholder, salaries)
        - Finance (income/expenses, branch reports)
        - Pharmacy (purchase/sales, medicine inventory, stock management)
        """,
    'author': 'Nasratullah Shafiq / Generated',
    'depends': ['base', 'hr', 'account'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/pharmacy_default_users.xml',
        'data/pharmacy_default_currency.xml',

        # Menus should load first
        'views/menu.xml',

        # Wizard files
        'wizard/views/finance_report_wizard_views.xml',
        # 'wizard/views/sale_report_wizard_views.xml',
        # 'wizard/views/purchase_report_wizard_views.xml',
        # 'wizard/views/salary_payment_wizard_views.xml',
        # 'wizard/views/expense_report_wizard_views.xml',
        # 'wizard/views/cash_deposit_report_wizard_views.xml',
        'wizard/views/cash_account_report_wizard_views.xml',
        'wizard/views/customer_payment_report_wizard_views.xml',
        'wizard/views/supplier_payment_report_wizard_views.xml',
        # 'wizard/views/payment_report_wizard_views.xml',

        # view files

        'views/employee_views.xml',
        'views/salary_payment_views.xml',

        'views/sales_views.xml',
        'views/pharmacy_stock_views.xml',
        'views/cashier_views.xml',
        'views/purchase_views.xml',
        'views/cash_account_views.xml',
        'views/cash_deposit_views.xml',
        'views/cash_transfer_views.xml',
        'views/expenses_views.xml',
        'views/hide_menu.xml',
        'views/product_views.xml',
        'views/pharmacy_payment_views.xml',
        'views/partner_views.xml',

        # Reports - actions before templates
        # 'report/finance_report_action.xml',
        # 'report/finance_report_template.xml',
        # 'report/purchase_report_template.xml',
        # 'report/sales_report_template.xml',
        # 'report/salary_payment_report_template.xml',
        # 'report/expense_report_template.xml',
        # 'report/death_report_template.xml',
        # 'report/cash_deposit_report_template.xml',
        'report/cash_account_report_template.xml',
        'report/customer_payment_report_template.xml',
        'report/supplier_payment_report_template.xml',
        # 'report/payment_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 'pharmacy/static/src/css/dashboard.css',
            # 'pharmacy/static/src/js/dashboard_graph.js',
        ],
    },

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}