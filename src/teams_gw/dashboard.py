from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

import aiohttp
from fastapi.responses import HTMLResponse

ROLE_META = {
    "supervisor": {
        "label": "Supervisor de Mesa",
        "description": "Visibilidad de recordatorios al técnico y escalaciones iniciales.",
        "color": "#2563eb",
        "levels": [
            {"key": "recordatorio_tecnico", "label": "Recordatorios a técnicos"},
            {"key": "Escalamiento_Supervisor", "label": "Escalaciones activas"},
        ],
        "notification_roles": ["tecnico", "supervisor_mesa"],
    },
    "jefe_operacion": {
        "label": "Jefe de Operaciones",
        "description": "Alertas operativas que requieren coordinación inmediata.",
        "color": "#f97316",
        "levels": [
            {"key": "alerta_jefe_operacion", "label": "Alertas operativas"},
        ],
        "notification_roles": ["jefe_operacion"],
    },
    "jefe_servicios": {
        "label": "Jefe de Servicios",
        "description": "Escalaciones avanzadas que impactan el backlog crítico.",
        "color": "#059669",
        "levels": [
            {"key": "alerta_jefe_servicios", "label": "Escalaciones avanzadas"},
        ],
        "notification_roles": ["jefe_servicios"],
    },
    "gerente": {
        "label": "Gerente de TI",
        "description": "Resumen ejecutivo del estado del controller y backlog crítico.",
        "color": "#7c3aed",
        "levels": [
            {"key": "alerta_gerencia", "label": "Alertas ejecutivas"},
        ],
        "notification_roles": ["gerente_servicios", "gerente"],
    },
}


def normalize_roles(config_value: str) -> List[str]:
    roles = [item.strip() for item in (config_value or "").split(",") if item.strip()]
    return [role for role in roles if role in ROLE_META]


async def fetch_controller_metrics(url: str) -> Dict[str, Any]:
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()


def build_dashboard_payload(raw: Dict[str, Any], allowed_roles: List[str]) -> Dict[str, Any]:
    levels = raw.get("levels") or {}
    notifications = raw.get("recent_notifications") or []
    runs = raw.get("recent_runs") or []
    summary = raw.get("summary") or {}

    roles_payload: Dict[str, Any] = {}
    for role_key in allowed_roles:
        meta = ROLE_META.get(role_key)
        if not meta:
            continue
        level_entries = []
        total_alerts = 0
        for level in meta["levels"]:
            count = int(levels.get(level["key"], 0) or 0)
            level_entries.append({"key": level["key"], "label": level["label"], "count": count})
            total_alerts += count
        role_notifications = [
            {
                "ticket_id": item.get("ticket_id"),
                "nivel": item.get("nivel"),
                "rol": item.get("rol"),
                "canal": item.get("canal"),
                "fecha": item.get("fecha"),
                "resultado": item.get("resultado"),
            }
            for item in notifications
            if item.get("rol") in meta["notification_roles"]
        ][:6]
        roles_payload[role_key] = {
            "label": meta["label"],
            "description": meta["description"],
            "color": meta["color"],
            "levels": level_entries,
            "total_alerts": total_alerts,
            "notifications": role_notifications,
        }

    return {
        "summary": summary,
        "roles": roles_payload,
        "runs": runs,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }


def render_dashboard_html(roles: List[str]) -> HTMLResponse:
    config = {
        "roles": roles,
        "labels": {key: ROLE_META[key]["label"] for key in roles if key in ROLE_META},
        "colors": {key: ROLE_META[key]["color"] for key in roles if key in ROLE_META},
    }
    html = DASHBOARD_TEMPLATE.replace("__DASHBOARD_CONFIG__", json.dumps(config))
    return HTMLResponse(html)


ROWS_FOOTER = ""

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Controller Dashboard</title>
    <style>
      :root {
        color-scheme: light;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background-color: #f5f6fb;
      }
      body {
        margin: 0;
        padding: 0;
        background: #f5f6fb;
        color: #0f172a;
      }
      .dashboard {
        max-width: 1280px;
        margin: 0 auto;
        padding: 32px 24px 48px;
      }
      header {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: flex-end;
        gap: 16px;
      }
      header h1 {
        font-size: 28px;
        margin: 0;
        color: #0f172a;
      }
      header p {
        margin: 0;
        color: #64748b;
      }
      .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-top: 24px;
      }
      .card {
        background: #fff;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .card h3 {
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin: 0;
      }
      .card .value {
        font-size: 32px;
        font-weight: 600;
        color: #0f172a;
      }
      .card .muted {
        font-size: 13px;
        color: #94a3b8;
      }
      .chart-card {
        margin-top: 24px;
        background: #fff;
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
      }
      .tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 32px;
      }
      .tab {
        border: none;
        background: #e2e8f0;
        color: #475569;
        padding: 10px 18px;
        border-radius: 999px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
      }
      .tab.active {
        background: #0f172a;
        color: #fff;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.25);
      }
      .role-panel {
        margin-top: 20px;
        background: #fff;
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
      }
      .role-header {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 16px;
        border-left: 6px solid #2563eb;
        padding-left: 16px;
      }
      .role-header h2 {
        margin: 0;
        font-size: 22px;
      }
      .role-header p {
        margin: 4px 0 0;
        color: #64748b;
      }
      .role-kpi {
        text-align: right;
      }
      .role-kpi .number {
        font-size: 36px;
        font-weight: 600;
      }
      .level-grid {
        margin-top: 20px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
      }
      .level-card {
        background: #f8fafc;
        border-radius: 14px;
        padding: 16px;
        border: 1px solid #e2e8f0;
      }
      .level-card h4 {
        margin: 0;
        color: #475569;
        font-size: 14px;
      }
      .level-card .count {
        margin-top: 8px;
        font-size: 28px;
        font-weight: 600;
        color: #0f172a;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 24px;
        font-size: 14px;
      }
      th, td {
        padding: 12px 8px;
        text-align: left;
      }
      th {
        font-size: 13px;
        color: #94a3b8;
        font-weight: 500;
        border-bottom: 1px solid #e2e8f0;
      }
      tr + tr td {
        border-top: 1px solid #f1f5f9;
      }
      .badge {
        display: inline-flex;
        align-items: center;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 12px;
        background: #e2e8f0;
        color: #475569;
      }
      .empty-state {
        padding: 24px;
        text-align: center;
        color: #94a3b8;
      }
      @media (max-width: 768px) {
        header {
          flex-direction: column;
          align-items: flex-start;
        }
        .role-header {
          flex-direction: column;
          align-items: flex-start;
        }
        .role-kpi {
          text-align: left;
        }
      }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js"></script>
  </head>
  <body>
    <div class="dashboard">
      <header>
        <div>
          <h1>Controller Dashboard</h1>
          <p id="last-updated">Actualizando…</p>
        </div>
      </header>
      <section class="summary-grid">
        <div class="card">
          <h3>corridas totales</h3>
          <div class="value" id="kpi-runs">-</div>
          <div class="muted">Histórico del controller</div>
        </div>
        <div class="card">
          <h3>tickets monitoreados</h3>
          <div class="value" id="kpi-tickets">-</div>
          <div class="muted">Tickets con alguna regla disparada</div>
        </div>
        <div class="card">
          <h3>alertas hoy</h3>
          <div class="value" id="kpi-alerts-today">-</div>
          <div class="muted">Acciones ejecutadas en las últimas 24h</div>
        </div>
        <div class="card">
          <h3>última corrida</h3>
          <div class="value" id="kpi-last-run">-</div>
          <div class="muted">UTC</div>
        </div>
      </section>
      <section class="chart-card">
        <h3 style="margin-bottom:12px;color:#475569;">Histórico de corridas</h3>
        <canvas id="runs-chart" height="120"></canvas>
      </section>
      <section>
        <div class="tabs" id="role-tabs"></div>
        <div id="role-panel"></div>
      </section>
    </div>
    <script>
      const DASHBOARD_CONFIG = __DASHBOARD_CONFIG__;
      const state = {
        data: null,
        activeRole: DASHBOARD_CONFIG.roles[0] || null,
        chart: null,
      };

      function formatDate(value) {
        if (!value) return "-";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString("es-PE", {
          dateStyle: "medium",
          timeStyle: "short",
        });
      }

      function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
      }

      async function loadData() {
        try {
          const response = await fetch("/dashboard/data");
          if (!response.ok) throw new Error("No se pudo obtener la data");
          const payload = await response.json();
          state.data = payload;
          renderSummary();
          renderTabs();
          renderChart();
          renderRole(state.activeRole);
        } catch (err) {
          console.error(err);
          const panel = document.getElementById("role-panel");
          if (panel) {
            panel.innerHTML =
              "<div class='role-panel'><div class='empty-state'>No pudimos cargar la información del controller.</div></div>";
          }
        }
      }

      function renderSummary() {
        const summary = state.data.summary || {};
        setText("kpi-runs", summary.runs ?? 0);
        setText("kpi-tickets", summary.tickets_monitored ?? 0);
        setText("kpi-alerts-today", summary.alerts_today ?? 0);
        setText("kpi-last-run", formatDate(summary.last_run_finished_at));
        setText("last-updated", "Actualizado: " + formatDate(state.data.refreshed_at));
      }

      function renderTabs() {
        const container = document.getElementById("role-tabs");
        container.innerHTML = "";
        if (!DASHBOARD_CONFIG.roles.length) {
          container.innerHTML = "<p class='muted'>No hay roles configurados.</p>";
          return;
        }
        DASHBOARD_CONFIG.roles.forEach((role) => {
          const button = document.createElement("button");
          button.className = "tab" + (role === state.activeRole ? " active" : "");
          button.textContent = DASHBOARD_CONFIG.labels[role] || role;
          button.addEventListener("click", () => {
            state.activeRole = role;
            document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
            button.classList.add("active");
            renderRole(role);
          });
          container.appendChild(button);
        });
      }

      function renderChart() {
        const ctx = document.getElementById("runs-chart");
        if (!ctx) return;
        const runs = state.data.runs || [];
        const labels = runs.map((item) => formatDate(item.fecha_inicio));
        const values = runs.map((item) => item.tickets || 0);
        if (state.chart) {
          state.chart.data.labels = labels;
          state.chart.data.datasets[0].data = values;
          state.chart.update();
          return;
        }
        state.chart = new Chart(ctx, {
          type: "line",
          data: {
            labels,
            datasets: [
              {
                label: "Tickets procesados",
                data: values,
                fill: true,
                borderColor: "#6366f1",
                backgroundColor: "rgba(99,102,241,0.1)",
                tension: 0.4,
              },
            ],
          },
          options: {
            plugins: {
              legend: { display: false },
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  precision: 0,
                },
              },
            },
          },
        });
      }

      function renderRole(roleKey) {
        const container = document.getElementById("role-panel");
        const roleData = (state.data.roles || {})[roleKey];
        if (!roleData) {
          container.innerHTML =
            "<div class='role-panel'><div class='empty-state'>Sin datos disponibles para este rol.</div></div>";
          return;
        }
        const levels = roleData.levels
          .map(
            (lvl) => `
            <div class="level-card">
              <h4>${lvl.label}</h4>
              <div class="count">${lvl.count}</div>
            </div>
          `,
          )
          .join("");
        const rows =
          (roleData.notifications || [])
            .map(
              (item) => `
            <tr>
              <td>#${item.ticket_id || "-"}</td>
              <td><span class="badge">${item.nivel || "-"}</span></td>
              <td>${item.canal || "-"}</td>
              <td>${formatDate(item.fecha)}</td>
            </tr>
          `,
            )
            .join("") || "<tr><td colspan='4' class='empty-state'>Sin alertas recientes.</td></tr>";
        container.innerHTML = `
          <div class="role-panel">
            <div class="role-header" style="border-color: ${roleData.color};">
              <div>
                <h2>${roleData.label}</h2>
                <p>${roleData.description}</p>
              </div>
              <div class="role-kpi">
                <div class="number">${roleData.total_alerts}</div>
                <div class="muted">Alertas vigentes</div>
              </div>
            </div>
            <div class="level-grid">${levels}</div>
            <table>
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Nivel</th>
                  <th>Canal</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        `;
      }

      document.addEventListener("DOMContentLoaded", loadData);
    </script>
  </body>
</html>
"""
