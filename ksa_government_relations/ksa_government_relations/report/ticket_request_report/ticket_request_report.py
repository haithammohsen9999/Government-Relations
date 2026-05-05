from frappe import _

from ksa_government_relations import reporting


def execute(filters=None):
	columns = [
		{"label": _("Ticket Request"), "fieldname": "name", "fieldtype": "Link", "options": "Travel Ticket Request", "width": 170},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Destination Country"), "fieldname": "destination_country", "fieldtype": "Link", "options": "Country", "width": 130},
		{"label": _("Destination City"), "fieldname": "destination_city", "fieldtype": "Data", "width": 130},
		{"label": _("Departure Date"), "fieldname": "departure_date", "fieldtype": "Date", "width": 110},
		{"label": _("Return Date"), "fieldname": "return_date", "fieldtype": "Date", "width": 110},
		{"label": _("Ticket Amount"), "fieldname": "ticket_amount", "fieldtype": "Currency", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
	]
	data = reporting.get_ticket_request_rows(filters)
	return columns, data
