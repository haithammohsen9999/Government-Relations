from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeCustody(Document):
	def validate(self):
		if not self.employee:
			frappe.throw(_("Employee is required."))
		self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
		if self.asset and frappe.db.exists("Asset", self.asset):
			asset_details = frappe.db.get_value("Asset", self.asset, ["asset_name", "gross_purchase_amount"], as_dict=True)
			if asset_details:
				self.description = self.description or asset_details.asset_name
				self.estimated_value = self.estimated_value or asset_details.gross_purchase_amount
		if not self.status:
			self.status = "Issued"
