import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class VisaPricingRule(Document):
	def validate(self):
		if flt(self.minimum_days) <= 0:
			self.minimum_days = None
		if flt(self.maximum_days) <= 0:
			self.maximum_days = None
		if flt(self.duration_days) <= 0:
			self.duration_days = 0
		if flt(self.minimum_days) < 0 or flt(self.maximum_days) < 0 or flt(self.duration_days) < 0:
			frappe.throw(_("Visa pricing days cannot be negative."))
		if self.minimum_days and self.maximum_days and flt(self.maximum_days) < flt(self.minimum_days):
			frappe.throw(_("Maximum Days cannot be less than Minimum Days."))
		if self.minimum_days or self.maximum_days:
			# Keep legacy exact-day field only for backward compatibility.
			self.duration_days = 0
