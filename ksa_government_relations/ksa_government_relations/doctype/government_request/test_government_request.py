import frappe
from frappe.tests.utils import FrappeTestCase


class TestGovernmentRequest(FrappeTestCase):
	def test_main_request_does_not_auto_complete_without_links(self):
		doc = frappe.get_doc(
			{
				"doctype": "Government Request",
				"request_type": "Outside KSA Leave Processing",
				"status": "Draft",
			}
		)

		doc.sync_status_from_linked_documents()

		self.assertEqual(doc.status, "Draft")

	def test_visa_request_waits_for_real_payment_status(self):
		doc = frappe.get_doc(
			{
				"doctype": "Government Request",
				"request_type": "Issue Exit Re-entry Visa",
				"status": "Draft",
				"linked_visa": "EMP-VISA-TEST",
				"linked_visa_status": "Requested",
				"linked_payment_request": "GPR-TEST",
				"linked_payment_request_status": "Waiting Payment",
			}
		)

		doc.sync_status_from_linked_documents()

		self.assertEqual(doc.status, "Draft")
