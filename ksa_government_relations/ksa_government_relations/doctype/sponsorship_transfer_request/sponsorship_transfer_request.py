from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ksa_government_relations.utils import clear_first_pending_status, get_employee_snapshot, get_or_create_government_profile, get_settings


class SponsorshipTransferRequest(Document):
	def validate(self):
		self.populate_employee_context()
		self.calculate_amount()
		if not self.status:
			self.status = "Draft"

	def before_submit(self):
		if self.status == "Draft":
			self.status = "Sent to Qiwa"

	def on_submit(self):
		self.ensure_payment_request()
		if self.transfer_direction == "Out of Company":
			self.ensure_clearance()

	def on_update_after_submit(self):
		if self.status == "Completed" and self.employee:
			profile = get_or_create_government_profile(self.employee)
			profile.current_sponsor = self.new_sponsor
			profile.save(ignore_permissions=True)

	def populate_employee_context(self):
		if not self.employee:
			return
		snapshot = get_employee_snapshot(self.employee)
		self.employee_name = snapshot.get("employee_name")
		self.iqama_number = self.iqama_number or snapshot.get("iqama_number")
		self.current_sponsor = self.current_sponsor or snapshot.get("current_sponsor")
		self.nationality = self.nationality or snapshot.get("nationality")

	def calculate_amount(self):
		settings = get_settings()
		if self.amount:
			return
		rules = settings.get("sponsorship_transfer_pricing_rules") or []
		for rule in rules:
			if rule.transfer_direction != self.transfer_direction:
				continue
			if rule.nationality and self.nationality and rule.nationality != self.nationality:
				continue
			self.amount = rule.amount
			self.account = rule.account
			break

	def ensure_payment_request(self):
		if not flt(self.amount):
			return

		payment_name = self.payment_request
		if not payment_name:
			payment_name = frappe.db.get_value("Government Payment Request", {"sponsorship_transfer_request": self.name}, "name")
			if payment_name:
				self.db_set("payment_request", payment_name, update_modified=False)
				self.payment_request = payment_name

		if payment_name and frappe.db.exists("Government Payment Request", payment_name):
			self.sync_payment_request(payment_name)
			return

		payment = frappe.get_doc(self.get_payment_request_values())
		payment.insert(ignore_permissions=True)
		payment.submit()
		self.db_set("payment_request", payment.name, update_modified=False)

	def get_payment_request_values(self):
		return {
			"doctype": "Government Payment Request",
			"employee": self.employee,
			"employee_name": self.employee_name,
			"company": frappe.db.get_value("Employee", self.employee, "company"),
			"sponsorship_transfer_request": self.name,
			"payment_type": "Sponsorship Transfer Fee",
			"visa_price": self.amount,
			"account": self.account,
			"status": "Draft",
		}

	def sync_payment_request(self, payment_name: str):
		payment = frappe.get_doc("Government Payment Request", payment_name)
		payment.payment_type = "Sponsorship Transfer Fee"
		payment.employee = self.employee
		payment.employee_name = self.employee_name
		payment.company = frappe.db.get_value("Employee", self.employee, "company")
		payment.sponsorship_transfer_request = self.name
		payment.leave_application = None
		payment.government_request = None
		payment.visa_request = None
		payment.ticket_request = None
		payment.visa_price = self.amount
		payment.account = self.account
		payment.employee_qiwa_balance = 0
		payment.visa_duration_days = 0
		payment.normalize_payment_type_fields()
		payment.calculate_amounts()
		payment.apply_account_defaults()

		frappe.db.set_value(
			"Government Payment Request",
			payment_name,
			{
				"employee": payment.employee,
				"employee_name": payment.employee_name,
				"company": payment.company,
				"sponsorship_transfer_request": payment.sponsorship_transfer_request,
				"payment_type": payment.payment_type,
				"leave_application": payment.leave_application,
				"government_request": payment.government_request,
				"visa_request": payment.visa_request,
				"ticket_request": payment.ticket_request,
				"visa_price": payment.visa_price,
				"account": payment.account,
				"payment_account": payment.payment_account,
				"cost_center": payment.cost_center,
				"employee_qiwa_balance": payment.employee_qiwa_balance,
				"visa_duration_days": payment.visa_duration_days,
				"company_payable_amount": payment.company_payable_amount,
			},
			update_modified=False,
		)

	def ensure_clearance(self):
		if self.clearance:
			return
		clearance = frappe.get_doc(
			{
				"doctype": "Employee Clearance",
				"employee": self.employee,
				"employee_name": self.employee_name,
				"clearance_type": "Final Exit Clearance",
				"status": "Draft",
				"notes": _("Auto-created from Sponsorship Transfer Request {0}").format(self.name),
			}
		)
		clearance.insert(ignore_permissions=True)
		clearance.generate_clearance_items()
		clearance.save(ignore_permissions=True)
		clearance.db_set("status", clear_first_pending_status(clearance), update_modified=False)
		self.db_set("clearance", clearance.name, update_modified=False)
