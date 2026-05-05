from __future__ import annotations

import frappe


def execute():
	if not frappe.db.exists("DocType", "Employee Government Profile"):
		return

	from ksa_government_relations.utils import get_or_create_government_profile

	for employee in frappe.get_all("Employee", filters={"status": ["!=", "Left"]}, pluck="name"):
		try:
			get_or_create_government_profile(employee)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Failed creating Employee Government Profile for {employee}")
