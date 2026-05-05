from frappe import _

from ksa_government_relations import reporting


def execute(filters=None):
	columns = [
		{"label": _("Leave Application"), "fieldname": "name", "fieldtype": "Link", "options": "Leave Application", "width": 170},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("From Date"), "fieldname": "from_date", "fieldtype": "Date", "width": 100},
		{"label": _("To Date"), "fieldname": "to_date", "fieldtype": "Date", "width": 100},
		{"label": _("GRO Status"), "fieldname": "custom_gro_status", "fieldtype": "Data", "width": 130},
		{"label": _("Finance Status"), "fieldname": "custom_finance_status", "fieldtype": "Data", "width": 130},
		{"label": _("Clearance Status"), "fieldname": "custom_clearance_status", "fieldtype": "Data", "width": 140},
		{"label": _("Ticket Status"), "fieldname": "custom_ticket_status", "fieldtype": "Data", "width": 120},
		{"label": _("Return Status"), "fieldname": "custom_return_status", "fieldtype": "Data", "width": 150},
	]
	data = reporting.get_outside_ksa_leave_rows(filters)
	return columns, data
