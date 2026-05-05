from frappe import _

from ksa_government_relations import reporting


def execute(filters=None):
	columns = [
		{"label": _("Transfer Request"), "fieldname": "name", "fieldtype": "Link", "options": "Sponsorship Transfer Request", "width": 180},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Direction"), "fieldname": "transfer_direction", "fieldtype": "Data", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
		{"label": _("Payment Request"), "fieldname": "payment_request", "fieldtype": "Link", "options": "Government Payment Request", "width": 170},
		{"label": _("Qiwa Request No"), "fieldname": "qiwa_request_no", "fieldtype": "Data", "width": 140},
	]
	data = reporting.get_sponsorship_transfer_payment_rows(filters)
	return columns, data
