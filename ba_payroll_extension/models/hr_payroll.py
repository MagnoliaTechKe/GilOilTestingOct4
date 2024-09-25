# -*- coding: utf-8 -*-

from odoo import models, fields, api, Command
from datetime import timedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    overtime_hours_weekdays = fields.Float(string='Overtime Hours (Weekdays)', compute='_compute_overtime_hours')
    overtime_hours_sunday_holiday = fields.Float(string='Overtime Hours (Sunday/Public Holidays)',
                                                 compute='_compute_overtime_hours')

    overtime_amount_weekdays = fields.Float(string='Overtime Amount (Weekdays)', compute='_compute_overtime_amount')
    overtime_amount_sunday_holiday = fields.Float(string='Overtime Amount (Sunday/Public Holidays)',
                                                  compute='_compute_overtime_amount')


    class HrPayslip(models.Model):
        _inherit = 'hr.payslip'

        overtime_hours_weekdays = fields.Float(string='Overtime Hours (Weekdays)', compute='_compute_overtime_hours')
        overtime_hours_sunday_holiday = fields.Float(string='Overtime Hours (Sunday/Holiday)',
                                                     compute='_compute_overtime_hours')

        @api.depends('employee_id', 'date_from', 'date_to')
        def _compute_overtime_hours(self):
            for payslip in self:
                overtime_weekdays = 0
                overtime_sunday_holiday = 0

                # Fetch actual attendance records for the employee
                attendance_records = self.env['hr.attendance'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('check_in', '>=', payslip.date_from),
                    ('check_out', '<=', payslip.date_to)
                ])

                # Get the work schedule and public holidays
                public_holidays = self._get_public_holidays(payslip.date_from, payslip.date_to)

                for attendance in attendance_records:
                    attendance_day = attendance.check_in.weekday()  # 0 = Monday, 6 = Sunday
                    overtime_hours_data = attendance.overtime_hours
                    time_string = self.convert_float_time_to_hours_minutes(overtime_hours_data)
                    overtime_hours = self.convert_time_string_to_float(time_string)

                    # Check if it's a Sunday or public holiday
                    if attendance_day == 6 or attendance.check_in.date() in public_holidays:
                        # Overtime for Sundays and Public Holidays (OT2)
                        overtime_sunday_holiday += overtime_hours
                    elif 0 <= attendance_day <= 4:  # Weekdays (Monday to Friday)
                        # Overtime for weekdays (OT1)
                        overtime_weekdays += overtime_hours

                payslip.overtime_hours_weekdays = overtime_weekdays
                payslip.overtime_hours_sunday_holiday = overtime_sunday_holiday

    def convert_float_time_to_hours_minutes(self, float_time):
        hours = int(float_time)
        minutes = round((float_time - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    def convert_time_string_to_float(self, time_str):
        hours, minutes = map(int, time_str.split(':'))
        float_time = hours + (minutes / 60)
        return round(float_time, 2)


    @api.depends('overtime_hours_weekdays', 'overtime_hours_sunday_holiday')
    def _compute_overtime_amount(self):
        for payslip in self:
            basic_pay = payslip.contract_id.wage
            ot1_rate = 1.5
            ot2_rate = 2
            hourly_rate = basic_pay / 192

            payslip.overtime_amount_weekdays = payslip.overtime_hours_weekdays * hourly_rate * ot1_rate
            payslip.overtime_amount_sunday_holiday = payslip.overtime_hours_sunday_holiday * hourly_rate * ot2_rate

    def _get_public_holidays(self, date_from, date_to):
        # Fetch the list of public holidays between date_from and date_to
        holidays = self.env['resource.calendar.leaves'].search([
            ('date_from', '<=', date_to),
            ('date_to', '>=', date_from),
            ('resource_id', '=', False)
        ])
        holiday_dates = set()
        for holiday in holidays:
            current_date = holiday.date_from.date()
            end_date = holiday.date_to.date()
            # Add all dates in the range from start date to end date
            while current_date <= end_date:
                holiday_dates.add(current_date)
                current_date += timedelta(days=1)
        return holiday_dates


    def action_print_payslip(self):
        # records = self.env['hr.payslip'].browse(self.ids)
        return self.env.ref('hr_payroll.action_report_payslip').report_action(self)
