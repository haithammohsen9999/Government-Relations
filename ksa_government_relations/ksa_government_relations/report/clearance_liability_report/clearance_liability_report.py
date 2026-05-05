from frappe import _

from ksa_government_relations import reporting


def execute(filters=None):
	columns = [
		{"label": _("Clearance"), "fieldname": "name", "fieldtype": "Link", "options": "Employee Clearance", "width": 170},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Clearance Type"), "fieldname": "clearance_type", "fieldtype": "Data", "width": 160},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": _("Financial Liability"), "fieldname": "total_financial_liability", "fieldtype": "Currency", "width": 130},
		{"label": _("Asset Liability"), "fieldname": "total_asset_liability", "fieldtype": "Currency", "width": 130},
		{"label": _("Leave Settlement"), "fieldname": "total_leave_settlement", "fieldtype": "Currency", "width": 130},
		{"label": _("Total Liability"), "fieldname": "total_liability", "fieldtype": "Currency", "width": 130},
	]
	data = reporting.get_clearance_liability_rows(filters)
	return columns, data
