from frappe import _

from ksa_government_relations import reporting


def execute(filters=None):
	columns = [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 130},
		{"label": _("Iqama Number"), "fieldname": "iqama_number", "fieldtype": "Data", "width": 150},
		{"label": _("Iqama Expiry Date"), "fieldname": "iqama_expiry_date", "fieldtype": "Date", "width": 120},
		{"label": _("Days Remaining"), "fieldname": "days_remaining", "fieldtype": "Int", "width": 110},
		{"label": _("Status"), "fieldname": "iqama_status", "fieldtype": "Data", "width": 120},
		{"label": _("Expires Before Return"), "fieldname": "expires_before_return", "fieldtype": "Check", "width": 130},
	]
	data = reporting.get_iqama_expiry_rows(filters)
	return columns, data
