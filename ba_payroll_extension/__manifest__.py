# -*- coding: utf-8 -*-
{
    'name': 'Payroll Extension',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': '',
    'description': """Payroll Customization""",
    "author": "Braincrew Apps",
    "website": 'http://www.braincrewapps.com',
    "license": "AGPL-3",
    'depends': ['analytic', 'hr_payroll', 'hr_holidays', 'hr_timesheet'],
    'data': [
        'data/payroll_data.xml',
        'security/ir.model.access.csv',
        # 'report/hr_payroll_report_inh.xml',
        'views/hr_payroll.xml',
        'wizard/monthly_bank_report_wizard_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    "application": False,
}

