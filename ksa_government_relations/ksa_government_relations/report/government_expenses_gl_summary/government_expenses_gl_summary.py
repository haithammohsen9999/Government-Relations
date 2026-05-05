from frappe import _

from ksa_government_relations import reporting


def execute(filters=None):
	columns = [
		{"label": _("Payment Type"), "fieldname": "payment_type", "fieldtype": "Data", "width": 150},
		{"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 180},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140},
		{"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 160},
		{"label": _("Posted Count"), "fieldname": "posted_count", "fieldtype": "Int", "width": 100},
		{"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 140},
	]
	data = reporting.get_government_expenses_gl_summary(filters)
	return columns, data
