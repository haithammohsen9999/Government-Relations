from frappe import _
from frappe.utils import date_diff, today

from ksa_government_relations import reporting


def execute(filters=None):
	columns = [
		{"label": _("Leave Application"), "fieldname": "name", "fieldtype": "Link", "options": "Leave Application", "width": 170},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Expected Return"), "fieldname": "custom_expected_return_date", "fieldtype": "Date", "width": 120},
		{"label": _("Actual Return"), "fieldname": "custom_actual_return_date", "fieldtype": "Date", "width": 110},
		{"label": _("Return Status"), "fieldname": "custom_return_status", "fieldtype": "Data", "width": 160},
		{"label": _("Days Delayed"), "fieldname": "days_delayed", "fieldtype": "Int", "width": 100},
	]
	data = reporting.get_late_return_rows(filters)
	for row in data:
		row.days_delayed = date_diff(today(), row.to_date) if row.to_date else 0
	return columns, data
