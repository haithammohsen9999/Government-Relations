from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate

from ksa_government_relations.ksa_government_relations.doctype.government_request.government_request import (
	sync_request_snapshot,
)
from ksa_government_relations.utils import (
	get_employee_snapshot,
	get_or_create_government_profile,
	get_payment_defaults,
	get_settings,
	refresh_profile_status,
)


class EmployeeVisa(Document):
	def validate(self):
		self.populate_employee_context()
		self.apply_visa_pricing()
		self.resolve_payment_request()
		self.sync_payment_request_pricing()
		self.sync_status_from_payment()
		self.validate_dates()
		self.validate_government_documents()
		if not self.status:
			self.status = "Requested"

	def on_update(self):
		self.sync_payment_request_pricing()
		self.sync_profile()
		self.sync_related_requests()

	def on_cancel(self):
		self.sync_profile(cancelled=True)
		self.sync_related_requests(cancelled=True)

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
				["custom_destination_country", "custom_destination_city", "custom_departure_airport", "custom_arrival_airport", "from_date", "to_date"],
				as_dict=True,
			)
			if leave:
				self.destination_country = self.destination_country or leave.custom_destination_country
				self.destination_city = self.destination_city or leave.custom_destination_city
				self.departure_airport = self.departure_airport or leave.custom_departure_airport
				self.arrival_airport = self.arrival_airport or leave.custom_arrival_airport
				self.issue_date = self.issue_date or leave.from_date
				self.expiry_date = self.expiry_date or leave.to_date

	def resolve_payment_request(self):
		payment_name = self.payment_request
		if not payment_name and self.visa_request:
			payment_name = frappe.db.get_value(
				"Government Payment Request",
				{
					"employee": self.employee,
					"visa_request": self.visa_request,
					"payment_type": "Exit Re-entry Visa Fee",
				},
				"name",
				order_by="creation desc",
			)
		if not payment_name and self.leave_application:
			payment_name = frappe.db.get_value(
				"Government Payment Request",
				{
					"employee": self.employee,
					"leave_application": self.leave_application,
					"payment_type": "Exit Re-entry Visa Fee",
				},
				"name",
				order_by="creation desc",
			)
		if payment_name:
			self.payment_request = payment_name
			self.payment_request_status = frappe.db.get_value("Government Payment Request", payment_name, "status")

	def sync_status_from_payment(self):
		if not self.payment_request:
			self.payment_request_status = None
			return
		payment_status = self.payment_request_status or frappe.db.get_value(
			"Government Payment Request", self.payment_request, "status"
		)
		self.payment_request_status = payment_status
		if payment_status == "Waiting Payment" and self.status == "Requested":
			self.status = "Waiting Payment"
		elif payment_status in ("Paid", "Posted to GL") and self.status in ("Requested", "Waiting Payment"):
			self.status = "Paid"

	def validate_dates(self):
		if self.issue_date and self.expiry_date and getdate(self.expiry_date) < getdate(self.issue_date):
			frappe.throw(_("Visa expiry date cannot be before the issue date."))

	def apply_visa_pricing(self):
		if self.issue_date and self.expiry_date and not self.duration_days:
			self.duration_days = max(date_diff(self.expiry_date, self.issue_date) + 1, 1)

		if self.visa_type != "Exit Re-entry":
			return

		payment_defaults = get_payment_defaults(
			"Exit Re-entry Visa Fee",
			country=self.destination_country,
			destination_city=self.destination_city,
			nationality=self.nationality,
			departure_airport=self.departure_airport,
			arrival_airport=self.arrival_airport,
			visa_type=self.visa_type,
			entry_type=self.entry_type,
			duration_days=self.duration_days,
		)
		pricing_rule = payment_defaults.get("pricing_rule")
		if pricing_rule:
			self.visa_amount = flt(pricing_rule.amount)
		elif not self.visa_amount and self.payment_request:
			self.visa_amount = flt(
				frappe.db.get_value("Government Payment Request", self.payment_request, "visa_price") or 0
			)

	def sync_payment_request_pricing(self):
		if not self.payment_request or not frappe.db.exists("Government Payment Request", self.payment_request):
			return

		payment = frappe.db.get_value(
			"Government Payment Request",
			self.payment_request,
			["status", "employee_qiwa_balance"],
			as_dict=True,
		) or {}
		if payment.get("status") in ("Paid", "Posted to GL"):
			return

		company_payable_amount = max(flt(self.visa_amount) - flt(payment.get("employee_qiwa_balance")), 0)
		frappe.db.set_value(
			"Government Payment Request",
			self.payment_request,
			{
				"employee": self.employee,
				"employee_name": self.employee_name,
				"leave_application": self.leave_application,
				"visa_request": self.visa_request,
				"nationality": self.nationality,
				"destination_country": self.destination_country,
				"destination_city": self.destination_city,
				"departure_airport": self.departure_airport,
				"arrival_airport": self.arrival_airport,
				"visa_duration_days": self.duration_days or 0,
				"visa_price": self.visa_amount or 0,
				"company_payable_amount": company_payable_amount,
			},
			update_modified=False,
		)

	def validate_government_documents(self):
		profile = get_or_create_government_profile(self.employee)
		refresh_profile_status(profile)
		settings = get_settings()
		return_date = self.expiry_date or (frappe.db.get_value("Leave Application", self.leave_application, "to_date") if self.leave_application else None)
		if settings.block_if_passport_expired and profile.passport_status == "Expired":
			frappe.throw(_("Passport is expired for employee {0}.").format(self.employee))
		if settings.block_if_iqama_expired and profile.iqama_status == "Expired":
			frappe.throw(_("Iqama is expired for employee {0}.").format(self.employee))
		if profile.passport_expiry_date and return_date and getdate(profile.passport_expiry_date) < getdate(return_date):
			frappe.throw(_("Passport expires before the leave return date."))
		if profile.iqama_expiry_date and return_date and getdate(profile.iqama_expiry_date) < getdate(return_date):
			frappe.throw(_("Iqama expires before the leave return date."))

	def sync_profile(self, cancelled: bool = False):
		profile = get_or_create_government_profile(self.employee)
		if self.visa_type == "Exit Re-entry":
			if cancelled or self.status in ("Cancelled", "Expired"):
				if profile.current_exit_reentry_visa == self.name:
					profile.current_exit_reentry_visa = None
					profile.visa_status = "Cancelled" if self.status == "Cancelled" else "Expired"
			elif self.status in ("Issued", "Active", "Paid", "Requested", "Waiting Payment"):
				profile.current_exit_reentry_visa = self.name
				profile.visa_status = "Active"
				profile.visa_expiry_date = self.expiry_date
		profile.save(ignore_permissions=True)

	def sync_related_requests(self, cancelled: bool = False):
		request_names = set()
		if self.visa_request and frappe.db.exists("Government Request", self.visa_request):
			request_names.add(self.visa_request)
		for request_name in frappe.get_all("Government Request", filters={"linked_visa": self.name}, pluck="name"):
			request_names.add(request_name)
		if self.leave_application:
			for request_name in frappe.get_all("Government Request", filters={"leave_application": self.leave_application}, pluck="name"):
				request_names.add(request_name)

		for request_name in request_names:
			if not request_name or not frappe.db.exists("Government Request", request_name):
				continue
			request = frappe.get_doc("Government Request", request_name)
			request.linked_visa = None if cancelled and request.linked_visa == self.name else (request.linked_visa or self.name)
			frappe.db.set_value("Government Request", request_name, "linked_visa", request.linked_visa, update_modified=False)
			sync_request_snapshot(request_name)
