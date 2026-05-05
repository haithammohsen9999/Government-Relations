from frappe import _
from frappe.utils import date_diff, today

from ksa_government_relations import reporting


def execute(filters=None):
	columns = [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Current Visa"), "fieldname": "current_exit_reentry_visa", "fieldtype": "Link", "options": "Employee Visa", "width": 160},
		{"label": _("Exit Date"), "fieldname": "last_exit_date", "fieldtype": "Date", "width": 110},
		{"label": _("Expected Return"), "fieldname": "expected_return_date", "fieldtype": "Date", "width": 120},
		{"label": _("Actual Return"), "fieldname": "actual_return_date", "fieldtype": "Date", "width": 110},
		{"label": _("Days Outside"), "fieldname": "days_outside", "fieldtype": "Int", "width": 100},
	]
	data = reporting.get_employees_outside_ksa_rows(filters)
	for row in data:
		basis = row.actual_return_date or today()
		row.days_outside = date_diff(basis, row.last_exit_date) if row.last_exit_date else 0
	return columns, data
