from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from ksa_government_relations.utils import get_employee_core_details, get_employee_nationality, refresh_profile_status, sync_profile_to_employee


class EmployeeGovernmentProfile(Document):
	def validate(self):
		self.populate_from_employee()
		self.validate_unique_employee()
		refresh_profile_status(self)

	def on_update(self):
		sync_profile_to_employee(self)

	def populate_from_employee(self):
		if not self.employee:
			return

		employee = get_employee_core_details(self.employee)
		if not employee:
			frappe.throw(_("Employee {0} was not found.").format(self.employee))

		self.employee_name = employee.get("employee_name")
		self.company = employee.get("company")
		self.branch = employee.get("branch")
		self.department = employee.get("department")
		self.designation = employee.get("designation")
		self.nationality = get_employee_nationality(employee)
		self.identity_type = employee.get("custom_identity_type") or self.identity_type or "Resident"
		self.government_portal = employee.get("custom_government_portal") or self.government_portal or "Muqeem"
		self.iqama_number = employee.get("custom_iqama_number")
		self.iqama_issue_date = employee.get("custom_iqama_issue_date")
		self.iqama_expiry_date = employee.get("custom_iqama_expiry_date")
		self.passport_number = employee.get("custom_passport_number")
		self.passport_issue_date = employee.get("custom_passport_issue_date")
		self.passport_expiry_date = employee.get("custom_passport_expiry_date")
		self.passport_issue_place = employee.get("custom_passport_issue_place")
		self.current_sponsor = employee.get("custom_current_sponsor")
		self.qiwa_balance = employee.get("custom_qiwa_balance") or 0
		self.is_outside_ksa = employee.get("custom_is_outside_ksa") or 0
		self.last_exit_date = employee.get("custom_last_exit_date")
		self.expected_return_date = employee.get("custom_expected_return_date")
		self.actual_return_date = employee.get("custom_actual_return_date")
		if not self.identity_type:
			self.identity_type = "Resident"

	def validate_unique_employee(self):
		if not self.employee:
			return
		existing = frappe.db.get_value(
			"Employee Government Profile",
			{"employee": self.employee, "name": ["!=", self.name]},
			"name",
		)
		if existing:
			frappe.throw(_("Employee Government Profile already exists for employee {0}.").format(self.employee))
