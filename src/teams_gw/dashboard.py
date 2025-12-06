from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

import aiohttp
from fastapi.responses import HTMLResponse

ROLE_META = {
    "supervisor": {
        "label": "Supervisor de Mesa",
        "description": "Casos que ameritan revisión a nivel de Supervisión",
        "color": "#2563eb",
        "levels": [
            {"key": "recordatorio_tecnico", "label": "Tickets sin Inicio de Atención"},
            {"key": "Escalamiento_Supervisor", "label": "Tickets proximos a escalar al siguiente Nivel"},
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

LEVEL_LABELS = {
    "recordatorio_tecnico": "Recordatorio al Analista",
    "escalamiento_supervisor": "Escalamiento al Supervisor",
    "escalamiento_al_supervisor": "Escalamiento al Supervisor",
    "escalamiento": "Escalamiento al Supervisor",
    "escalamiento_supervisor_mesa": "Escalamiento al Supervisor",
    "escalamiento supervisor": "Escalamiento al Supervisor",
    "escalamiento supervisor mesa": "Escalamiento al Supervisor",
    "escalamiento supervisor_mesa": "Escalamiento al Supervisor",
    "escalamiento_supervisor_mesa": "Escalamiento al Supervisor",
    "Escalamiento_Supervisor": "Escalamiento al Supervisor",
    "alerta_jefe_operacion": "Alerta Jefe de Operaciones",
    "alerta_jefe_servicios": "Alerta Jefe de Servicios",
    "alerta_gerencia": "Alerta Gerencia",
    "pausa_cliente_supervisor": "Pausa por Cliente (Supervisor)",
    "pausa_cliente_jefe": "Pausa por cliente (Jefe de Operaciones)",
    "pausa_proveedor_supervisor": "Pausa por Proveedor (Supervisor)",
    "pausa_proveedor_jefe": "Pausa por Proveedor (Jefe de operaciones)",
    "pausa_interna_supervisor": "Pausa Interna (Supervisor)",
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


async def fetch_controller_generic(url: str) -> Dict[str, Any]:
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
    role_insights = raw.get("role_insights") or {}
    backlog_delta = raw.get("backlog_delta") or {}
    active_reminders = raw.get("active_reminders") or []
    fired_reminders = raw.get("fired_reminders") or {"count": 0, "items": []}
    snapshot = raw.get("snapshot") or {}
    assigned_snapshot = snapshot.get("assigned") if isinstance(snapshot, dict) else {}
    at_risk_near: List[Dict[str, Any]] = []
    if isinstance(snapshot, dict):
        combined = (snapshot.get("at_risk_active") or []) + (snapshot.get("at_risk_pause") or [])
        for item in combined:
            try:
                ratio_val = float(item.get("ratio", 0) or 0)
            except (TypeError, ValueError):
                ratio_val = 0.0
            if 0.75 <= ratio_val < 1:
                at_risk_near.append(item)
    role_panels = raw.get("role_panels") or {}

    roles_payload: Dict[str, Any] = {}
    for role_key in allowed_roles:
        meta = ROLE_META.get(role_key)
        if not meta:
            continue
        level_entries = []
        total_alerts = 0
        for level in meta["levels"]:
            # Override recordatorio_tecnico count with assigned_snapshot.count if available
            if level["key"] == "recordatorio_tecnico":
                count = int(assigned_snapshot.get("count", 0) or 0)
            elif level["key"] == "Escalamiento_Supervisor":
                count = len(at_risk_near)
            else:
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
        "insights": role_insights,
        "backlog": backlog_delta,
        "active_reminders": active_reminders,
        "fired_reminders": fired_reminders,
        "snapshot": snapshot,
        "at_risk_near": at_risk_near,
        "role_panels": role_panels,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }


def render_dashboard_html(roles: List[str]) -> HTMLResponse:
    config = {
        "roles": roles,
        "labels": {key: ROLE_META[key]["label"] for key in roles if key in ROLE_META},
        "colors": {key: ROLE_META[key]["color"] for key in roles if key in ROLE_META},
    }
    html = (
        DASHBOARD_TEMPLATE.replace("__DASHBOARD_CONFIG__", json.dumps(config))
        .replace("__LEVEL_LABELS__", json.dumps(LEVEL_LABELS))
    )
    return HTMLResponse(html)


def render_service_dashboard_html() -> HTMLResponse:
    html = SERVICE_TEMPLATE
    return HTMLResponse(html)


def render_risk_dashboard_html() -> HTMLResponse:
    return HTMLResponse(RISK_TEMPLATE)


ROWS_FOOTER = ""

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Backlog & Alertas</title>
    <style>
      :root {
        color-scheme: dark;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background-color: #0b1224;
      }
      body {
        margin: 0;
        padding: 0;
        background: radial-gradient(circle at 10% 20%, rgba(37, 99, 235, 0.12), transparent 25%),
                    radial-gradient(circle at 90% 10%, rgba(16, 185, 129, 0.14), transparent 22%),
                    #0b1224;
        color: #e2e8f0;
        width: 100%;
        overflow-x: hidden;
      }
      .dashboard {
        max-width: 1000px;
        margin: 0 auto;
        padding: 12px 12px 28px;
        width: 100%;
      }
      .gerente-wide .dashboard {
        max-width: 96vw;
      }
      header {
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-end;
        align-items: flex-start;
        gap: 8px;
      }
      header h1 {
        font-size: 22px;
        margin: 0;
        color: #0f172a;
      }
      header p {
        margin: 0;
        color: #64748b;
      }
      .header-title,
      #last-updated {
        display: none;
      }
      .last-check-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 8px 10px;
        min-width: 220px;
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.05);
      }
      .last-check-card h3 {
        margin: 0 0 4px;
        font-size: 16px;
        color: #0f172a;
      }
      .last-check-card p {
        margin: 2px 0;
        color: #475569;
        font-size: 13px;
      }
      .last-check-card .value {
        margin-top: 6px;
        font-size: 18px;
        font-weight: 700;
        color: #0f172a;
      }
      .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-top: 24px;
      }
      .card {
        background: rgba(15, 23, 42, 0.9);
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
        border: 1px solid rgba(148, 163, 184, 0.25);
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
      .card .value { font-size: 32px; font-weight: 600; color: #f8fafc; }
      .card .muted { font-size: 13px; color: #cbd5e1; }
      .muted { color: #cbd5e1; }
      .chart-card {
        margin-top: 24px;
        background: rgba(15, 23, 42, 0.9);
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 14px 32px rgba(0,0,0,0.4);
        border: 1px solid rgba(148, 163, 184, 0.25);
      }
      .tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 12px;
      }
      .tab {
        border: none;
        background: #1e293b;
        color: #e2e8f0;
        padding: 8px 14px;
        border-radius: 999px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
      }
      .tab.active {
        background: #1d4ed8;
        color: #f8fafc;
        box-shadow: 0 8px 18px rgba(0,0,0,0.35);
      }
      .role-panel {
        margin-top: 18px;
        background: rgba(15, 23, 42, 0.9);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.35);
        border: 1px solid rgba(148, 163, 184, 0.25);
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
      .role-kpi .hint {
        font-size: 12px;
        color: #94a3b8;
      }
      .level-grid {
        margin-top: 16px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 14px;
      }
      .level-card {
        background: #1e293b;
        border-radius: 12px;
        padding: 14px;
        border: 1px solid rgba(148, 163, 184, 0.25);
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
      .notification-grid {
        margin-top: 18px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
        gap: 16px;
        align-items: start;
      }
      .notification-grid.single {
        grid-template-columns: 1fr;
      }
      .notification-card {
        background: #fff;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        padding: 16px;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
        display: flex;
        flex-direction: column;
        height: 100%;
      }
      .notification-card h3 {
        margin: 0 0 8px;
        font-size: 17px;
        color: #0f172a;
      }
      .insights-grid {
        margin-top: 24px;
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 16px;
      }
      .insight-card {
        background: #f8fafc;
        border-radius: 16px;
        padding: 18px;
        border: 1px solid #e2e8f0;
      }
      .insight-card h3 {
        margin: 0 0 12px;
        font-size: 16px;
        color: #0f172a;
      }
      .insight-card p {
        margin: 0 0 12px;
        color: #475569;
        font-size: 13px;
      }
      .section-block {
        margin-top: 20px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 12px;
      }
      .section-block .card {
        background: #fff;
        border-radius: 14px;
        padding: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
      }
      .mini-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
      }
      .mini-table th,
      .mini-table td {
        padding: 6px 8px;
        border-bottom: 1px solid #f1f5f9;
        text-align: left;
      }
      .mini-table th { color: #475569; }
      .chip-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 12px;
      }
      .chip {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 13px;
        display: inline-flex;
        gap: 6px;
        align-items: center;
      }
      .ratio-pill {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: 999px;
        color: #0f172a;
        background: rgba(59, 130, 246, 0.15);
      }
      .ratio-pill.danger {
        background: rgba(248, 113, 113, 0.2);
        color: #b91c1c;
      }
      .risk-table {
        width: 100%;
        border-collapse: collapse;
      }
      .risk-table th,
      .risk-table td {
        padding: 8px 6px;
        font-size: 13px;
      }
      .risk-table th {
        color: #94a3b8;
        border-bottom: 1px solid #e2e8f0;
      }
      .risk-table tr + tr td {
        border-top: 1px solid #f1f5f9;
      }
      .action-link {
        color: #2563eb;
        text-decoration: none;
        font-weight: 600;
      }
      .action-link:hover {
        text-decoration: underline;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 24px;
        font-size: 14px;
        table-layout: fixed;
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
      .compact-table th:nth-child(1),
      .compact-table td:nth-child(1) { width: 88px; }
      .compact-table th:nth-child(2),
      .compact-table td:nth-child(2) { width: 160px; }
      .compact-table th:nth-child(3),
      .compact-table td:nth-child(3) { width: 220px; }
      .compact-table th:nth-child(4),
      .compact-table td:nth-child(4) { width: 140px; }
      .compact-table .subject-cell,
      .compact-table .col-tech,
      .compact-table .col-channel,
      .compact-table .col-date {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .compact-table .col-tech { max-width: 210px; }
      .compact-table .col-channel { max-width: 140px; }
      .compact-table .progress-cell {
        width: 92px;
      }
      /* Ampliar columnas en modo Gerente */
      .gerente-wide .compact-table th:nth-child(2),
      .gerente-wide .compact-table td:nth-child(2) { width: 220px; max-width: 240px; }
      .gerente-wide .compact-table th:nth-child(3),
      .gerente-wide .compact-table td:nth-child(3) { width: 320px; max-width: 360px; }
      .gerente-wide .compact-table .col-tech { max-width: 260px; }
      .gerente-wide .compact-table .subject-cell { max-width: 420px; }
      .badge {
        display: inline-flex;
        align-items: center;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 12px;
        background: #e2e8f0;
        color: #475569;
      }
      .badge.reminder {
        background: rgba(59, 130, 246, 0.15);
        color: #1d4ed8;
      }
      .badge.escalation {
        background: rgba(248, 113, 113, 0.2);
        color: #b91c1c;
      }
      .empty-state {
        padding: 24px;
        text-align: center;
        color: #94a3b8;
        background: #f8fafc;
        border: 1px dashed #e2e8f0;
        border-radius: 12px;
      }
      /* Vista escritorio amplia (navegador) */
      @media (min-width: 1200px) {
        body {
          padding: 12px 0 24px;
        }
        .dashboard {
          max-width: 1280px;
          padding: 22px 22px 36px;
        }
        .gerente-wide .dashboard {
          max-width: 96vw;
          padding: 24px 28px 40px;
        }
        header {
          justify-content: space-between;
          align-items: center;
          position: sticky;
          top: 0;
          z-index: 8;
          background: linear-gradient(180deg, rgba(247, 248, 252, 0.95), rgba(241, 244, 251, 0.9));
          backdrop-filter: blur(6px);
          padding: 10px 6px;
          margin: 0 -4px 8px;
          border-radius: 12px;
        }
        .header-title,
        #last-updated {
          display: block;
        }
        .header-title h1 {
          font-size: 24px;
        }
        .header-title p,
        #last-updated {
          color: #475569;
          font-size: 13px;
        }
        .last-check-card {
          min-width: 260px;
        }
        .tabs {
          position: sticky;
          top: 76px;
          z-index: 7;
          background: linear-gradient(180deg, rgba(247, 248, 252, 0.9), rgba(241, 244, 251, 0.85));
          padding: 10px 6px 6px;
          margin: 0 -4px 8px;
          border-radius: 12px;
          backdrop-filter: blur(6px);
        }
      }
      @media (max-width: 820px) {
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
        .insights-grid {
          grid-template-columns: 1fr;
        }
      }
      /* Override a dark theme consistent with /dashboard/risk */
      body {
        background: radial-gradient(circle at 10% 20%, rgba(37, 99, 235, 0.12), transparent 25%),
                    radial-gradient(circle at 90% 10%, rgba(16, 185, 129, 0.14), transparent 22%),
                    #0b1224;
        color: #e2e8f0;
      }
      .card,
      .role-panel,
      .notification-card,
      .insight-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(148, 163, 184, 0.25);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
      }
      .level-card {
        background: #1e293b;
        border: 1px solid rgba(148, 163, 184, 0.25);
      }
      header h1, h2, h3, h4, h5, h6 { color: #f8fafc; }
      .muted, p, .role-header p, th { color: #cbd5e1; }
      .tabs .tab { background: #1e293b; color: #e2e8f0; }
      .tabs .tab.active { background: #1d4ed8; color: #f8fafc; box-shadow: 0 8px 18px rgba(0,0,0,0.35); }
      a.action-link { color: #60a5fa; }
      .badge { background: rgba(148, 163, 184, 0.2); color: #e2e8f0; }
      table tr + tr td { border-top: 1px solid rgba(148, 163, 184, 0.2); }
      .last-check-card {
        background: rgba(15,23,42,0.85);
        border: 1px solid rgba(148, 163, 184, 0.25);
        color: #e2e8f0;
      }
      /* Ajuste para contenedores embebidos (Teams) */
      @media (max-width: 1180px) {
        .summary-grid {
          grid-template-columns: 1fr;
        }
        .notification-grid {
          grid-template-columns: 1fr;
        }
        .insights-grid {
          grid-template-columns: 1fr;
        }
        .dashboard {
          padding: 16px 10px 26px;
        }
      }
    </style>
  </head>
  <body>
    <div class="dashboard">
      <header>
        <div class="header-title">
          <h1>Backlog & Alertas</h1>
          <p id="last-updated">Actualizando…</p>
        </div>
        <div class="last-check-card" id="last-check-card">
          <h3>Última verificación</h3>
          <p>Fecha y hora de la última corrida</p>
          <p class="value">-</p>
        </div>
      </header>
      <section>
        <div class="tabs" id="role-tabs"></div>
        <div id="role-panel"></div>
      </section>
    </div>
    <script>
      const DASHBOARD_CONFIG = __DASHBOARD_CONFIG__;
      const LEVEL_LABELS = __LEVEL_LABELS__;
      const state = {
        data: null,
        activeRole: DASHBOARD_CONFIG.roles[0] || null,
        chart: null,
      };

      function formatDate(value) {
        if (!value) return "-";
        const raw = String(value).replace(" ", "T");
        // Si no viene zona horaria, asumimos UTC y agregamos "Z"
        const hasZone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(raw);
        const iso = hasZone ? raw : `${raw}Z`;
        const date = new Date(iso);
        if (Number.isNaN(date.getTime())) return value;
        try {
          return date.toLocaleString("es-PE", {
            dateStyle: "medium",
            timeStyle: "short",
            timeZone: "America/Lima",
          });
        } catch (e) {
          return date.toLocaleString("es-PE", { dateStyle: "medium", timeStyle: "short" });
        }
      }

      function formatTechnician(value) {
        if (!value) return "-";
        const formatString = (text) => {
          const raw = (text || "").toString();
          if (!raw) return "";
          const base = raw.includes("@") ? raw.split("@")[0] : raw;
          const cleaned = base.replace(/[._]/g, " ").replace(/\s+/g, " ").trim();
          if (!cleaned) return raw;
          return cleaned
            .split(" ")
            .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
            .join(" ");
        };

        if (typeof value === "string" || typeof value === "number") {
          return formatString(value);
        }

        if (typeof value === "object") {
          const candidates = [
            value.name,
            value.display,
            value.technician,
            value.technician_name,
            value.technician_id,
            value.email,
            value.mail,
            value.user,
            value.username,
          ].filter(Boolean);
          if (candidates.length) {
            return formatString(candidates[0]);
          }
        }

        return value.toString();
      }

      function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
      }

      function applyRoleLayout(roleKey) {
        const body = document.body;
        if (!body) return;
        if (roleKey === "gerente") {
          body.classList.add("gerente-wide");
        } else {
          body.classList.remove("gerente-wide");
        }
      }

      async function loadData() {
        try {
          const response = await fetch("/dashboard/data");
          if (!response.ok) throw new Error("No se pudo obtener la data");
          const payload = await response.json();
          state.data = payload;
          setText("last-updated", "Actualizado: " + formatDate(state.data.refreshed_at));
          renderLastCheck(state.data.snapshot);
          try {
            renderTabs();
            renderRole(state.activeRole);
          } catch (e) {
            console.error("Error rendering role panel", e);
          }
        } catch (err) {
          console.error(err);
          if (!state.data) {
            const panel = document.getElementById("role-panel");
            if (panel) {
              panel.innerHTML =
                "<div class='role-panel'><div class='empty-state'>No pudimos cargar la información del controller.</div></div>";
            }
          }
        }
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
            applyRoleLayout(role);
          });
          container.appendChild(button);
        });
      }

      function renderLastCheck(snapshot) {
        const card = document.getElementById("last-check-card");
        if (!card) return;
        const last = snapshot && snapshot.last_run ? formatDate(snapshot.last_run) : "Sin corrida";
        const valueEl = card.querySelector(".value");
        if (valueEl) valueEl.textContent = last;
      }

      function renderRole(roleKey) {
        const container = document.getElementById("role-panel");
        applyRoleLayout(roleKey);
        const roleData = (state.data.roles || {})[roleKey];
        if (!roleData) {
          container.innerHTML =
            "<div class='role-panel'><div class='empty-state'>Sin datos disponibles para este rol.</div></div>";
          return;
        }
        if (roleKey === "supervisor") {
          const assignedSnapshot = state.data && state.data.snapshot && state.data.snapshot.assigned ? state.data.snapshot.assigned : { count: 0, items: [] };
          const atRiskNear = state.data && state.data.at_risk_near ? state.data.at_risk_near : [];
          const levels = roleData.levels
            .map((lvl, idx) => {
              const label =
                idx === 1
                  ? "Tickets próximos a escalar al siguiente Nivel"
                  : lvl.label;
              return `
                <div class="level-card">
                  <h4>${label}</h4>
                  <div class="count">${lvl.count}</div>
                </div>
              `;
            })
            .join("");
          container.innerHTML = `
            <div class="role-panel">
              <div class="role-header" style="border-color: ${roleData.color};">
                <div>
                  <h2>${roleData.label}</h2>
                  <p>${roleData.description}</p>
                </div>
                <div class="role-kpi">
                  <div class="number">${assignedSnapshot.count || 0}</div>
                  <div class="muted">Tickets sin Inicio de Atención</div>
                </div>
              </div>
              <div class="level-grid">${levels}</div>
              ${buildNotificationSection(roleKey, roleData.notifications || [], atRiskNear)}
            </div>
          `;
          return;
        }

        const panelData = state.data && state.data.role_panels ? state.data.role_panels[roleKey] : null;
        const fired = (panelData && panelData.fired) || [];
        const nearNext = (panelData && panelData.near_next) || [];
        const isGerente = roleKey === "gerente";
        container.innerHTML = `
          <div class="role-panel">
            <div class="role-header" style="border-color: ${roleData.color};">
              <div>
                <h2>${roleData.label}</h2>
                <p>${isGerente ? "Tickets con mucho tiempo Sin Atenderse" : roleData.description}</p>
              </div>
            </div>
            <div class="notification-grid${isGerente ? " single" : ""}">
              <div class="notification-card">
                <h3>${
                  isGerente
                    ? "Detalle de Tickets que superaron todos los controles previos"
                    : "Detalle de Tickets que superaron el control anterior"
                }</h3>
                ${renderFiredReminders(fired)}
              </div>
              ${
                isGerente
                  ? ""
                  : `<div class="notification-card">
                      <h3>Detalle de Ticket próximos a escalar al siguiente Nivel</h3>
                      ${renderAtRiskDetail(nearNext)}
                    </div>`
              }
            </div>
          </div>
        `;
      }

      function buildInsightsHtml(roleKey, insights) {
        if (!insights || roleKey !== "supervisor") {
          return "";
        }
        const atRiskRows =
          (insights.at_risk || [])
            .map((item) => {
              const pillClass = item.ratio >= 0.9 ? "ratio-pill danger" : "ratio-pill";
              const link = item.ticket_link
                ? `<a class="action-link" href="${item.ticket_link}" target="_blank" rel="noopener">Abrir</a>`
                : "-";
              return `
                <tr>
                  <td>#${item.ticket_id}</td>
                  <td>${formatDate(item.created_at)}</td>
                  <td>${item.requester || "-"}</td>
                  <td>${formatTechnician(item.technician || item.technician_name || item.technician_id) || "-"}</td>
                  <td>${item.priority || "-"}</td>
                  <td>${item.active_days} / ${item.threshold_days} días</td>
                  <td><span class="${pillClass}">${Math.round(item.ratio * 100)}%</span></td>
                  <td>${link}</td>
                </tr>
              `;
            })
            .join("") || "<tr><td colspan='7' class='empty-state'>Sin tickets cerca al umbral.</td></tr>";
        const chipList =
          (insights.priority_breakdown || [])
            .map((item) => `<span class="chip"><span>${item.label}</span><strong>${item.count}</strong></span>`)
            .join("") || "<p class='muted'>Sin tickets monitoreados.</p>";
        const reminders = insights.reminders_today || {};
        const lastSent = reminders.last_sent_at ? formatDate(reminders.last_sent_at) : "Sin envíos hoy.";
        return `
          <div class="insights-grid">
            <div class="insight-card">
              <h3>Próximos a escalar <span class="tag">A3</span></h3>
              <p>Tickets que se acercan al umbral de escalamiento (${insights.threshold_days} días hábiles).</p>
              <table class="risk-table">
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Creado</th>
                    <th>Solicitante</th>
                    <th>Técnico</th>
                    <th>Prioridad</th>
                    <th>Días activos</th>
                    <th>Progreso</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>${atRiskRows}</tbody>
              </table>
            </div>
            <div class="insight-card">
              <h3>Prioridades y recordatorios <span class="tag">A4</span></h3>
              <div class="chip-list">${chipList}</div>
              <p><strong>${reminders.total || 0}</strong> recordatorios hoy (${reminders.tickets || 0} tickets).</p>
              <p>Último envío: ${lastSent}</p>
            </div>
          </div>
        `;
      }

      function buildSnapshotHtml(snapshot, includeExtras = true) {
        if (!snapshot || (!snapshot.unmoved && !snapshot.at_risk_active && !snapshot.at_risk_pause)) {
          return "";
        }
        const lastRun = snapshot.last_run ? formatDate(snapshot.last_run) : "Sin corrida";
        const unmoved = snapshot.unmoved || { count: 0, items: [] };
        const atRiskActive = snapshot.at_risk_active || [];
        const atRiskPause = snapshot.at_risk_pause || [];

        const unmovedRows =
          (unmoved.items || [])
            .map(
              (item) => `
              <tr>
                <td>#${item.ticket_id || "-"}</td>
                <td>${formatTechnician(item.technician || item.technician_name || item.technician_id) || "-"}</td>
                <td>${item.subject || "-"}</td>
                <td>${formatDate(item.assigned_at || item.created_at)}</td>
                <td>${item.ticket_link ? `<a class="action-link" href="${item.ticket_link}" target="_blank" rel="noopener">Abrir</a>` : "-"}</td>
              </tr>
            `,
            )
            .join("") || "<tr><td colspan='5' class='empty-state'>Sin tickets detenidos.</td></tr>";

        const atRiskActiveRows =
          atRiskActive
            .map(
              (item) => `
              <tr>
                <td>#${item.ticket_id || "-"}</td>
                <td>${formatTechnician(item.technician || item.technician_name || item.technician_id) || "-"}</td>
                <td>${item.subject || "-"}</td>
                <td>${Math.round((item.ratio || 0) * 100)}%</td>
                <td>${item.ticket_link ? `<a class="action-link" href="${item.ticket_link}" target="_blank" rel="noopener">Abrir</a>` : "-"}</td>
              </tr>
            `,
            )
            .join("") || "<tr><td colspan='5' class='empty-state'>Sin tickets próximos (activos).</td></tr>";

        const atRiskPauseRows =
          atRiskPause
            .map(
              (item) => `
              <tr>
                <td>#${item.ticket_id || "-"}</td>
                <td>${formatTechnician(item.technician || item.technician_name || item.technician_id) || "-"}</td>
                <td>${item.subject || "-"}</td>
                <td>${Math.round((item.ratio || 0) * 100)}%</td>
                <td>${item.ticket_link ? `<a class="action-link" href="${item.ticket_link}" target="_blank" rel="noopener">Abrir</a>` : "-"}</td>
              </tr>
            `,
            )
            .join("") || "<tr><td colspan='5' class='empty-state'>Sin tickets próximos (pausa).</td></tr>";

        if (!includeExtras) {
          return `
            <div class="insight-card">
              <h3>Tickets sin moverse (asignación) <span class="tag">A7</span></h3>
              <p>${unmoved.count || 0} tickets sin cambios desde la asignación.</p>
              <table class="risk-table">
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Técnico</th>
                    <th>Asunto</th>
                    <th>Asignado</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>${unmovedRows}</tbody>
              </table>
            </div>
          `;
        }

        return `
          <div class="insights-grid">
            <div class="insight-card">
              <h3>Última verificación <span class="tag">A5</span></h3>
              <p>Fecha y hora de la última corrida</p>
              <p><strong>${lastRun}</strong></p>
            </div>
            <div class="insight-card">
              <h3>Tickets sin moverse (asignación) <span class="tag">A6</span></h3>
              <p>${unmoved.count || 0} tickets sin cambios desde la asignación.</p>
              <table class="risk-table">
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Técnico</th>
                    <th>Asunto</th>
                    <th>Asignado</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>${unmovedRows}</tbody>
              </table>
            </div>
            <div class="insight-card">
              <h3>Próximos a escalar (activos)</h3>
              <table class="risk-table">
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Técnico</th>
                    <th>Asunto</th>
                    <th>Progreso</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>${atRiskActiveRows}</tbody>
              </table>
            </div>
            <div class="insight-card">
              <h3>Próximos a escalar (pausa)</h3>
              <table class="risk-table">
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Técnico</th>
                    <th>Asunto</th>
                    <th>Progreso</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>${atRiskPauseRows}</tbody>
              </table>
            </div>
          </div>
        `;
      }

      function buildNotificationSection(roleKey, notifications, atRiskNear = []) {
        if (roleKey === "supervisor") {
          const assignedSnapshot = state.data && state.data.snapshot && state.data.snapshot.assigned ? state.data.snapshot.assigned : { items: [] };
          const supervisorNotifications = notifications || [];
          return `
            <div class="notification-grid">
              <div class="notification-card">
                <h3>Detalle de Tickets sin inicio de Atención</h3>
                ${renderFiredReminders(assignedSnapshot.items || [])}
              </div>
              <div class="notification-card">
                <h3>Detalle de Tickets próximos a escalar al siguiente Nivel</h3>
                ${renderAtRiskDetail(atRiskNear)}
              </div>
            </div>
          `;
        }
        if (!notifications.length) {
          return "<div class='empty-state'>Sin alertas recientes.</div>";
        }
        return renderNotificationTable(
          notifications.map((item) => ({
            ...item,
            category: classifyNotification(item.nivel),
            display_level: prettifyLevel(item.nivel),
          })),
        );
      }

function groupNotifications(items) {
  const grouped = { reminders: [], escalations: [] };
  items.forEach((item) => {
    const category = classifyNotification(item.nivel);
    const enriched = { ...item, category, display_level: prettifyLevel(item.nivel) };
    if (category === "reminder") {
      grouped.reminders.push(enriched);
    } else if (category === "escalation") {
      grouped.escalations.push(enriched);
    }
        });
        return grouped;
      }

function classifyNotification(level) {
  const normalized = (level || "").toLowerCase();
  if (normalized.includes("recordatorio")) return "reminder";
  if (normalized.includes("escalamiento") || normalized.includes("alerta")) return "escalation";
  return "other";
}

function prettifyLevel(level) {
  if (!level) return "-";
  const key = level.toString().toLowerCase();
  return LEVEL_LABELS[key] || level;
}

      function renderNotificationTable(items, emptyMessage = "Sin alertas recientes.") {
        if (!items.length) {
          return `<div class='empty-state'>${emptyMessage}</div>`;
        }
        const rows = items
          .map((item) => {
            const badgeClass =
              item.category === "reminder"
                ? "badge reminder"
                : item.category === "escalation"
                ? "badge escalation"
                : "badge";
            return `
              <tr>
                <td class="col-ticket">#${item.ticket_id || "-"}</td>
                <td class="col-level"><span class="${badgeClass}">${item.display_level || item.nivel || "-"}</span></td>
                <td class="col-channel">${item.canal || "-"}</td>
                <td>${formatDate(item.fecha)}</td>
              </tr>
            `;
          })
          .join("");
        return `
          <table class="compact-table">
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
        `;
      }

      function renderFiredReminders(items) {
        if (!items.length) {
          return "<div class='empty-state'>No hay tickets sin moverse en la última corrida.</div>";
        }
        const rows = items
          .map((item) => {
            const link = item.ticket_link
              ? `<a class="action-link" href="${item.ticket_link}" target="_blank" rel="noopener">Abrir</a>`
              : "-";
            return `
              <tr>
                <td class="col-ticket">#${item.ticket_id || "-"}</td>
                <td class="col-tech">${formatTechnician(item.technician || item.technician_name || item.technician_id) || "-"}</td>
                <td class="subject-cell">${item.subject || "-"}</td>
                <td class="col-date">${formatDate(item.assigned_at || item.sent_at)}</td>
                <td>${link}</td>
              </tr>
            `;
          })
          .join("");
        return `
          <table class="compact-table">
            <thead>
              <tr>
                <th>Ticket</th>
                <th>Técnico</th>
                <th>Asunto</th>
                <th>Fecha/Hora (Asig. sin avance)</th>
                <th></th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        `;
      }

      function renderAtRiskDetail(items) {
        if (!items.length) {
          return "<div class='empty-state'>Sin tickets próximos a escalar.</div>";
        }
        const rows = items
          .map((item) => {
            const ratio = Math.round((item.ratio || 0) * 100);
            const badgeClass = ratio >= 90 ? "badge escalation" : ratio >= 75 ? "badge reminder" : "badge";
            const link = item.ticket_link
              ? `<a class="action-link" href="${item.ticket_link}" target="_blank" rel="noopener">Abrir</a>`
              : "-";
            return `
              <tr>
                <td class="col-ticket">#${item.ticket_id || "-"}</td>
                <td class="col-tech">${formatTechnician(item.technician || item.technician_name || item.technician_id) || "-"}</td>
                <td class="subject-cell">${item.subject || "-"}</td>
                <td class="progress-cell"><span class="${badgeClass}">${ratio}%</span></td>
                <td>${link}</td>
              </tr>
            `;
          })
          .join("");
        return `
          <table class="compact-table">
            <thead>
              <tr>
                <th>Ticket</th>
                <th>Técnico</th>
                <th>Asunto</th>
                <th>Progreso</th>
                <th></th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        `;
      }

      function aggregateRepeatedReminders(reminders) {
        const counts = {};
        reminders.forEach((item) => {
          const key = item.ticket_id || "";
          if (!key) return;
          counts[key] = counts[key] || { ticket_id: key, count: 0, last: item.fecha, canal: item.canal };
          counts[key].count += 1;
          counts[key].last = item.fecha || counts[key].last;
          counts[key].canal = item.canal || counts[key].canal;
        });
        return Object.values(counts).filter((entry) => entry.count > 1);
      }

      function renderAggregatedReminders(items) {
        if (!items.length) {
          return "<div class='empty-state'>Sin recordatorios repetidos.</div>";
        }
        const rows = items
          .map(
            (item) => `
            <tr>
              <td>#${item.ticket_id}</td>
              <td>${item.count} envíos</td>
              <td>${item.canal || "-"}</td>
              <td>${formatDate(item.last)}</td>
            </tr>
          `,
          )
          .join("");
        return `
          <table>
            <thead>
              <tr>
                <th>Ticket</th>
                <th>Recordatorios</th>
                <th>Último canal</th>
                <th>Último envío</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        `;
      }

      document.addEventListener("DOMContentLoaded", loadData);
    </script>
  </body>
</html>
"""


SERVICE_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Disponibilidad del Controller</title>
    <style>
      :root {
        color-scheme: light;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background-color: #f5f6fb;
      }
      body {
        margin: 0;
        background: #eef2ff;
        color: #0f172a;
      }
      .dashboard {
        max-width: 1000px;
        margin: 0 auto;
        padding: 32px 24px 64px;
      }
      header {
        text-align: center;
        margin-bottom: 24px;
      }
      header h1 {
        font-size: 30px;
        margin-bottom: 6px;
      }
      header p {
        color: #475569;
      }
      .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 14px;
      }
      .card {
        background: #fff;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
      }
      .card h3 {
        margin: 0;
        font-size: 13px;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.04em;
      }
      .card .value {
        margin-top: 8px;
        font-size: 30px;
        font-weight: 600;
      }
      .card small {
        color: #94a3b8;
      }
      .chart-card {
        background: #fff;
        border-radius: 18px;
        padding: 24px;
        margin-top: 28px;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
      }
      .chart-card h3 {
        margin: 0 0 12px;
        color: #475569;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 24px;
        background: #fff;
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
      }
      th, td {
        padding: 14px;
        text-align: left;
      }
      th {
        font-size: 13px;
        color: #94a3b8;
        background: #f8fafc;
      }
      tr + tr td {
        border-top: 1px solid #f1f5f9;
      }
      .status-ok {
        color: #14b8a6;
        font-weight: 600;
      }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.6/dist/chart.umd.min.js"></script>
  </head>
  <body>
    <div class="dashboard">
      <header>
        <h1>Disponibilidad del Controller</h1>
        <p id="service-last-updated">Actualizando…</p>
      </header>
      <section class="summary-grid">
        <div class="card">
          <h3>corridas totales</h3>
          <div class="value" id="svc-runs">-</div>
          <small>Histórico del servicio</small>
        </div>
        <div class="card">
          <h3>tickets monitorizados</h3>
          <div class="value" id="svc-tickets">-</div>
          <small>Con alguna regla disparada</small>
        </div>
        <div class="card">
          <h3>alertas hoy</h3>
          <div class="value" id="svc-alerts">-</div>
          <small>Notificaciones del día</small>
        </div>
        <div class="card">
          <h3>última corrida</h3>
          <div class="value" id="svc-last-run">-</div>
          <small>UTC</small>
        </div>
      </section>
      <section class="chart-card">
        <h3>Tickets procesados por corrida</h3>
        <canvas id="svc-runs-chart" height="120"></canvas>
      </section>
      <table id="svc-runs-table">
        <thead>
          <tr>
            <th>Inicio</th>
            <th>Fin</th>
            <th>Tickets</th>
            <th>Alertas</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
    <script>
      async function loadServiceData() {
        try {
          const response = await fetch("/dashboard/data");
          if (!response.ok) throw new Error("No se pudo obtener la data");
          const data = await response.json();
          renderServiceSummary(data);
          renderServiceChart(data);
          renderRunsTable(data);
        } catch (err) {
          console.error(err);
        }
      }

      function renderServiceSummary(data) {
        const summary = data.summary || {};
        document.getElementById("service-last-updated").textContent =
          "Actualizado: " + formatDate(data.refreshed_at);
        document.getElementById("svc-runs").textContent = summary.runs ?? 0;
        document.getElementById("svc-tickets").textContent = summary.tickets_monitored ?? 0;
        document.getElementById("svc-alerts").textContent = summary.alerts_today ?? 0;
        document.getElementById("svc-last-run").textContent = formatDate(summary.last_run_finished_at);
      }

      function renderServiceChart(data) {
        const ctx = document.getElementById("svc-runs-chart");
        if (!ctx) return;
        const runs = data.runs || [];
        const labels = runs.map((item) => formatDate(item.fecha_inicio));
        const values = runs.map((item) => item.tickets || 0);
        new Chart(ctx, {
          type: "line",
          data: {
            labels,
            datasets: [
              {
                label: "Tickets procesados",
                data: values,
                fill: true,
                borderColor: "#4f46e5",
                backgroundColor: "rgba(79,70,229,0.15)",
                tension: 0.35,
                pointRadius: 4,
                pointBackgroundColor: "#4f46e5",
              },
            ],
          },
          options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
          },
        });
      }

      function renderRunsTable(data) {
        const tbody = document.querySelector("#svc-runs-table tbody");
        tbody.innerHTML = "";
        (data.runs || []).forEach((run) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${formatDate(run.fecha_inicio)}</td>
            <td>${formatDate(run.fecha_fin)}</td>
            <td>${run.tickets ?? "-"}</td>
            <td>${run.alertas ?? "-"}</td>
            <td class="${run.estado === "ok" ? "status-ok" : ""}">${run.estado || "-"}</td>
          `;
          tbody.appendChild(tr);
        });
      }

      function formatDate(value) {
        if (!value) return "-";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString("es-PE", {
          dateStyle: "medium",
          timeStyle: "short",
        });
      }

      document.addEventListener("DOMContentLoaded", loadServiceData);
    </script>
  </body>
</html>
"""

RISK_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Riesgo y Corridas</title>
    <style>
      :root {
        color-scheme: light;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #eef2ff;
      }
      body {
        margin: 0;
        background:
          radial-gradient(circle at 15% 20%, rgba(79, 70, 229, 0.12), transparent 30%),
          radial-gradient(circle at 80% 10%, rgba(16, 185, 129, 0.15), transparent 28%),
          linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
        color: #0f172a;
      }
      .shell {
        max-width: 1260px;
        margin: 0 auto;
        padding: 28px 18px 80px;
      }
      h1 { margin: 0; font-size: 28px; color: #0f172a; }
      h3 { margin: 0 0 6px; color: #0f172a; }
      .eyebrow { text-transform: uppercase; letter-spacing: 0.08em; font-size: 11px; color: #6366f1; margin: 0 0 6px; font-weight: 700; }
      .muted { color: #4b5563; margin: 0; }
      .small { font-size: 12px; }
      .hero {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 16px;
        margin-bottom: 18px;
        flex-wrap: wrap;
      }
      .hero-card {
        background: #0b1120;
        color: #f8fafc;
        padding: 10px 12px;
        border-radius: 12px;
        box-shadow: 0 14px 32px rgba(15, 23, 42, 0.28);
        min-width: 200px;
        max-width: 320px;
        width: fit-content;
      }
      .hero-number { font-size: 22px; font-weight: 700; margin: 2px 0; color: #f8fafc; }
      .hero-card p { color: #e2e8f0; }
      .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
        margin: 12px 0 18px;
      }
      .kpi-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 14px 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
      }
      .kpi-card .label { margin: 0; color: #475569; font-size: 13px; }
      .kpi-value { font-size: 26px; font-weight: 700; margin: 8px 0 4px; }
      .accent-red { border-color: #fecdd3; box-shadow: 0 10px 26px rgba(248, 113, 113, 0.18); }
      .accent-amber { border-color: #fde68a; box-shadow: 0 10px 26px rgba(251, 191, 36, 0.16); }
      .accent-green { border-color: #bbf7d0; box-shadow: 0 10px 26px rgba(34, 197, 94, 0.14); }
      .accent-indigo { border-color: #c7d2fe; box-shadow: 0 10px 26px rgba(99, 102, 241, 0.14); }
      .tabs {
        display: inline-flex;
        gap: 8px;
        padding: 8px;
        background: rgba(255, 255, 255, 0.7);
        border-radius: 999px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
        margin: 8px 0 16px;
      }
      .tab {
        border: none;
        background: transparent;
        padding: 8px 14px;
        border-radius: 999px;
        font-weight: 600;
        color: #475569;
        cursor: pointer;
      }
      .tab.active { background: #0f172a; color: #f8fafc; box-shadow: 0 10px 22px rgba(15,23,42,0.25); }
      .grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
      }
      .card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 14px 28px rgba(15, 23, 42, 0.1);
      }
      .card-head {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: flex-start;
      }
      .filters { display: flex; gap: 8px; flex-wrap: wrap; position: relative; z-index: 1000; overflow: visible; }
      .dropdown {
        position: relative;
        min-width: 180px;
        z-index: 1001;
      }
      .dropdown-toggle {
        width: 100%;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 10px 12px;
        background: #f8fafc;
        color: #0f172a;
        font-size: 14px;
        text-align: left;
        cursor: pointer;
      }
      .dropdown-toggle::after {
        content: "▾";
        float: right;
        color: #475569;
      }
      .dropdown-menu {
        position: absolute;
        top: calc(100% + 4px);
        left: 0;
        right: 0;
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.15);
        max-height: 280px;
        overflow-y: auto;
        display: none;
      }
      .dropdown.open .dropdown-menu { display: block; }
      .dropdown-item {
        padding: 10px 12px;
        cursor: pointer;
        color: #0f172a;
      }
      .dropdown-item:hover { background: #f1f5f9; }
      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 12px;
      }
      th { text-align: left; color: #475569; border-bottom: 1px solid #e5e7eb; font-size: 13px; font-weight: 600; padding: 10px 8px; }
      td { padding: 10px 8px; font-size: 13px; color: #0f172a; }
      tr + tr td { border-top: 1px solid #e5e7eb; }
      tr:hover td { background: #f8fafc; }
      .pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }
      .pill-sm { padding: 4px 8px; font-weight: 600; }
      .pill.rojo { background: #fee2e2; color: #991b1b; }
      .pill.naranja { background: #ffedd5; color: #c2410c; }
      .pill.amarillo { background: #fef9c3; color: #854d0e; }
      .pill.verde { background: #dcfce7; color: #166534; }
      .pill.azul { background: #e0e7ff; color: #312e81; }
      .badge {
        padding: 4px 8px;
        border-radius: 10px;
        background: #e5e7eb;
        color: #0f172a;
        font-size: 12px;
        font-weight: 600;
      }
      .meter {
        position: relative;
        height: 8px;
        border-radius: 999px;
        background: #e5e7eb;
        overflow: hidden;
        margin-top: 6px;
      }
      .meter-fill {
        height: 100%;
        border-radius: 999px;
        display: block;
      }
      .fill-rojo { background: linear-gradient(90deg, #ef4444, #b91c1c); }
      .fill-naranja { background: linear-gradient(90deg, #f59e0b, #d97706); }
      .fill-amarillo { background: linear-gradient(90deg, #facc15, #eab308); }
      .fill-verde { background: linear-gradient(90deg, #34d399, #059669); }
      .risk-cell { display: flex; flex-direction: column; gap: 4px; }
      .detail-block { margin-top: 10px; padding: 10px 12px; border-radius: 12px; background: #f8fafc; border: 1px dashed #e5e7eb; }
      a { color: #1d4ed8; text-decoration: none; font-weight: 600; }
      a:hover { text-decoration: underline; }
      @media (max-width: 1024px) {
        .grid { grid-template-columns: 1fr; }
        .hero { flex-direction: column; }
        .hero-card { width: 100%; max-width: 100%; }
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="hero">
        <div>
          <p class="eyebrow">Controller SDP</p>
          <h1>Alertas por Umbral</h1>
          <p class="muted">Detalle accionable de tickets, servicios y grupos antes de que escalen.</p>
        </div>
        <div class="hero-card">
          <p class="small muted">Última actualización</p>
          <div class="hero-number" id="last-updated">-</div>
          <p class="small muted">Sincronizado con controller</p>
        </div>
      </div>
      <div class="kpi-grid" id="kpi-grid">
        <div class="kpi-card accent-red">
          <p class="label">Riesgo alto</p>
          <div class="kpi-value" id="kpi-high">-</div>
          <p class="muted small">Tickets en rojo y naranja</p>
        </div>
        <div class="kpi-card accent-amber">
          <p class="label">En seguimiento</p>
          <div class="kpi-value" id="kpi-mid">-</div>
          <p class="muted small">Cerca al umbral activo</p>
        </div>
        <div class="kpi-card accent-green">
          <p class="label">Estables</p>
          <div class="kpi-value" id="kpi-low">-</div>
          <p class="muted small">Tickets verdes</p>
        </div>
      </div>
      <div class="tabs" id="view-tabs">
        <button class="tab active" data-tab="tiempo">Tiempo</button>
        <button class="tab" data-tab="personas">Personas</button>
        <button class="tab" data-tab="servicios">Servicios</button>
      </div>
      <div class="grid" id="grid-tiempo">
        <div class="card">
          <div class="card-head">
            <div>
              <p class="eyebrow">Tiempo</p>
              <h3>Tickets en mayor riesgo</h3>
              <p class="muted small">Colorea porcentajes según banda de riesgo.</p>
            </div>
            <div class="filters" id="risk-filters"></div>
          </div>
          <table id="risk-table">
            <thead>
              <tr>
                <th>Ticket</th><th>Asunto</th><th>Grupo</th><th>Activo (umbral)</th><th>Pausa (categoría/umbral)</th><th></th>
              </tr>
            </thead>
            <tbody><tr><td colspan="6" class="muted">Cargando…</td></tr></tbody>
          </table>
        </div>
      </div>
      <div class="grid" id="grid-personas" style="display:none;">
        <div class="card" style="grid-column: span 2;">
          <h3>Personas y grupos en riesgo</h3>
          <p class="muted">Haz clic en un grupo para ver técnicos y tickets en riesgo alto.</p>
          <table id="groups-table-personas">
            <thead><tr><th>Grupo</th><th>Riesgo alto</th><th>Total</th></tr></thead>
            <tbody><tr><td colspan="3" class="muted">Cargando…</td></tr></tbody>
          </table>
          <div id="group-detail-personas"></div>
        </div>
      </div>
      <div class="grid" id="grid-servicios" style="display:none;">
        <div class="card" style="grid-column: span 2;">
          <h3>Servicios con más riesgo</h3>
          <div class="filters" id="service-filters"></div>
          <table id="service-table">
            <thead>
              <tr>
                <th>Ticket</th>
                <th>Solicitante</th>
                <th>Categoría</th>
                <th>Subcategoría</th>
                <th>Item</th>
                <th>Activo (umbral)</th>
                <th>Pausa (categoría/umbral)</th>
                <th></th>
              </tr>
            </thead>
            <tbody><tr><td colspan="8" class="muted">Cargando…</td></tr></tbody>
          </table>
        </div>
      </div>
      <div class="section-block" id="tactical-section">
        <div class="card">
          <h3>Vista táctica</h3>
          <div id="tactical-content"><p class="muted small">Cargando…</p></div>
        </div>
        <div class="card">
          <h3>Vista ejecutiva</h3>
          <div id="executive-content"><p class="muted small">Cargando…</p></div>
        </div>
      </div>
    </div>
    <script>
      const fmtDate = (val) => {
        if (!val) return "-";
        const iso = val.includes("Z") || /[+-]\\d{2}:?\\d{2}$/.test(val) ? val : val + "Z";
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return val;
        return d.toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short", timeZone: "America/Lima" });
      };
      const fmtName = (val) => {
        if (!val) return "-";
        const base = (val.includes("@") ? val.split("@")[0] : val).replace(/[._]/g, " ");
        return base.split(" ").map(w => w ? w[0].toUpperCase()+w.slice(1) : "").join(" ").trim();
      };
      const baseUrl = window.location.origin;
      let opsData = null;
      const uiState = { filters: {} };
      const matchServiceFilters = (item, filters) => {
        if (filters.category && (item.category || "").toLowerCase() !== filters.category.toLowerCase()) return false;
        if (filters.subcategory && (item.subcategory || "").toLowerCase() !== filters.subcategory.toLowerCase()) return false;
        if (filters.item && (item.item || "").toLowerCase() !== filters.item.toLowerCase()) return false;
        if (filters.request_type && (item.request_type || "").toLowerCase() !== filters.request_type.toLowerCase()) return false;
        if (filters.priority && (item.priority || "").toLowerCase() !== filters.priority.toLowerCase()) return false;
        return true;
      };
      const currentThreshold = () => {
        return uiState.filters.threshold;
      };

      function summarizeRisk(items = []) {
        const bands = { rojo: 0, naranja: 0, amarillo: 0, verde: 0 };
        let ratioSum = 0;
        items.forEach((item) => {
          const band = item.risk_band || "verde";
          bands[band] = (bands[band] || 0) + 1;
          ratioSum += Math.max(0, Math.round((item.ratio || 0) * 100));
        });
        const total = items.length || 1;
        return { bands, total: items.length, average: Math.round(ratioSum / total) || 0 };
      }

      function renderSummary(risk, ops) {
        const items = risk.items || [];
        const sum = summarizeRisk(items);
        const kpi = document.getElementById("kpi-grid");
        if (kpi) {
          kpi.querySelector("#kpi-high").textContent = (sum.bands.rojo + sum.bands.naranja) || 0;
          kpi.querySelector("#kpi-mid").textContent = sum.bands.amarillo || 0;
          kpi.querySelector("#kpi-low").textContent = sum.bands.verde || 0;
        }
      }

      const buildRiskCell = (ratio, band, threshold, days) => {
        const pct = Math.min(100, Math.round((ratio || 0) * 100));
        const bandClass = band || "verde";
        const fillClass = {
          rojo: "fill-rojo",
          naranja: "fill-naranja",
          amarillo: "fill-amarillo",
          verde: "fill-verde",
        }[bandClass] || "fill-verde";
        const label = days && threshold
          ? `${Number(days).toFixed(1)}d / ${threshold}d`
          : (threshold ? `${threshold}d` : "-");
        return `
          <div class="risk-cell">
            <span class="pill pill-sm ${bandClass}">${pct}%</span>
            <div class="meter"><span class="meter-fill ${fillClass}" style="width:${pct}%"></span></div>
            <span class="muted small">${label}</span>
          </div>
        `;
      };

      const buildPauseCell = (pauseRatio, pauseBand, pauseDays, pauseThreshold, pauseCategory) => {
        const hasPause = pauseThreshold && pauseThreshold > 0;
        if (!hasPause) return `<span class="muted">Sin pausa</span>`;
        const pct = Math.min(100, Math.round((pauseRatio || 0) * 100));
        const bandClass = pauseBand || "verde";
        const fillClass = {
          rojo: "fill-rojo",
          naranja: "fill-naranja",
          amarillo: "fill-amarillo",
          verde: "fill-verde",
        }[bandClass] || "fill-verde";
        const label = pauseDays ? `${Number(pauseDays).toFixed(1)}d / ${pauseThreshold}d` : `${pauseThreshold}d`;
        return `
          <div class="risk-cell">
            <span class="pill pill-sm ${bandClass}">${pauseCategory || "Pausa"}</span>
            <span class="pill pill-sm ${bandClass}">${pct}%</span>
            <div class="meter"><span class="meter-fill ${fillClass}" style="width:${pct}%"></span></div>
            <span class="muted small">${label}</span>
          </div>
        `;
      };

      async function loadAll(filters = {}) {
        uiState.filters = { ...uiState.filters, ...filters };
        const [risk, ops, summary, tactical, executive] = await Promise.all([
          fetch(baseUrl + "/dashboard/data/risk").then(r => r.json()),
          fetch(baseUrl + "/dashboard/data/operations").then(r => r.json()).catch(() => ({groups: []})),
          fetch(baseUrl + "/dashboard/data/risk/summary").then(r => r.json()).catch(() => ({})),
          fetch(baseUrl + "/controller/tactical").then(r => r.json()).catch(() => ({})),
          fetch(baseUrl + "/controller/executive").then(r => r.json()).catch(() => ({})),
        ]);
        opsData = ops;
        document.getElementById("last-updated").textContent = fmtDate(new Date().toISOString());
        const items = risk.items || [];
        const timeFiltered = items.filter((item) => {
          const t = filters.threshold ? Number(filters.threshold) : null;
          const pt = filters.pause_threshold ? Number(filters.pause_threshold) : null;
          const pc = filters.pause_category ? String(filters.pause_category).toLowerCase() : "";
          const matchActive = t ? Number(item.threshold_days || 0) === t : true;
          const matchPause = pt ? Number(item.pause_threshold_days || 0) === pt : true;
          const matchPauseCat = pc ? (String(item.pause_category || "").toLowerCase() === pc) : true;
          return matchActive && matchPause && matchPauseCat;
        });
        const serviceFiltered = items.filter((item) => {
          const t = filters.threshold ? Number(filters.threshold) : null;
          const pt = filters.pause_threshold ? Number(filters.pause_threshold) : null;
          const pc = filters.pause_category ? String(filters.pause_category).toLowerCase() : "";
          const matchActive = t ? Number(item.threshold_days || 0) === t : true;
          const matchPause = pt ? Number(item.pause_threshold_days || 0) === pt : true;
          const matchPauseCat = pc ? (String(item.pause_category || "").toLowerCase() === pc) : true;
          return matchActive && matchPause && matchPauseCat && matchServiceFilters(item, filters);
        });
        renderSummary({ items: timeFiltered }, ops);
        renderFilters(summary, filters, items);
        renderTactical(tactical);
        renderExecutive(executive);

        const riskBody = document.querySelector("#risk-table tbody");
        const rows = timeFiltered.map(item => {
          const band = item.risk_band || "verde";
          const link = item.ticket_link ? `<a href="${item.ticket_link}" target="_blank">Abrir</a>` : "-";
          const pauseCell = buildPauseCell(item.pause_ratio, item.pause_band, item.pause_days, item.pause_threshold_days, item.pause_category);
          return `<tr>
            <td>#${item.ticket_id || "-"}</td>
            <td>${item.subject || "-"}</td>
            <td>${item.group || "-"}</td>
            <td>${buildRiskCell(item.ratio, band, item.threshold_days, item.active_days)}</td>
            <td>${pauseCell}</td>
            <td>${link}</td>
          </tr>`;
        }).join("") || `<tr><td colspan="6" class="muted">Sin tickets en riesgo.</td></tr>`;
        riskBody.innerHTML = rows;

        renderPersonas(ops);
        renderServicios({ items: serviceFiltered }, filters, summary);
      }

      function buildDropdown({ placeholder, options, selected, onSelect, id }) {
        const wrapper = document.createElement("div");
        wrapper.className = "dropdown";
        if (id) wrapper.id = id;
        const button = document.createElement("button");
        button.type = "button";
        button.className = "dropdown-toggle";
        const current = options.find((o) => String(o.value || "") === String(selected || ""));
        button.textContent = current ? current.label : placeholder;
        const menu = document.createElement("div");
        menu.className = "dropdown-menu";
        options.forEach((opt) => {
          const item = document.createElement("div");
          item.className = "dropdown-item";
          item.textContent = opt.label;
          item.addEventListener("click", () => {
            button.textContent = opt.label;
            wrapper.classList.remove("open");
            onSelect(opt.value || undefined);
          });
          menu.appendChild(item);
        });
        button.addEventListener("click", (e) => {
          e.stopPropagation();
          const isOpen = wrapper.classList.contains("open");
          document.querySelectorAll(".dropdown.open").forEach((el) => el.classList.remove("open"));
          if (!isOpen) wrapper.classList.add("open");
        });
        document.addEventListener("click", () => wrapper.classList.remove("open"));
        wrapper.appendChild(button);
        wrapper.appendChild(menu);
        return wrapper;
      }

      function renderFilters(summary, current, riskItems = []) {
        const container = document.getElementById("risk-filters");
        if (!container) return;
        container.innerHTML = "";
        container.style.display = "flex";
        container.style.gap = "8px";
        const makeOpts = (field, label) => {
          const counts = {};
          riskItems.forEach((item) => {
            const key = item[field] || 0;
            counts[key] = (counts[key] || 0) + 1;
          });
          const opts = Object.keys(counts)
            .map(Number)
            .sort((a, b) => a - b)
            .map((val) => ({ value: String(val), label: `${val} días (${counts[val]})` }));
          opts.unshift({ value: "", label });
          return opts;
        };
        const activeOpts = makeOpts("threshold_days", "Umbral activo (todos)");
        const pauseOpts = makeOpts("pause_threshold_days", "Umbral pausa (todos)");
        const pauseCatCounts = {};
        riskItems.forEach((item) => {
          const key = item.pause_category || "Sin categoría";
          pauseCatCounts[key] = (pauseCatCounts[key] || 0) + 1;
        });
        const pauseCatOpts = Object.keys(pauseCatCounts)
          .sort()
          .map((val) => ({ value: val === "Sin categoría" ? "" : val, label: `${val} (${pauseCatCounts[val]})` }));
        pauseCatOpts.unshift({ value: "", label: "Categoría pausa (todas)" });
        const dropdownActive = buildDropdown({
          placeholder: "Umbral activo (todos)",
          options: activeOpts,
          selected: current.threshold,
          onSelect: (val) => {
            loadAll({ ...uiState.filters, threshold: val || undefined }).catch(console.error);
          },
        });
        const dropdownPauseCat = buildDropdown({
          placeholder: "Categoría pausa (todas)",
          options: pauseCatOpts,
          selected: current.pause_category,
          onSelect: (val) => {
            loadAll({ ...uiState.filters, pause_category: val || undefined }).catch(console.error);
          },
        });
        container.appendChild(dropdownActive);
        container.appendChild(dropdownPauseCat);
      }

      function renderPersonas(ops) {
        const body = document.querySelector("#groups-table-personas tbody");
        if (!body) return;
        body.innerHTML = (ops.groups || []).slice(0, 12).map(g => {
          const high = (g.bands?.rojo || 0) + (g.bands?.naranja || 0);
          const total = Object.values(g.bands || {}).reduce((a,b)=>a+ (b||0),0);
          return `<tr data-group="${g.group}"><td>${g.group}</td><td>${high}</td><td>${total}</td></tr>`;
        }).join("") || `<tr><td colspan="3" class="muted">Sin datos de grupos.</td></tr>`;
        const detail = document.getElementById("group-detail-personas");
        body.querySelectorAll("tr[data-group]").forEach(row => {
            row.style.cursor = "pointer";
            row.addEventListener("click", () => {
              const g = row.getAttribute("data-group");
              const group = (ops.groups || []).find(x => (x.group || "").toLowerCase() === g.toLowerCase());
              if (!detail) return;
              if (!group) { detail.innerHTML = ""; return; }
              const tickets = group.tickets || [];
              const riskyTickets = tickets.filter(item => {
                const band = item.risk_band;
                return band === "rojo" || band === "naranja";
              });
              const techCounts = {};
              const pickTechKey = (item) =>
                (item.technician_name && item.technician_name.trim()) ||
                (item.technician && item.technician.trim()) ||
                (item.technician_id && item.technician_id.toString().trim()) ||
                "sin técnico";
              riskyTickets.forEach(item => {
                const key = pickTechKey(item);
                techCounts[key] = (techCounts[key] || 0) + 1;
              });
              const allTechs = Object.entries(techCounts).sort((a,b)=>b[1]-a[1]);
              const techHtml = allTechs.map(([tech,count])=>`<span class="badge tech-pill" data-tech="${tech}">${fmtName(tech)} · ${count}</span>`).join(" ") || "<span class='muted'>Sin técnicos en riesgo alto.</span>";
              const renderRows = (list, technicianFilter) => {
                const source = technicianFilter
                  ? list.filter(item => pickTechKey(item).toLowerCase() === technicianFilter.toLowerCase())
                  : list;
                return source.map(item => {
                  const band=item.risk_band||"verde"; const link=item.ticket_link?`<a href=\"${item.ticket_link}\" target=\"_blank\">Abrir</a>`:"-";
                  return `<tr><td>#${item.ticket_id}</td><td>${fmtName(item.technician||item.technician_name||item.technician_id||'')}</td><td>${buildRiskCell(item.ratio, band)}</td><td>${item.threshold_days||"-"}</td><td>${link}</td></tr>`;
                }).join("") || `<tr><td colspan="5" class="muted">Sin tickets en riesgo.</td></tr>`;
              };
              detail.innerHTML = `<h4>Detalle de ${g}</h4><div class="detail-block">Técnicos más expuestos: ${techHtml}</div><div class="detail-block small muted">Click en un técnico para filtrar los tickets.</div><table><thead><tr><th>Ticket</th><th>Técnico</th><th>Riesgo</th><th>Umbral</th><th></th></tr></thead><tbody>${renderRows(riskyTickets)}</tbody></table>`;
              detail.querySelectorAll(".tech-pill").forEach(pill => {
                pill.style.cursor = "pointer";
                pill.addEventListener("click", () => {
                  const tech = pill.getAttribute("data-tech") || "";
                  detail.querySelector("tbody").innerHTML = renderRows(riskyTickets, tech);
                  detail.querySelectorAll(".tech-pill").forEach(el => el.classList.remove("pill", "azul"));
                  pill.classList.add("pill", "azul");
                });
              });
            });
        });
      }

      function renderServicios(risk, filters, summary) {
        const body = document.querySelector("#service-table tbody");
        if (!body) return;
        const rows = (risk.items || []).map(item => {
          const band = item.risk_band || "verde";
          const link = item.ticket_link ? `<a href="${item.ticket_link}" target="_blank">Abrir</a>` : "-";
          const pauseCell = buildPauseCell(item.pause_ratio, item.pause_band, item.pause_days, item.pause_threshold_days, item.pause_category);
          return `<tr>
            <td class="subject-cell">#${item.ticket_id}</td>
            <td>${item.requester || "-"}</td>
            <td>${item.category || "-"}</td>
            <td>${item.subcategory || "-"}</td>
            <td>${item.item || "-"}</td>
            <td>${buildRiskCell(item.ratio, band, item.threshold_days, item.active_days)}</td>
            <td>${pauseCell}</td>
            <td>${link}</td>
          </tr>`;
        }).join("") || `<tr><td colspan="8" class="muted">Sin tickets filtrados.</td></tr>`;
        body.innerHTML = rows;
        const serviceFilters = document.getElementById("service-filters");
        if (!serviceFilters) return;
        serviceFilters.innerHTML = "";
        const makeOptions = (data, placeholder) => {
          const opts = Object.keys(data || {})
            .sort()
            .map((opt) => ({
              value: opt,
              label: `${opt} (${data[opt]})`,
            }));
          opts.unshift({ value: "", label: placeholder });
          return opts;
        };
        const baseItems = risk.items || [];
        const currentCategory = filters.category ? filters.category.toLowerCase() : "";
        const currentSubcategory = filters.subcategory ? filters.subcategory.toLowerCase() : "";
        const categoriesCounts = {};
        const filteredSubcats = {};
        const filteredItems = {};
        const typeCounts = {};
        const priorityCounts = {};
        baseItems.forEach((item) => {
          const cat = item.category || "Sin categoría";
          const sub = item.subcategory || "Sin subcategoría";
          const it = item.item || "Sin item";
          const req = item.request_type || "Sin tipo";
          const prio = item.priority || "Sin prioridad";
          categoriesCounts[cat] = (categoriesCounts[cat] || 0) + 1;
          if (!filters.category || cat.toLowerCase() === currentCategory) {
            filteredSubcats[sub] = (filteredSubcats[sub] || 0) + 1;
            if (!filters.subcategory || sub.toLowerCase() === currentSubcategory) {
              filteredItems[it] = (filteredItems[it] || 0) + 1;
            }
          }
          typeCounts[req] = (typeCounts[req] || 0) + 1;
          priorityCounts[prio] = (priorityCounts[prio] || 0) + 1;
        });
        const dropdowns = [
          { id: "sf-request_type", field: "request_type", opts: makeOptions(typeCounts, "Seleccionar tipo") },
          { id: "sf-priority", field: "priority", opts: makeOptions(priorityCounts, "Seleccionar prioridad") },
          { id: "sf-category", field: "category", opts: makeOptions(categoriesCounts, "Seleccionar categoría") },
          { id: "sf-subcategory", field: "subcategory", opts: makeOptions(filteredSubcats, "Seleccionar subcategoría") },
          { id: "sf-item", field: "item", opts: makeOptions(filteredItems, "Seleccionar item") },
        ];
        dropdowns.forEach(({ id, field, opts }) => {
          const selected = filters[field] || "";
          const dropdown = buildDropdown({
            id,
            placeholder: opts[0]?.label || `Seleccionar ${field}`,
            options: opts,
            selected,
            onSelect: (val) => {
              const newFilters = { ...uiState.filters, [field]: val || undefined };
              loadAll(newFilters).catch(console.error);
            },
          });
          serviceFilters.appendChild(dropdown);
        });
      }

      function renderTactical(data = {}) {
        const container = document.getElementById("tactical-content");
        if (!container) return;
        const trend = (data.backlog_trend || []).slice(0, 10).reverse();
        const bands = data.bands || {};
        const pauseMix = data.pause_mix || {};
        const topGroups = data.top_groups || [];
        container.innerHTML = `
          <div class="small muted">Backlog (últimas corridas)</div>
          <div class="muted small">${trend.map(t => `${fmtDate(t.timestamp)} · ${t.count}`).join("<br>") || "Sin datos"}</div>
          <div class="small muted" style="margin-top:8px;">Bandas actuales</div>
          <div class="chip-list">
            ${["rojo","naranja","amarillo","verde"].map(b=>`<span class="chip">${b}: ${bands[b]||0}</span>`).join("")}
          </div>
          <div class="small muted">Pausa por categoría</div>
          <div class="chip-list">
            ${Object.entries(pauseMix).map(([k,v])=>`<span class="chip">${k||"N/A"}: ${v}</span>`).join("") || "<span class='chip'>Sin datos</span>"}
          </div>
          <div class="small muted">Top grupos (activo promedio)</div>
          <table class="mini-table">
            <thead><tr><th>Grupo</th><th>Activo (d)</th><th>Pausa (d)</th><th>Tickets</th></tr></thead>
            <tbody>
              ${topGroups.map(g=>`<tr><td>${g.group}</td><td>${g.avg_active_days}</td><td>${g.avg_pause_days}</td><td>${g.count}</td></tr>`).join("") || "<tr><td colspan='4' class='muted'>Sin datos</td></tr>"}
            </tbody>
          </table>
        `;
      }

      function renderExecutive(data = {}) {
        const container = document.getElementById("executive-content");
        if (!container) return;
        const priority = data.priority_distribution || [];
        const requesters = data.top_requesters || [];
        const pauseMix = data.pause_mix || [];
        const sites = data.backlog_by_site || [];
        container.innerHTML = `
          <div class="small muted">Prioridad (foto actual)</div>
          <div class="chip-list">
            ${priority.map(p=>`<span class="chip">${p.label}: ${p.count}</span>`).join("") || "<span class='chip'>Sin datos</span>"}
          </div>
          <div class="small muted">Top solicitantes</div>
          <table class="mini-table">
            <thead><tr><th>Solicitante</th><th>Tickets</th><th>Activo (avg)</th><th>Pausa (avg)</th></tr></thead>
            <tbody>
              ${requesters.map(r=>`<tr><td>${fmtName(r.requester)}</td><td>${r.count}</td><td>${r.avg_active_days}</td><td>${r.avg_pause_days}</td></tr>`).join("") || "<tr><td colspan='4' class='muted'>Sin datos</td></tr>"}
            </tbody>
          </table>
          <div class="small muted">Pausa por categoría</div>
          <div class="chip-list">
            ${pauseMix.map(p=>`<span class="chip">${p.category||"N/A"}: ${p.tickets} (${p.pause_days}d)</span>`).join("") || "<span class='chip'>Sin datos</span>"}
          </div>
          <div class="small muted">Backlog por sitio</div>
          <div class="chip-list">
            ${sites.map(s=>`<span class="chip">${s.site}: ${s.count}</span>`).join("") || "<span class='chip'>Sin datos</span>"}
          </div>
        `;
      }

      const tabs = document.getElementById("view-tabs");
      if (tabs) {
        tabs.querySelectorAll(".tab").forEach(btn => {
          btn.addEventListener("click", () => {
            tabs.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const tab = btn.getAttribute("data-tab");
            document.getElementById("grid-tiempo").style.display = tab === "tiempo" ? "grid" : "none";
            document.getElementById("grid-personas").style.display = tab === "personas" ? "grid" : "none";
            document.getElementById("grid-servicios").style.display = tab === "servicios" ? "grid" : "none";
          });
        });
      }
      loadAll().catch(err => console.error(err));
    </script>
  </body>
</html>
"""
