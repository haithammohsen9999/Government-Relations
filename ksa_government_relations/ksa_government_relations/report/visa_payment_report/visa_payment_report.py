from frappe import _

from ksa_government_relations import reporting


def execute(filters=None):
	columns = [
		{"label": _("Payment Request"), "fieldname": "name", "fieldtype": "Link", "options": "Government Payment Request", "width": 170},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Payment Type"), "fieldname": "payment_type", "fieldtype": "Data", "width": 150},
		{"label": _("Visa Price"), "fieldname": "visa_price", "fieldtype": "Currency", "width": 120},
		{"label": _("Qiwa Balance"), "fieldname": "employee_qiwa_balance", "fieldtype": "Currency", "width": 120},
		{"label": _("Company Payable"), "fieldname": "company_payable_amount", "fieldtype": "Currency", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Journal Entry"), "fieldname": "journal_entry", "fieldtype": "Link", "options": "Journal Entry", "width": 150},
	]
	data = [row for row in reporting.get_payment_request_rows(filters) if row.payment_type == "Exit Re-entry Visa Fee"]
	return columns, data
