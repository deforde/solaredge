import os
from typing import Any

from flask import Flask, jsonify, render_template_string, request

from solaredge.database.database import DATABASE_FILE, Database


DASHBOARD_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>SolarEdge measurements</title>
	<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
	<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
	<style>
		:root { color-scheme: light; font-family: system-ui, sans-serif; }
		body { margin: 0; background: #f3f5f7; color: #17202a; }
		main { width: min(1100px, 100% - 2rem); margin: 1rem auto 3rem; }
		h1 { font-size: clamp(1.4rem, 5vw, 2.2rem); margin: 0 0 1rem; }
		.toolbar { display: flex; flex-wrap: wrap; gap: .75rem; margin-bottom: 1rem; }
		.toolbar label { display: grid; gap: .25rem; font-size: .85rem; }
		input, button { font: inherit; padding: .55rem .7rem; border: 1px solid #bac3cc; border-radius: .35rem; }
		button { cursor: pointer; background: #1769aa; color: white; border-color: #1769aa; }
		.panel { background: white; border: 1px solid #d9e0e6; border-radius: .5rem; padding: 1rem; margin-bottom: 1rem; }
		.chart { position: relative; height: min(55vw, 360px); min-height: 240px; }
		#status { color: #52606d; min-height: 1.25rem; }
	</style>
</head>
<body>
<main>
	<h1>SolarEdge measurements</h1>
	<form class="toolbar" id="range-form">
		<label>From <input type="datetime-local" id="start"></label>
		<label>To <input type="datetime-local" id="end"></label>
		<button type="submit">Refresh</button>
	</form>
	<p id="status" role="status"></p>
	<section class="panel"><div class="chart"><canvas id="power-chart"></canvas></div></section>
	<section class="panel"><div class="chart"><canvas id="electrical-chart"></canvas></div></section>
</main>
<script>
let powerChart;
let electricalChart;

function timestampFromInput(id) {
	const value = document.getElementById(id).value;
	return value ? Math.floor(new Date(value).getTime() / 1000) : null;
}

async function refreshCharts(event) {
	if (event) event.preventDefault();
	const params = new URLSearchParams();
	const start = timestampFromInput("start");
	const end = timestampFromInput("end");
	if (start !== null) params.set("start", start);
	if (end !== null) params.set("end", end);

	const response = await fetch(`/api/measurements?${params}`);
	const measurements = await response.json();
	if (!response.ok) throw new Error(measurements.error || "Could not load measurements");
	const labels = measurements.map(row => new Date(row.timestamp * 1000));
	const common = { pointRadius: 1, tension: .2, spanGaps: true };

	powerChart?.destroy();
	electricalChart?.destroy();
	powerChart = new Chart(document.getElementById("power-chart"), {
		type: "line",
		data: { labels, datasets: [{ ...common, label: "Power (W)", data: measurements.map(row => row.power), borderColor: "#e4572e", backgroundColor: "#e4572e" }] },
		options: { responsive: true, maintainAspectRatio: false, scales: { x: { type: "time", time: { tooltipFormat: "PPp" } }, y: { beginAtZero: true } } }
	});
	electricalChart = new Chart(document.getElementById("electrical-chart"), {
		type: "line",
		data: { labels, datasets: [
			{ ...common, label: "Current (A)", data: measurements.map(row => row.current), borderColor: "#2e86ab" },
			{ ...common, label: "Voltage (V)", data: measurements.map(row => row.voltage), borderColor: "#4caf50" },
			{ ...common, label: "Frequency (Hz)", data: measurements.map(row => row.frequency), borderColor: "#8e6c8a" }
		] },
		options: { responsive: true, maintainAspectRatio: false, scales: { x: { type: "time", time: { tooltipFormat: "PPp" } } } }
	});
	document.getElementById("status").textContent = `${measurements.length} measurements loaded`;
}

document.getElementById("range-form").addEventListener("submit", refreshCharts);
refreshCharts().catch(error => { document.getElementById("status").textContent = error.message; });
</script>
</body>
</html>
"""


def create_app(database_file: str = DATABASE_FILE) -> Flask:
		app = Flask(__name__)

		@app.get("/")
		def dashboard() -> str:
				return render_template_string(DASHBOARD_TEMPLATE)

		@app.get("/api/measurements")
		def measurements() -> Any:
				try:
						start = request.args.get("start", type=int)
						end = request.args.get("end", type=int)
						if start is not None and end is not None and start > end:
								return jsonify({"error": "start must not be later than end"}), 400

						with Database(database_file) as database:
								rows = database.get_measurements(start, end)
						return jsonify([
								{
										"timestamp": timestamp,
										"power": power,
										"current": current,
										"voltage": voltage,
										"frequency": frequency,
								}
								for timestamp, power, current, voltage, frequency in rows
						])
				except Exception:
						app.logger.exception("Could not load measurements")
						return jsonify({"error": "Could not load measurements"}), 500

		return app


def main() -> None:
		host = os.getenv("SOLAREDGE_DASHBOARD_HOST", "0.0.0.0")
		port = int(os.getenv("SOLAREDGE_DASHBOARD_PORT", "5000"))
		create_app().run(host=host, port=port)

if __name__ == "__main__":
		main()
