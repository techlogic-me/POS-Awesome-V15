# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, nowdate, flt


@frappe.whitelist()
def get_submitted_invoices(date=None, pos_profile=None):
	"""
	Fetch submitted Sales Invoices filtered by is_pos=1 for a given date.
	Returns list of invoices with totals.
	
	Args:
		date: Date to filter invoices (defaults to today)
		pos_profile: POS Profile name to filter (optional)
	
	Returns:
		dict: {
			'invoices': List of invoice details,
			'totals': {
				'total_qty': Total quantity sold,
				'total_amount': Total grand total,
				'total_invoices': Count of invoices
			}
		}
	"""
	if not date:
		date = nowdate()
	else:
		date = getdate(date)
	
	filters = {
		"docstatus": 1,  # Submitted
		"is_pos": 1,
		"posting_date": date
	}
	
	if pos_profile:
		filters["pos_profile"] = pos_profile
	
	fields = [
		"name",
		"customer",
		"customer_name",
		"posting_date",
		"posting_time",
		"grand_total",
		"total_qty",
		"status",
		"pos_profile",
		"modified",
		"owner"
	]
	
	invoices = frappe.get_all(
		"Sales Invoice",
		filters=filters,
		fields=fields,
		order_by="posting_time desc, creation desc"
	)
	
	# Calculate totals
	total_qty = 0
	total_amount = 0
	
	for invoice in invoices:
		total_qty += flt(invoice.get("total_qty", 0))
		total_amount += flt(invoice.get("grand_total", 0))
	
	return {
		"invoices": invoices,
		"totals": {
			"total_qty": total_qty,
			"total_amount": total_amount,
			"total_invoices": len(invoices)
		}
	}
