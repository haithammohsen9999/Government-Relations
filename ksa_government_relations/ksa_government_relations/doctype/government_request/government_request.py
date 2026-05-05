from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

from ksa_government_relations.utils import create_government_request_log, get_employee_snapshot


class GovernmentRequest(Document):
	def validate(self):
		self.populate_employee_context()
		self.resolve_linked_documents()
		self.populate_linked_statuses()
		self.populate_linked_summary_fields()
		self.sync_status_from_linked_documents()
		self.populate_progress_metrics()
		self.validate_linked_document_ownership()
		self.validate_dates()
		self.ensure_status()
		self.track_status_change()

	def before_submit(self):
		if self.status == "Draft":
			self.status = "Submitted"
		create_government_request_log(self, "Request Submitted", self.status, self.remarks or _("Request submitted"))

	def on_update_after_submit(self):
		if self.status == "Completed":
			self.update_linked_documents()

	def populate_employee_context(self):
		if not self.employee:
			frappe.throw(_("Employee is required."))
		snapshot = get_employee_snapshot(self.employee)
		self.employee_name = snapshot.get("employee_name")
		self.employee_government_profile = snapshot.get("government_profile")
		if not self.company:
			self.company = snapshot.get("company")
		if not self.branch:
			self.branch = snapshot.get("branch")
		if not self.department:
			self.department = snapshot.get("department")
		if not self.request_date:
			self.request_date = today()
		if not self.government_platform:
			self.government_platform = snapshot.get("government_portal")

	def resolve_linked_documents(self):
		links = self.get_resolved_links()
		for fieldname, value in links.items():
			if value:
				setattr(self, fieldname, value)

	def get_resolved_links(self):
		links = {
			"linked_visa": None,
			"linked_payment_request": None,
			"linked_ticket_request": None,
			"linked_clearance": None,
		}

		if self.leave_application and frappe.db.exists("Leave Application", self.leave_application):
			leave_links = frappe.db.get_value(
				"Leave Application",
				self.leave_application,
				[
					"custom_linked_employee_visa",
					"custom_linked_payment_request",
					"custom_linked_ticket_request",
					"custom_linked_clearance",
				],
				as_dict=True,
			) or {}
			links.update(
				{
					"linked_visa": leave_links.get("custom_linked_employee_visa"),
					"linked_payment_request": leave_links.get("custom_linked_payment_request"),
					"linked_ticket_request": leave_links.get("custom_linked_ticket_request"),
					"linked_clearance": leave_links.get("custom_linked_clearance"),
				}
			)

		if self.request_type == "Issue Exit Re-entry Visa":
			payment_name = frappe.db.get_value(
				"Government Payment Request",
				{"employee": self.employee, "visa_request": self.name},
				"name",
				order_by="creation desc",
			)
			ticket_name = frappe.db.get_value(
				"Travel Ticket Request",
				{"employee": self.employee, "visa_request": self.name},
				"name",
				order_by="creation desc",
			)
			if payment_name:
				links["linked_payment_request"] = payment_name
			if ticket_name:
				links["linked_ticket_request"] = ticket_name

		if self.parent_request:
			parent_request = frappe.db.get_value(
				"Government Request",
				self.parent_request,
				["linked_clearance", "linked_ticket_request", "leave_application"],
				as_dict=True,
			) or {}
			links["linked_clearance"] = links["linked_clearance"] or parent_request.get("linked_clearance")
			links["linked_ticket_request"] = links["linked_ticket_request"] or parent_request.get("linked_ticket_request")
			if not self.leave_application and parent_request.get("leave_application"):
				self.leave_application = parent_request.get("leave_application")

		return links

	def populate_linked_statuses(self):
		status_map = {
			"linked_visa": ("Employee Visa", "status", "linked_visa_status"),
			"linked_payment_request": ("Government Payment Request", "status", "linked_payment_request_status"),
			"linked_ticket_request": ("Travel Ticket Request", "status", "linked_ticket_request_status"),
			"linked_clearance": ("Employee Clearance", "status", "linked_clearance_status"),
		}
		for link_field, (doctype, status_field, target_field) in status_map.items():
			link_name = getattr(self, link_field, None)
			status = None
			if link_name and frappe.db.exists(doctype, link_name):
				status = frappe.db.get_value(doctype, link_name, status_field)
			setattr(self, target_field, status)

	def populate_linked_summary_fields(self):
		self.linked_ticket_payment_request = None
		self.linked_ticket_payment_request_status = ""
		self.ticket_amount = 0
		self.visa_amount = 0
		self.clearance_amount = 0
		self.custody_amount = 0

		if self.linked_payment_request and frappe.db.exists("Government Payment Request", self.linked_payment_request):
			payment = frappe.db.get_value(
				"Government Payment Request",
				self.linked_payment_request,
				["visa_price", "company_payable_amount"],
				as_dict=True,
			) or {}
			self.visa_amount = payment.get("visa_price") or payment.get("company_payable_amount") or 0
		elif self.linked_visa and frappe.db.exists("Employee Visa", self.linked_visa):
			self.visa_amount = frappe.db.get_value("Employee Visa", self.linked_visa, "visa_amount") or 0

		if self.linked_ticket_request and frappe.db.exists("Travel Ticket Request", self.linked_ticket_request):
			ticket = frappe.db.get_value(
				"Travel Ticket Request",
				self.linked_ticket_request,
				["ticket_amount", "payment_request", "payment_request_status"],
				as_dict=True,
			) or {}
			self.ticket_amount = ticket.get("ticket_amount")
			self.linked_ticket_payment_request = ticket.get("payment_request")
			self.linked_ticket_payment_request_status = ticket.get("payment_request_status")

		if (
			self.linked_ticket_payment_request
			and not self.linked_ticket_payment_request_status
			and frappe.db.exists("Government Payment Request", self.linked_ticket_payment_request)
		):
			self.linked_ticket_payment_request_status = frappe.db.get_value(
				"Government Payment Request", self.linked_ticket_payment_request, "status"
			)

		if self.linked_clearance and frappe.db.exists("Employee Clearance", self.linked_clearance):
			clearance = frappe.db.get_value(
				"Employee Clearance",
				self.linked_clearance,
				["total_liability", "total_asset_liability"],
				as_dict=True,
			) or {}
			self.clearance_amount = clearance.get("total_liability") or 0
			self.custody_amount = clearance.get("total_asset_liability") or 0

	def populate_progress_metrics(self):
		status_scores = {
			"Draft": 0,
			"Submitted": 20,
			"Under Review": 35,
			"Government Processing": 55,
			"Waiting Payment": 45,
			"Paid": 70,
			"Posted to GL": 100,
			"Issued": 100,
			"Completed": 100,
			"Rejected": 100,
			"Cancelled": 100,
			"On Hold": 25,
			"Requested": 20,
			"Booked": 85,
			"Cleared": 100,
			"Active": 90,
			"Used": 100,
			"Expired": 100,
		}

		items = []
		if self.is_visa_sub_request():
			items.extend(
				[
					("Employee Visa", self.linked_visa),
					("Government Payment Request", self.linked_payment_request),
				]
			)
		elif self.leave_application and frappe.db.exists("Leave Application", self.leave_application):
			leave = frappe.db.get_value(
				"Leave Application",
				self.leave_application,
				[
					"custom_linked_government_request",
					"custom_linked_visa_request",
					"custom_linked_payment_request",
					"custom_linked_ticket_request",
					"custom_linked_clearance",
				],
				as_dict=True,
			) or {}
			items.extend(
				[
					("Government Request", leave.get("custom_linked_government_request")),
					("Government Request", leave.get("custom_linked_visa_request")),
					("Government Payment Request", leave.get("custom_linked_payment_request")),
					("Travel Ticket Request", leave.get("custom_linked_ticket_request")),
					("Employee Clearance", leave.get("custom_linked_clearance")),
				]
			)
		else:
			items.extend(
				[
					("Employee Visa", self.linked_visa),
					("Government Payment Request", self.linked_payment_request),
					("Travel Ticket Request", self.linked_ticket_request),
					("Employee Clearance", self.linked_clearance),
				]
			)

		seen = set()
		scores = []
		labels = []
		for doctype, name in items:
			if not name or (doctype, name) in seen or not frappe.db.exists(doctype, name):
				continue
			if doctype == "Government Request" and name == self.name and self.is_main_travel_request():
				continue
			seen.add((doctype, name))
			status = frappe.db.get_value(doctype, name, "status")
			if status is None:
				continue
			scores.append(self.get_progress_score(doctype, status, status_scores))
			labels.append(f"{doctype}: {status}")

		if not scores:
			scores = [status_scores.get(self.status, 0)]
			labels = [f"Government Request: {self.status}"]

		self.completion_percent = round(sum(scores) / len(scores), 1)
		self.progress_summary = " | ".join(labels[:5])

	def get_progress_score(self, doctype: str, status: str, status_scores: dict[str, int]) -> int:
		if doctype == "Travel Ticket Request" and status == "Paid":
			return 100
		if doctype == "Employee Visa" and status == "Issued":
			return 100
		return status_scores.get(status, 0)

	def is_main_travel_request(self) -> bool:
		return self.request_type == "Outside KSA Leave Processing" and not self.parent_request

	def is_visa_sub_request(self) -> bool:
		return self.request_type == "Issue Exit Re-entry Visa" or bool(self.parent_request)

	def sync_status_from_linked_documents(self):
		terminal_statuses = {"Completed", "Cancelled", "Rejected"}
		if self.status in terminal_statuses:
			return

		has_payment = bool(self.linked_payment_request)
		has_visa = bool(self.linked_visa)
		has_ticket = bool(self.linked_ticket_request)
		has_clearance = bool(self.linked_clearance)
		has_any_link = any([has_payment, has_visa, has_ticket, has_clearance])

		if not has_any_link:
			return

		payment_done = (not has_payment) or self.linked_payment_request_status in {"Paid", "Posted to GL"}
		visa_done = (not has_visa) or self.linked_visa_status in {"Issued", "Active", "Used", "Expired"}
		ticket_done = (not has_ticket) or self.linked_ticket_request_status in {"Paid", "Cancelled"}
		clearance_done = (not has_clearance) or self.linked_clearance_status in {"Cleared", "Cancelled"}

		if self.is_visa_sub_request():
			if has_payment and has_visa and payment_done and visa_done:
				self.status = "Completed"
			elif has_payment and payment_done and self.linked_visa_status in {"Requested", "Waiting Payment", "Paid"}:
				self.status = "Paid"
			return

		if self.is_main_travel_request():
			if payment_done and visa_done and ticket_done and clearance_done:
				self.status = "Completed"
			elif payment_done:
				self.status = "Paid"

	def validate_linked_document_ownership(self):
		link_map = {
			"linked_visa": "Employee Visa",
			"linked_payment_request": "Government Payment Request",
			"linked_ticket_request": "Travel Ticket Request",
			"linked_clearance": "Employee Clearance",
		}
		for fieldname, doctype in link_map.items():
			link_name = getattr(self, fieldname, None)
			if not link_name or not frappe.db.exists(doctype, link_name):
				continue
			values = frappe.db.get_value(doctype, link_name, ["employee", "leave_application"], as_dict=True) or {}
			if values.get("employee") and values.get("employee") != self.employee:
				frappe.throw(_("Linked document {0} does not belong to employee {1}.").format(link_name, self.employee))
			if self.leave_application and values.get("leave_application") and values.get("leave_application") != self.leave_application:
				frappe.throw(_("Linked document {0} does not belong to leave application {1}.").format(link_name, self.leave_application))

	def validate_dates(self):
		if self.due_date and self.request_date and getdate(self.due_date) < getdate(self.request_date):
			frappe.throw(_("Due Date cannot be before Request Date."))

	def ensure_status(self):
		if not self.status:
			self.status = "Draft" if self.docstatus == 0 else "Submitted"

	def track_status_change(self):
		if self.is_new():
			return
		previous = self.get_doc_before_save()
		if previous and previous.status != self.status:
			create_government_request_log(
				self,
				"Status Updated",
				self.status,
				_("Status changed from {0} to {1}").format(previous.status, self.status),
			)

	def update_linked_documents(self):
		if self.linked_visa and frappe.db.exists("Employee Visa", self.linked_visa):
			visa = frappe.get_doc("Employee Visa", self.linked_visa)
			if visa.status not in ("Cancelled", "Expired", "Used"):
				visa.status = "Issued"
				visa.save(ignore_permissions=True)

		if self.leave_application and frappe.db.exists("Leave Application", self.leave_application):
			frappe.db.set_value(
				"Leave Application",
				self.leave_application,
				"custom_gro_status",
				"Approved",
				update_modified=False,
			)

	def get_snapshot_values(self) -> dict[str, object]:
		return {
			"linked_visa": self.linked_visa,
			"linked_visa_status": self.linked_visa_status,
			"linked_payment_request": self.linked_payment_request,
			"linked_payment_request_status": self.linked_payment_request_status,
			"visa_amount": self.visa_amount,
			"linked_ticket_request": self.linked_ticket_request,
			"linked_ticket_request_status": self.linked_ticket_request_status,
			"linked_ticket_payment_request": self.linked_ticket_payment_request,
			"linked_ticket_payment_request_status": self.linked_ticket_payment_request_status,
			"ticket_amount": self.ticket_amount,
			"linked_clearance": self.linked_clearance,
			"linked_clearance_status": self.linked_clearance_status,
			"clearance_amount": self.clearance_amount,
			"custody_amount": self.custody_amount,
			"status": self.status,
			"completion_percent": self.completion_percent,
			"progress_summary": self.progress_summary,
		}


def sync_request_snapshot(request_name: str | None):
	if not request_name or not frappe.db.exists("Government Request", request_name):
		return

	request = frappe.get_doc("Government Request", request_name)
	request.resolve_linked_documents()
	request.populate_linked_statuses()
	request.populate_linked_summary_fields()
	request.sync_status_from_linked_documents()
	request.populate_progress_metrics()
	request.ensure_status()
	frappe.db.set_value("Government Request", request_name, request.get_snapshot_values(), update_modified=False)
