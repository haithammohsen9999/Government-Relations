from __future__ import annotations

import frappe

from ksa_government_relations.constants import ROLE_GRO_MANAGER, ROLE_SELF_SERVICE


def is_restricted_self_service_user(user: str | None = None) -> bool:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	return ROLE_SELF_SERVICE in roles and "System Manager" not in roles and ROLE_GRO_MANAGER not in roles


def get_employee_for_user(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	return frappe.db.get_value("Employee", {"user_id": user}, "name")


def get_self_service_query_condition(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if not is_restricted_self_service_user(user):
		return None

	employee = get_employee_for_user(user)
	if not employee:
		return "1=0"

	return f"employee = {frappe.db.escape(employee)}"


def has_self_service_permission(doc, ptype=None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if not is_restricted_self_service_user(user):
		return True

	employee = get_employee_for_user(user)
	if not employee:
		return False

	return getattr(doc, "employee", None) == employee
