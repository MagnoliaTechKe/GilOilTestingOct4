# -*- coding: utf-8 -*-

from odoo import models, fields, api, Command
from datetime import datetime
from datetime import timedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    overtime_hours_weekdays = fields.Float(string='Overtime Hours (Weekdays)', compute='_compute_overtime_hours')
    overtime_hours_sunday_holiday = fields.Float(string='Overtime Hours (Sunday/Public Holidays)',
                                                 compute='_compute_overtime_hours')

    overtime_amount_weekdays = fields.Float(string='Overtime Amount (Weekdays)', compute='_compute_overtime_amount')
    overtime_amount_sunday_holiday = fields.Float(string='Overtime Amount (Sunday/Public Holidays)',
                                                  compute='_compute_overtime_amount')

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_overtime_hours(self):
        for payslip in self:
            overtime_weekdays_minutes = 0
            overtime_sunday_holiday_minutes = 0

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
                overtime_hours = attendance.overtime_hours  # Assume this is a float representing hours

                # Convert the float to hours and minutes
                hours = int(overtime_hours)
                minutes = int((overtime_hours - hours) * 60)
                total_minutes = hours * 60 + minutes

                # Check if it's a Sunday or public holiday
                if attendance_day == 6 or attendance.check_in.date() in public_holidays:
                    # Overtime 2 for Sundays and Public Holidays
                    overtime_sunday_holiday_minutes += total_minutes
                elif 0 <= attendance_day <= 4:  # Weekdays (Monday to Friday)
                    # Overtime for weekdays
                    overtime_weekdays_minutes += total_minutes

            # Convert total minutes back to float hours
            payslip.overtime_hours_weekdays = overtime_weekdays_minutes / 60.0
            payslip.overtime_hours_sunday_holiday = overtime_sunday_holiday_minutes / 60.0

    # @api.depends('employee_id', 'date_from', 'date_to')
    # def _compute_overtime_hours(self):
    #     for payslip in self:
    #         overtime_weekdays = 0
    #         overtime_sunday_holiday = 0
    #         timesheets = self.env['account.analytic.line'].search([
    #             ('employee_id', '=', payslip.employee_id.id),
    #             ('date', '>=', payslip.date_from),
    #             ('date', '<=', payslip.date_to)
    #         ])

    #         public_holidays = self._get_public_holidays(payslip.date_from, payslip.date_to)

    #         # Iterate over timesheets to calculate overtime
    #         for timesheet in timesheets:
    #             timesheet_day = str(timesheet.date.weekday())  # Get the day of the week (0 = Monday, 6 = Sunday)
    #             worked_hours = timesheet.unit_amount  # Number of hours worked that day

    #             # Find the corresponding work schedule for that day
    #             attendance = payslip.employee_id.resource_calendar_id.attendance_ids.filtered(
    #                 lambda a: a.dayofweek == timesheet_day
    #             )

    #             if timesheet_day == '6' or timesheet.date in public_holidays:
    #                 # Overtime 2 for Sundays and Public Holidays
    #                 overtime_sunday_holiday += worked_hours
    #             elif 0 <= int(timesheet_day) <= 4:  # Only weekdays (Monday to Friday)
    #                 if attendance:
    #                     total_scheduled_hours = 0

    #                     for att in attendance:
    #                         if att.day_period != 'lunch':
    #                             scheduled_hours = att.hour_to - att.hour_from
    #                             total_scheduled_hours += scheduled_hours
    #                     # Calculate overtime based on the excess worked hours
    #                     if worked_hours >= total_scheduled_hours:
    #                         overtime_weekdays += worked_hours - total_scheduled_hours
    #                 else:
    #                     # If no attendance is found for the day, consider all hours as overtime
    #                     overtime_weekdays += worked_hours

    #         # Set the computed overtime hours
    #         payslip.overtime_hours_weekdays = overtime_weekdays
    #         payslip.overtime_hours_sunday_holiday = overtime_sunday_holiday

    @api.depends('overtime_hours_weekdays', 'overtime_hours_sunday_holiday')
    def _compute_overtime_amount(self):
        for payslip in self:
            basic_pay = payslip.contract_id.wage
            ot1_rate = 1.5
            ot2_rate = 2
            hourly_rate = basic_pay / 192  # Basic Pay divided by 192 hours for overtime calculation

            # Calculate OT1 and OT2 amounts
            payslip.overtime_amount_weekdays = payslip.overtime_hours_weekdays * hourly_rate * ot1_rate
            payslip.overtime_amount_sunday_holiday = payslip.overtime_hours_sunday_holiday * hourly_rate * ot2_rate

    def _get_public_holidays(self, date_from, date_to):
        # Fetch the list of public holidays between date_from and date_to
        holidays = self.env['resource.calendar.leaves'].search([
            ('date_from', '<=', date_to),
            ('date_to', '>=', date_from),
            ('resource_id', '=', False)  # Consider only public holidays, not individual leaves
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

    # @api.model
    # def _compute_input_line_ids(self):
    #     """
    #     function used for writing overtime record in payslip
    #     input tree.
    #
    #     """
    #     input_data = []
    #     res = super(HrPayslip, self)._compute_input_line_ids()
    #     overtime_type = self.env.ref('ba_payroll_extension.hr_salary_rule_overtime')
    #     overtime_input_type = self.env.ref('ba_payroll_extension.input_overtime_payroll')
    #     contract = self.contract_id
    #     input_data.append(Command.create({
    #         'name': overtime_type.name,
    #         'amount': self.overtime_hours_sunday_holiday,
    #         'input_type_id': overtime_input_type.id if overtime_input_type else 1
    #     }))
    #     print(input_data)
    #     self.update({'input_line_ids': input_data})
    #     return res

