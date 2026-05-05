from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today

from ksa_government_relations.ksa_government_relations.doctype.government_request.government_request import (
	sync_request_snapshot,
)
from ksa_government_relations.utils import get_employee_snapshot, get_payment_defaults, get_settings


class GovernmentPaymentRequest(Document):
	def validate(self):
		self.populate_employee_context()
		self.populate_ticket_context()
		self.calculate_amounts()
		self.normalize_payment_type_fields()
		self.apply_account_defaults()
		if not self.status:
			self.status = "Draft"

	def before_submit(self):
		if self.status == "Draft":
			self.status = "Waiting Payment"

	def on_update_after_submit(self):
		previous = self.get_doc_before_save()
		if self.status == "Paid" and not self.journal_entry:
			self.post_to_gl()
		elif previous and previous.status != self.status:
			self.update_linked_documents()

	def populate_employee_context(self):
		if not self.employee:
			frappe.throw(_("Employee is required."))
		snapshot = get_employee_snapshot(self.employee)
		self.employee_name = snapshot.get("employee_name")
		self.nationality = self.nationality or snapshot.get("nationality")
		if not self.company:
			self.company = snapshot.get("company")
		if self.payment_type == "Exit Re-entry Visa Fee" and not self.employee_qiwa_balance:
			self.employee_qiwa_balance = snapshot.get("qiwa_balance") or 0

	def populate_ticket_context(self):
		if not self.ticket_request or not frappe.db.exists("Travel Ticket Request", self.ticket_request):
			return
		ticket = frappe.db.get_value(
			"Travel Ticket Request",
			self.ticket_request,
			[
				"employee",
				"employee_name",
				"leave_application",
				"government_request",
				"visa_request",
				"nationality",
				"destination_country",
				"destination_city",
				"departure_airport",
				"arrival_airport",
				"ticket_amount",
			],
			as_dict=True,
		)
		if not ticket:
			return
		self.employee = self.employee or ticket.employee
		self.employee_name = self.employee_name or ticket.employee_name
		self.leave_application = self.leave_application or ticket.leave_application
		self.government_request = self.government_request or ticket.government_request
		self.visa_request = self.visa_request or ticket.visa_request
		self.nationality = self.nationality or ticket.nationality
		self.destination_country = self.destination_country or ticket.destination_country
		self.destination_city = self.destination_city or ticket.destination_city
		self.departure_airport = self.departure_airport or ticket.departure_airport
		self.arrival_airport = self.arrival_airport or ticket.arrival_airport
		if self.payment_type == "Ticket Fee":
			self.visa_price = flt(ticket.ticket_amount)

	def calculate_amounts(self):
		if self.payment_type == "Ticket Fee" and self.ticket_request and not flt(self.visa_price):
			self.visa_price = frappe.db.get_value("Travel Ticket Request", self.ticket_request, "ticket_amount") or 0
		self.company_payable_amount = max(flt(self.visa_price) - flt(self.employee_qiwa_balance), 0)
		if self.payment_type == "Ticket Fee":
			self.company_payable_amount = flt(self.visa_price)

	def normalize_payment_type_fields(self):
		if self.payment_type == "Ticket Fee":
			self.employee_qiwa_balance = 0
			self.visa_duration_days = 0

	def apply_account_defaults(self):
		defaults = get_payment_defaults(
			self.payment_type,
			company=self.company,
			country=self.destination_country,
			destination_city=self.destination_city,
			nationality=self.nationality,
			departure_airport=self.departure_airport,
			arrival_airport=self.arrival_airport,
			visa_type="Exit Re-entry",
			entry_type="Single",
			duration_days=self.visa_duration_days,
		)
		if not flt(self.visa_price) and defaults.get("pricing_rule"):
			self.visa_price = flt(defaults["pricing_rule"].amount)
		if not self.account:
			self.account = defaults.get("account")
		if not self.payment_account:
			self.payment_account = defaults.get("payment_account")
		if not self.cost_center:
			self.cost_center = defaults.get("cost_center")

	def post_to_gl(self):
		if self.journal_entry:
			return
		if not flt(self.company_payable_amount):
			self.db_set("status", "Posted to GL", update_modified=False)
			self.update_linked_documents()
			return

		if not self.account or not self.payment_account:
			frappe.throw(_("Accounting setup is incomplete for this payment request."))

		je = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"posting_date": self.payment_date or today(),
				"company": self.company,
				"user_remark": _("Government payment request {0}").format(self.name),
				"accounts": [
					{
						"account": self.account,
						"debit_in_account_currency": self.company_payable_amount,
						"cost_center": self.cost_center,
					},
					{
						"account": self.payment_account,
						"credit_in_account_currency": self.company_payable_amount,
						"cost_center": self.cost_center,
					},
				],
			}
		)
		je.insert(ignore_permissions=True)
		je.submit()
		self.db_set("journal_entry", je.name, update_modified=False)
		self.db_set("status", "Posted to GL", update_modified=False)
		self.update_linked_documents()

	def update_linked_documents(self):
		if self.government_request and frappe.db.exists("Government Request", self.government_request):
			frappe.db.set_value("Government Request", self.government_request, "status", "Paid", update_modified=False)
		if self.visa_request and frappe.db.exists("Government Request", self.visa_request):
			frappe.db.set_value("Government Request", self.visa_request, "status", "Paid", update_modified=False)
		if self.leave_application and frappe.db.exists("Leave Application", self.leave_application):
			leave_updates = {}
			if self.payment_type == "Ticket Fee":
				if self.status in ("Paid", "Posted to GL"):
					leave_updates["custom_ticket_status"] = "Paid"
				elif self.status == "Waiting Payment":
					leave_updates["custom_ticket_status"] = "Requested"
				elif self.status == "Cancelled":
					leave_updates["custom_ticket_status"] = "Cancelled"
			else:
				if self.status in ("Paid", "Posted to GL"):
					leave_updates["custom_finance_status"] = "Paid"
				elif self.status == "Waiting Payment":
					leave_updates["custom_finance_status"] = "Pending"
			if leave_updates:
				frappe.db.set_value("Leave Application", self.leave_application, leave_updates, update_modified=False)
		if self.ticket_request and frappe.db.exists("Travel Ticket Request", self.ticket_request):
			ticket_values = {
				"payment_request": self.name,
				"payment_request_status": self.status,
			}
			if self.status in ("Paid", "Posted to GL"):
				ticket_values["status"] = "Paid"
			elif self.status == "Waiting Payment":
				ticket_values["status"] = "Waiting Payment"
			elif self.status == "Cancelled":
				ticket_values["status"] = "Cancelled"
			frappe.db.set_value("Travel Ticket Request", self.ticket_request, ticket_values, update_modified=False)

		request_names = {self.government_request, self.visa_request}
		if self.ticket_request and frappe.db.exists("Travel Ticket Request", self.ticket_request):
			ticket_links = frappe.db.get_value(
				"Travel Ticket Request", self.ticket_request, ["government_request", "visa_request"], as_dict=True
			) or {}
			request_names.update({ticket_links.get("government_request"), ticket_links.get("visa_request")})
		for request_name in request_names:
			sync_request_snapshot(request_name)
