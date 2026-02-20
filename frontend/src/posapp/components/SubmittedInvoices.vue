<template>
	<v-dialog v-model="dialog" max-width="1200" persistent scrollable>
		<v-card>
			<v-card-title class="text-h5 d-flex align-center justify-space-between pa-4">
				<div class="d-flex align-center">
					<v-icon start color="primary" class="mr-2">mdi-receipt-text-check</v-icon>
					{{ __("Submitted Invoices") }}
				</div>
				<v-btn icon variant="text" @click="close">
					<v-icon>mdi-close</v-icon>
				</v-btn>
			</v-card-title>

			<v-divider></v-divider>

			<v-card-text class="pa-4">
				<!-- Date Filter -->
				<v-row class="mb-4">
					<v-col cols="12" md="6">
						<v-text-field
							v-model="selectedDate"
							type="date"
							:label="__('Date')"
							variant="outlined"
							density="compact"
							hide-details
							@update:modelValue="loadInvoices"
						></v-text-field>
					</v-col>
					<v-col cols="12" md="6" class="d-flex align-center">
						<v-btn
							color="primary"
							variant="flat"
							@click="loadInvoices"
							:loading="loading"
							prepend-icon="mdi-refresh"
						>
							{{ __("Refresh") }}
						</v-btn>
					</v-col>
				</v-row>

				<!-- Totals Summary -->
				<v-row v-if="!loading && invoices.length > 0" class="mb-4">
					<v-col cols="12" md="4">
						<v-card color="primary" variant="tonal">
							<v-card-text class="text-center">
								<div class="text-h6 font-weight-bold">{{ totals.total_invoices }}</div>
								<div class="text-caption">{{ __("Total Invoices") }}</div>
							</v-card-text>
						</v-card>
					</v-col>
					<v-col cols="12" md="4">
						<v-card color="success" variant="tonal">
							<v-card-text class="text-center">
								<div class="text-h6 font-weight-bold">{{ formatNumber(totals.total_qty) }}</div>
								<div class="text-caption">{{ __("Total Quantity") }}</div>
							</v-card-text>
						</v-card>
					</v-col>
					<v-col cols="12" md="4">
						<v-card color="info" variant="tonal">
							<v-card-text class="text-center">
								<div class="text-h6 font-weight-bold">{{ formatCurrency(totals.total_amount) }}</div>
								<div class="text-caption">{{ __("Total Amount") }}</div>
							</v-card-text>
						</v-card>
					</v-col>
				</v-row>

				<!-- Invoices Table -->
				<v-data-table
					:headers="headers"
					:items="invoices"
					:loading="loading"
					:items-per-page="10"
					class="elevation-1"
					density="comfortable"
				>
					<template v-slot:item.name="{ item }">
						<a @click.prevent="openInvoice(item.name)" class="text-primary" style="cursor: pointer">
							{{ item.name }}
						</a>
					</template>

					<template v-slot:item.posting_time="{ item }">
						{{ formatTime(item.posting_time) }}
					</template>

					<template v-slot:item.grand_total="{ item }">
						{{ formatCurrency(item.grand_total) }}
					</template>

					<template v-slot:item.total_qty="{ item }">
						{{ formatNumber(item.total_qty) }}
					</template>

					<template v-slot:item.status="{ item }">
						<v-chip :color="getStatusColor(item.status)" size="small" variant="flat">
							{{ item.status }}
						</v-chip>
					</template>

					<template v-slot:item.actions="{ item }">
						<v-btn
							icon
							size="small"
							variant="text"
							@click="openInvoice(item.name)"
							:title="__('View Invoice')"
						>
							<v-icon size="20">mdi-eye</v-icon>
						</v-btn>
						<v-btn
							icon
							size="small"
							variant="text"
							@click="printInvoice(item.name)"
							:title="__('Print Invoice')"
						>
							<v-icon size="20">mdi-printer</v-icon>
						</v-btn>
					</template>

					<template v-slot:no-data>
						<div class="text-center pa-4">
							<v-icon size="64" color="grey">mdi-receipt-text-outline</v-icon>
							<div class="text-h6 mt-2">{{ __("No invoices found") }}</div>
							<div class="text-caption text-grey">
								{{ __("No submitted invoices for the selected date") }}
							</div>
						</div>
					</template>
				</v-data-table>
			</v-card-text>

			<v-divider></v-divider>

			<v-card-actions class="pa-4">
				<v-spacer></v-spacer>
				<v-btn color="grey" variant="text" @click="close">
					{{ __("Close") }}
				</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script>
/* global frappe */
export default {
	name: "SubmittedInvoices",
	props: {
		modelValue: {
			type: Boolean,
			default: false,
		},
		posProfile: {
			type: Object,
			default: () => ({}),
		},
	},
	data() {
		return {
			dialog: false,
			loading: false,
			selectedDate: this.getCurrentDate(),
			invoices: [],
			totals: {
				total_invoices: 0,
				total_qty: 0,
				total_amount: 0,
			},
			headers: [
				{ title: this.__("Invoice"), key: "name", sortable: true },
				{ title: this.__("Time"), key: "posting_time", sortable: true },
				{ title: this.__("Customer"), key: "customer_name", sortable: true },
				{ title: this.__("Qty"), key: "total_qty", sortable: true, align: "end" },
				{ title: this.__("Amount"), key: "grand_total", sortable: true, align: "end" },
				{ title: this.__("Status"), key: "status", sortable: true },
				{ title: this.__("Actions"), key: "actions", sortable: false, align: "center" },
			],
		};
	},
	watch: {
		modelValue(val) {
			this.dialog = val;
			if (val) {
				this.loadInvoices();
			}
		},
		dialog(val) {
			this.$emit("update:modelValue", val);
		},
	},
	methods: {
		getCurrentDate() {
			const today = new Date();
			const year = today.getFullYear();
			const month = String(today.getMonth() + 1).padStart(2, "0");
			const day = String(today.getDate()).padStart(2, "0");
			return `${year}-${month}-${day}`;
		},

		async loadInvoices() {
			this.loading = true;
			try {
				const response = await frappe.call({
					method: "posawesome.posawesome.api.submitted_invoices.get_submitted_invoices",
					args: {
						date: this.selectedDate,
						pos_profile: this.posProfile?.name || null,
					},
				});

				if (response?.message) {
					this.invoices = response.message.invoices || [];
					this.totals = response.message.totals || {
						total_invoices: 0,
						total_qty: 0,
						total_amount: 0,
					};
				}
			} catch (error) {
				console.error("Error loading invoices:", error);
				frappe.show_alert({
					message: this.__("Failed to load invoices"),
					indicator: "red",
				});
			} finally {
				this.loading = false;
			}
		},

		openInvoice(name) {
			const doctype = this.posProfile?.create_pos_invoice_instead_of_sales_invoice
				? "POS Invoice"
				: "Sales Invoice";
			frappe.set_route("Form", doctype, name);
		},

		printInvoice(name) {
			const print_format =
				this.posProfile?.print_format_for_online || this.posProfile?.print_format || "Standard";
			const letter_head = this.posProfile?.letter_head || 0;
			const doctype = this.posProfile?.create_pos_invoice_instead_of_sales_invoice
				? "POS Invoice"
				: "Sales Invoice";

			const url =
				frappe.urllib.get_base_url() +
				"/printview?doctype=" +
				encodeURIComponent(doctype) +
				"&name=" +
				encodeURIComponent(name) +
				"&trigger_print=1" +
				"&format=" +
				encodeURIComponent(print_format) +
				"&no_letterhead=" +
				letter_head;

			const printWindow = window.open(url, "Print");
			if (printWindow) {
				printWindow.addEventListener(
					"load",
					function () {
						printWindow.print();
					},
					{ once: true },
				);
			}
		},

		formatCurrency(value) {
			if (typeof value === "undefined" || value === null) return "0.00";
			return Number(value).toLocaleString("en-US", {
				minimumFractionDigits: 2,
				maximumFractionDigits: 2,
			});
		},

		formatNumber(value) {
			if (typeof value === "undefined" || value === null) return "0";
			return Number(value).toLocaleString("en-US", {
				minimumFractionDigits: 0,
				maximumFractionDigits: 2,
			});
		},

		formatTime(time) {
			if (!time) return "";
			// Convert HH:MM:SS to HH:MM AM/PM
			const [hours, minutes] = time.split(":");
			const hour = parseInt(hours);
			const ampm = hour >= 12 ? "PM" : "AM";
			const displayHour = hour % 12 || 12;
			return `${displayHour}:${minutes} ${ampm}`;
		},

		getStatusColor(status) {
			const colorMap = {
				Paid: "success",
				Unpaid: "warning",
				"Return": "error",
				"Credit Note Issued": "info",
			};
			return colorMap[status] || "grey";
		},

		close() {
			this.dialog = false;
		},

		__(text) {
			return window.__ ? window.__(text) : text;
		},
	},
};
</script>

<style scoped>
.text-primary {
	color: #1976d2;
	text-decoration: none;
}

.text-primary:hover {
	text-decoration: underline;
}

:deep(.v-data-table) {
	border-radius: 8px;
}

:deep(.v-data-table-header) {
	background-color: #f5f5f5;
}

:deep([data-theme="dark"]) .v-data-table-header,
:deep(.v-theme--dark) .v-data-table-header {
	background-color: #2d2d2d;
}
</style>
