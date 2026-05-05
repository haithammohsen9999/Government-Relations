from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ksa_government_relations.ksa_government_relations.doctype.government_request.government_request import (
	sync_request_snapshot,
)
from ksa_government_relations.utils import clear_first_pending_status, get_employee_snapshot, get_outstanding_clearance_items


class EmployeeClearance(Document):
	def validate(self):
		self.populate_employee_context()
		self.validate_leave_application()
		self.set_totals()
		self.validate_clear_status()
		if not self.status:
			self.status = "Draft"

	def before_submit(self):
		if not self.clearance_items:
			self.generate_clearance_items()
		if self.status == "Draft":
			self.status = clear_first_pending_status(self)

	def on_update_after_submit(self):
		self.set_totals()
		if self.status == "Cleared":
			self.mark_linked_documents_cleared()
		elif self.leave_application and frappe.db.exists("Leave Application", self.leave_application):
			frappe.db.set_value("Leave Application", self.leave_application, "custom_clearance_status", "Pending", update_modified=False)
		sync_request_snapshot(self.government_request)

	def populate_employee_context(self):
		if not self.employee:
			frappe.throw(_("Employee is required."))
		snapshot = get_employee_snapshot(self.employee)
		self.employee_name = snapshot.get("employee_name")

	def validate_leave_application(self):
		if self.leave_application and frappe.db.exists("Leave Application", self.leave_application):
			employee = frappe.db.get_value("Leave Application", self.leave_application, "employee")
			if employee and employee != self.employee:
				frappe.throw(_("Linked Leave Application belongs to another employee."))

	@frappe.whitelist()
	def generate_clearance_items(self):
		self.set("clearance_items", [])
		for item in get_outstanding_clearance_items(self.employee):
			self.append("clearance_items", item)
		self.set_totals()
		self.status = "Draft" if self.docstatus == 0 else clear_first_pending_status(self)
		return self.clearance_items

	def set_totals(self):
		self.total_financial_liability = sum(
			flt(item.amount)
			for item in self.clearance_items
			if item.department == "Finance" or item.item_type in ("Employee Advance", "Loan", "Expense Claim", "Government Payment")
		)
		self.total_asset_liability = sum(
			flt(item.amount)
			for item in self.clearance_items
			if item.department in ("Assets", "IT") or item.item_type in ("Asset", "Custody")
		)
		self.total_leave_settlement = sum(
			flt(item.amount)
			for item in self.clearance_items
			if item.item_type in ("Leave Encashment", "Leave Deduction")
		)
		self.total_liability = flt(self.total_financial_liability) + flt(self.total_asset_liability) + flt(self.total_leave_settlement)

	def validate_clear_status(self):
		if self.status != "Cleared":
			return
		allowed = {"Returned", "Paid", "Approved", "Waived", "Approved to Travel With Employee"}
		pending = [
			item.description or item.reference_name or item.item_type
			for item in self.clearance_items
			if item.mandatory and item.status not in allowed
		]
		if pending:
			frappe.throw(_("Mandatory clearance items are still pending: {0}").format(", ".join(pending)))

	def mark_linked_documents_cleared(self):
		if self.leave_application and frappe.db.exists("Leave Application", self.leave_application):
			frappe.db.set_value("Leave Application", self.leave_application, "custom_clearance_status", "Cleared", update_modified=False)
		if self.government_request and frappe.db.exists("Government Request", self.government_request):
			frappe.db.set_value("Government Request", self.government_request, "linked_clearance", self.name, update_modified=False)
		frappe.db.set_value("Employee", self.employee, "custom_latest_clearance", self.name, update_modified=False)
		sync_request_snapshot(self.government_request)
