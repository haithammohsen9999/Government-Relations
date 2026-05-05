window.ksaGovernmentRelations = {
	getBadge(status) {
		const colorMap = {
			Paid: "green",
			"Posted to GL": "green",
			Cleared: "green",
			Completed: "green",
			Active: "green",
			Issued: "green",
			Valid: "green",
			Returned: "green",
			Requested: "blue",
			Submitted: "blue",
			"Under Review": "blue",
			"Government Processing": "blue",
			"Outside KSA": "blue",
			"Waiting Payment": "orange",
			"Waiting Approval": "orange",
			"Pending Finance Clearance": "orange",
			"Pending Asset Clearance": "orange",
			"Pending HR Clearance": "orange",
			"Pending Government Clearance": "orange",
			"Late Return Stage 1": "orange",
			"Late Return Stage 2": "red",
			"Late Return Stage 3": "red",
			Rejected: "red",
			Cancelled: "red",
			Expired: "red",
			Draft: "gray",
			"On Hold": "gray",
		};
		const color = colorMap[status] || "gray";
		return `<span class="ksa-gr-pill ${color}">${__(status || "Unknown")}</span>`;
	},

	renderCards(container, cards) {
		const html = cards
			.map(
				(card) => `
				<div class="ksa-gr-card">
					<div class="ksa-gr-subtle">${__(card.label)}</div>
					<div class="ksa-gr-kpi">${card.value ?? 0}</div>
				</div>
			`
			)
			.join("");
		container.html(`<div class="ksa-gr-grid">${html}</div>`);
	},

	renderTable(container, columns, rows) {
		if (!rows || !rows.length) {
			container.html(`<div class="ksa-gr-empty">${__("No data")}</div>`);
			return;
		}
		const head = columns.map((c) => `<th>${__(c.label)}</th>`).join("");
		const body = rows
			.map((row) => {
				const cells = columns
					.map((c) => {
						const value = row[c.fieldname];
						if (c.type === "badge") {
							return `<td>${window.ksaGovernmentRelations.getBadge(value)}</td>`;
						}
						if (c.type === "link" && value) {
							return `<td><a href="/app/${frappe.router.slug(c.doctype)}/${value}">${frappe.utils.escape_html(value)}</a></td>`;
						}
						return `<td>${frappe.utils.escape_html(value == null ? "" : String(value))}</td>`;
					})
					.join("");
				return `<tr>${cells}</tr>`;
			})
			.join("");
		container.html(`<div class="ksa-gr-panel"><table class="ksa-gr-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`);
	},
};
