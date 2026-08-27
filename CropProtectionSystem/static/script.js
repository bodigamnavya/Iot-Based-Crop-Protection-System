// ============================================================
// AI Crop Protection System — Frontend JavaScript
// ============================================================
// Uses API_BASE_URL from config.js (loaded before this script)

/**
 * Fetch JSON from the Flask API.
 * @param {string} endpoint  e.g. "/api/status"
 * @returns {Promise<any>}
 */
async function apiFetch(endpoint) {
    const url = API_BASE_URL.replace(/\/+$/, "") + endpoint;
    const res = await fetch(url, { mode: "cors" });
    if (!res.ok) throw new Error(`API ${res.status}`);
    return res.json();
}

// ============================================================
// Dashboard (index.html)
// ============================================================

async function loadDashboard() {
    const statusDot  = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");

    // Detection card
    const elAnimal     = document.getElementById("val-animal");
    const elConfidence = document.getElementById("val-confidence");
    const elDetStatus  = document.getElementById("val-det-status");

    // Water card
    const elSoil = document.getElementById("val-soil");
    const elPump = document.getElementById("val-pump");

    try {
        const data = await apiFetch("/api/status");

        // Status bar
        statusDot.classList.remove("offline");
        statusText.textContent = "System Online — Backend Connected";

        // Animal detection
        if (elAnimal) {
            elAnimal.textContent = data.animal || "No Animal";
            elAnimal.className = "data-value" +
                (data.animal && data.animal !== "No Animal" ? " danger" : " highlight");
        }
        if (elConfidence) {
            const conf = data.confidence || 0;
            elConfidence.textContent = conf + "%";
            elConfidence.className = "data-value" +
                (conf >= 60 ? " warning" : " highlight");
        }
        if (elDetStatus) {
            elDetStatus.innerHTML = '<span class="badge badge-active">Active</span>';
        }

        // Water management
        if (elSoil) {
            elSoil.textContent = data.soil != null ? data.soil : "—";
        }
        if (elPump) {
            const isOn = data.pump && data.pump.toLowerCase() === "on";
            elPump.innerHTML = isOn
                ? '<span class="badge badge-on">ON</span>'
                : '<span class="badge badge-off">OFF</span>';
        }

    } catch (err) {
        console.error("Dashboard fetch error:", err);
        statusDot.classList.add("offline");
        statusText.textContent = "Backend Offline — Cannot reach API";
    }
}

// ============================================================
// Detection History (history.html)
// ============================================================

async function loadHistory() {
    const tbody   = document.getElementById("history-body");
    const loading = document.getElementById("loading");
    const empty   = document.getElementById("empty-state");

    if (!tbody) return;

    try {
        const data = await apiFetch("/api/history");

        if (loading) loading.style.display = "none";

        if (!data || data.length === 0) {
            if (empty) empty.style.display = "block";
            return;
        }

        for (const row of data) {
            const tr = document.createElement("tr");
            tr.innerHTML =
                "<td>" + escapeHtml(row.animal || "—") + "</td>" +
                "<td>" + (row.confidence != null ? Number(row.confidence).toFixed(2) : "—") + "</td>" +
                "<td>" + escapeHtml(row.time || "—") + "</td>" +
                "<td>" + escapeHtml(row.status || "—") + "</td>";
            tbody.appendChild(tr);
        }

    } catch (err) {
        console.error("History fetch error:", err);
        if (loading) loading.style.display = "none";
        if (empty) {
            empty.querySelector("p").textContent = "Could not load history — backend may be offline.";
            empty.style.display = "block";
        }
    }
}

// ============================================================
// Water History (water_history.html)
// ============================================================

async function loadWaterHistory() {
    const tbody   = document.getElementById("water-body");
    const loading = document.getElementById("loading");
    const empty   = document.getElementById("empty-state");

    if (!tbody) return;

    try {
        const data = await apiFetch("/api/water_history");

        if (loading) loading.style.display = "none";

        if (!data || data.length === 0) {
            if (empty) empty.style.display = "block";
            return;
        }

        for (const row of data) {
            const tr = document.createElement("tr");
            tr.innerHTML =
                "<td>" + escapeHtml(String(row.soil_moisture ?? "—")) + "</td>" +
                "<td>" + escapeHtml(row.pump_status || "—") + "</td>" +
                "<td>" + escapeHtml(row.time || "—") + "</td>";
            tbody.appendChild(tr);
        }

    } catch (err) {
        console.error("Water history fetch error:", err);
        if (loading) loading.style.display = "none";
        if (empty) {
            empty.querySelector("p").textContent = "Could not load water history — backend may be offline.";
            empty.style.display = "block";
        }
    }
}

// ============================================================
// Helpers
// ============================================================

function escapeHtml(str) {
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

// ============================================================
// Auto-refresh dashboard every 10 seconds
// ============================================================

function startAutoRefresh(fn, intervalMs) {
    fn();
    setInterval(fn, intervalMs);
}
