from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate

from ksa_government_relations.ksa_government_relations.doctype.government_request.government_request import (
	sync_request_snapshot,
)
from ksa_government_relations.utils import get_employee_snapshot, get_settings, get_ticket_pricing, get_ticket_travel_dates


class TravelTicketRequest(Document):
	def validate(self):
		self.populate_employee_context()
		self.set_default_dates()
		self.apply_ticket_pricing()
		self.pull_linked_payment_request()
		self.sync_status_from_payment()
		self.validate_dates()
		if not self.status:
			self.status = "Draft"

	def before_submit(self):
		if self.ticket_amount:
			self.ensure_payment_request()
			self.pull_linked_payment_request()
			self.sync_status_from_payment()
		elif self.status == "Draft":
			self.status = "Requested"

	def on_update_after_submit(self):
		self.pull_linked_payment_request()
		if self.ticket_amount and not self.payment_request:
			self.ensure_payment_request()
			self.pull_linked_payment_request()
		self.sync_payment_request_amount()
		if self.status in ("Waiting Payment", "Paid") and self.ticket_amount:
			self.ensure_payment_request()
		self.sync_status_from_payment(update_db=True)
		if self.leave_application and frappe.db.exists("Leave Application", self.leave_application):
			update_values = {"custom_ticket_status": self.status}
			if self.payment_request:
				update_values["custom_linked_ticket_request"] = self.name
			frappe.db.set_value("Leave Application", self.leave_application, update_values, update_modified=False)
		for request_name in {self.government_request, self.visa_request}:
			sync_request_snapshot(request_name)

	def populate_employee_context(self):
		if not self.employee:
			frappe.throw(_("Employee is required."))
		snapshot = get_employee_snapshot(self.employee)
		self.employee_name = snapshot.get("employee_name")
		self.nationality = self.nationality or snapshot.get("nationality")
		if self.leave_application and frappe.db.exists("Leave Application", self.leave_application):
			leave = frappe.db.get_value(
				"Leave Application",
				self.leave_application,
				["custom_destination_country", "custom_destination_city", "custom_departure_airport", "custom_arrival_airport", "company", "from_date", "to_date"],
				as_dict=True,
			)
			if leave:
				self.destination_country = self.destination_country or leave.custom_destination_country
				self.destination_city = self.destination_city or leave.custom_destination_city
				self.departure_airport = self.departure_airport or leave.custom_departure_airport
				self.arrival_airport = self.arrival_airport or leave.custom_arrival_airport
				if not self.account:
					self.account = get_settings().ticket_expense_account
				if not self.cost_center:
					self.cost_center = get_settings().default_cost_center

	def set_default_dates(self):
		if not self.leave_application or not frappe.db.exists("Leave Application", self.leave_application):
			return
		leave = frappe.db.get_value("Leave Application", self.leave_application, ["from_date", "to_date"], as_dict=True)
		if not leave:
			return
		settings = get_settings()
		departure_date, return_date = get_ticket_travel_dates(
			leave.from_date,
			leave.to_date,
			settings.default_departure_after_leave_start_days,
			settings.default_return_before_leave_end_days,
		)
		if not self.departure_date:
			self.departure_date = departure_date
		if not self.return_date:
			self.return_date = return_date

	def apply_ticket_pricing(self):
		if self.ticket_amount:
			return
		rule = get_ticket_pricing(
			country=self.destination_country,
			destination_city=self.destination_city,
			nationality=self.nationality,
			departure_airport=self.departure_airport,
			arrival_airport=self.arrival_airport,
			ticket_class="Economy",
		)
		if not rule:
			return
		self.ticket_amount = rule.amount
		self.account = self.account or rule.account
		self.cost_center = self.cost_center or rule.cost_center

	def validate_dates(self):
		if self.departure_date and self.return_date and getdate(self.return_date) < getdate(self.departure_date):
			frappe.throw(_("Return date cannot be before departure date."))
		if self.leave_application and frappe.db.exists("Leave Application", self.leave_application):
			leave = frappe.db.get_value("Leave Application", self.leave_application, ["from_date", "to_date"], as_dict=True)
			if leave and self.return_date and getdate(self.return_date) > getdate(leave.to_date):
				frappe.throw(_("Return date cannot be after leave end date."))

	def pull_linked_payment_request(self):
		payment_name = self.payment_request
		if not payment_name:
			payment_name = frappe.db.get_value(
				"Government Payment Request",
				{"ticket_request": self.name},
				"name",
			)
		if not payment_name and self.leave_application:
			payment_name = frappe.db.get_value(
				"Government Payment Request",
				{
					"payment_type": "Ticket Fee",
					"leave_application": self.leave_application,
					"employee": self.employee,
				},
				"name",
				order_by="creation desc",
			)
		if payment_name:
			self.payment_request = payment_name
			self.payment_request_status = frappe.db.get_value("Government Payment Request", payment_name, "status")

	def sync_status_from_payment(self, update_db: bool = False):
		if not self.payment_request:
			return
		payment_status = self.payment_request_status or frappe.db.get_value(
			"Government Payment Request", self.payment_request, "status"
		)
		if not payment_status:
			return
		self.payment_request_status = payment_status
		if payment_status in ("Paid", "Posted to GL"):
			self.status = "Paid"
		elif payment_status == "Waiting Payment" and self.status in ("Draft", "Requested", "Waiting Approval", "Booked"):
			self.status = "Waiting Payment"
		elif payment_status == "Cancelled":
			self.status = "Cancelled"
		if update_db:
			values = {"payment_request_status": payment_status, "payment_request": self.payment_request, "status": self.status}
			frappe.db.set_value("Travel Ticket Request", self.name, values, update_modified=False)

	def ensure_payment_request(self):
		if self.payment_request and frappe.db.exists("Government Payment Request", self.payment_request):
			if self.status == "Paid":
				payment = frappe.get_doc("Government Payment Request", self.payment_request)
				if payment.status != "Paid":
					payment.status = "Paid"
					payment.save(ignore_permissions=True)
			self.payment_request_status = frappe.db.get_value("Government Payment Request", self.payment_request, "status")
			return
		payment = frappe.get_doc(
			{
				"doctype": "Government Payment Request",
				"employee": self.employee,
				"employee_name": self.employee_name,
				"leave_application": self.leave_application,
				"government_request": self.government_request,
				"visa_request": self.visa_request,
				"ticket_request": self.name,
				"company": frappe.db.get_value("Employee", self.employee, "company"),
				"payment_type": "Ticket Fee",
				"nationality": self.nationality,
				"destination_country": self.destination_country,
				"destination_city": self.destination_city,
				"departure_airport": self.departure_airport,
				"arrival_airport": self.arrival_airport,
				"visa_price": self.ticket_amount,
				"status": "Draft",
			}
		)
		payment.insert(ignore_permissions=True)
		payment.submit()
		self.payment_request = payment.name
		self.payment_request_status = payment.status
		self.status = "Waiting Payment" if payment.status == "Waiting Payment" else self.status
		if not self.is_new():
			self.db_set("payment_request", payment.name, update_modified=False)
			self.db_set("payment_request_status", payment.status, update_modified=False)
			if self.status == "Waiting Payment":
				self.db_set("status", "Waiting Payment", update_modified=False)
		if self.status == "Paid":
			payment = frappe.get_doc("Government Payment Request", payment.name)
			payment.flags.ignore_validate_update_after_submit = True
			payment.status = "Paid"
			payment.save(ignore_permissions=True)

	def sync_payment_request_amount(self):
		if not self.payment_request or not frappe.db.exists("Government Payment Request", self.payment_request):
			return

		payment_status = self.payment_request_status or frappe.db.get_value(
			"Government Payment Request", self.payment_request, "status"
		)
		# Do not overwrite settled payment amounts after payment/GL posting.
		if payment_status in ("Paid", "Posted to GL"):
			return

		frappe.db.set_value(
			"Government Payment Request",
			self.payment_request,
			{
				"employee": self.employee,
				"employee_name": self.employee_name,
				"leave_application": self.leave_application,
				"government_request": self.government_request,
				"visa_request": self.visa_request,
				"ticket_request": self.name,
				"nationality": self.nationality,
				"destination_country": self.destination_country,
				"destination_city": self.destination_city,
				"departure_airport": self.departure_airport,
				"arrival_airport": self.arrival_airport,
				"visa_price": self.ticket_amount or 0,
				"company_payable_amount": self.ticket_amount or 0,
			},
			update_modified=False,
		)
