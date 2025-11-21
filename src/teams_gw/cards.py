from __future__ import annotations

from typing import Any, Dict


ALERT_LEVEL_CONFIG = {
    "Nivel 1": {
        "style": "emphasis",
        "audience": "Supervisor de Mesa",
        "icon": "https://adaptivecards.io/content/People/person2.png",
    },
    "Nivel 2": {
        "style": "warning",
        "audience": "Jefe de Operaciones",
        "icon": "https://adaptivecards.io/content/People/person3.png",
    },
    "Nivel 3": {
        "style": "accent",
        "audience": "Jefe de Servicios",
        "icon": "https://adaptivecards.io/content/People/person1.png",
    },
    "Nivel 4": {
        "style": "attention",
        "audience": "Gerente de TI",
        "icon": "https://adaptivecards.io/content/People/person4.png",
    },
}


def _resolve_alert_level(level: str) -> Dict[str, str]:
    default = {
        "style": "attention",
        "audience": "Equipo responsable",
        "icon": "https://adaptivecards.io/content/People/person7.png",
    }
    return ALERT_LEVEL_CONFIG.get(level, default)


def demo_ticket_card() -> Dict[str, Any]:
    """Tarjeta de ejemplo para tickets."""

    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "Container",
                "style": "emphasis",
                "bleed": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "Reporte de Incidentes",
                        "weight": "Bolder",
                        "size": "Medium",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Ticket #147 · Service Desk Plus",
                        "wrap": True,
                        "spacing": "Small",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Solicitante: Luis Flores",
                        "wrap": True,
                        "spacing": "Small",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Asignado a: Juan Carlos Melquiades",
                        "wrap": True,
                        "spacing": "Small",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Estado: Asignado · Prioridad: 4.Baja",
                        "wrap": True,
                        "spacing": "Small",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Creado: Nov 20, 2025 06:13 PM · Sitio: Criteria Technologies",
                        "wrap": True,
                        "spacing": "Small",
                    },
                ],
            }
        ],
    }


def demo_table_card() -> Dict[str, Any]:
    """Tarjeta de ejemplo con tabla."""

    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": "Tickets abiertos",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                "type": "TextBlock",
                "text": "Ejemplo alimentado con `open_tickets` (Criteria Service Desk).",
                "isSubtle": True,
                "wrap": True,
                "spacing": "Small",
            },
            {
                "type": "Table",
                "firstRowAsHeader": True,
                "columns": [
                    {"width": 1.2},
                    {"width": 1.4},
                    {"width": 1},
                    {"width": 1},
                ],
                "rows": [
                    {
                        "type": "TableRow",
                        "cells": [
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Ticket"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Asunto"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Solicitante"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Estado"}]},
                        ],
                    },
                    {
                        "type": "TableRow",
                        "cells": [
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "147"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Reporte de Incidentes", "wrap": True}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Luis Flores"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Asignado"}]},
                        ],
                    },
                    {
                        "type": "TableRow",
                        "cells": [
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "128"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Solicitud de actualizar sistema MCP 09-11-2025", "wrap": True}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "MCP Mesa de Servicios"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Asignado"}]},
                        ],
                    },
                    {
                        "type": "TableRow",
                        "cells": [
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "118"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Solicitud de actualizar sistema MCP 09-11-2025", "wrap": True}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "MCP Mesa de Servicios"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "En Evaluación"}]},
                        ],
                    },
                ],
            },
        ],
    }


def demo_report_card() -> Dict[str, Any]:
    """Tarjeta tipo reporte semanal."""

    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "Image",
                                "url": "https://adaptivecards.io/content/airplane.png",
                                "size": "Small",
                                "style": "person",
                            }
                        ],
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": "Reporte semanal",
                                "weight": "Bolder",
                                "size": "Medium",
                            },
                            {
                                "type": "TextBlock",
                                "text": "Del 01 al 07 de noviembre",
                                "isSubtle": True,
                                "spacing": "None",
                            },
                        ],
                    },
                ],
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Tickets abiertos", "value": "6"},
                    {"title": "Asignados", "value": "3"},
                    {"title": "Pausados", "value": "2"},
                ],
            },
            {
                "type": "TextBlock",
                "text": "Comentarios destacados:",
                "weight": "Bolder",
                "spacing": "Medium",
            },
            {
                "type": "TextBlock",
                "text": "- Mantenimientos pendientes para MCP.\n- BI Analytics con casos pausados por fabricante.",
                "wrap": True,
            },
        ],
    }


def build_alert_card(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Construye la tarjeta de alerta a partir del JSON recibido."""

    level = payload.get("nivel") or "Nivel 1"
    config = _resolve_alert_level(level)
    title = payload.get("titulo") or "Alerta temprana"
    body = payload.get("cuerpo") or ""
    url = payload.get("url") or "https://example.org"
    ticket_id = payload.get("ticket_id")
    subject = payload.get("subject")
    umbral = payload.get("umbral")
    requester = payload.get("requester")
    technician = payload.get("technician")
    created_at = payload.get("created_at")

    def _row(label: str, value: str | None) -> dict[str, Any] | None:
        if not value:
            return None
        return {
            "type": "TableRow",
            "cells": [
                {
                    "type": "TableCell",
                    "items": [{"type": "TextBlock", "text": label, "weight": "Bolder"}],
                    "style": "accent",
                },
                {
                    "type": "TableCell",
                    "items": [{"type": "TextBlock", "text": value, "wrap": True}],
                },
            ],
        }

    detail_rows = list(filter(None, [
        _row("Ticket", ticket_id),
        _row("Asunto", subject),
        _row("Solicitante", requester),
        _row("Asignado a", technician),
        _row("Creado", created_at),
        _row("Umbral", umbral),
        _row("Nivel", level),
    ]))

    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "ColumnSet",
                "style": config["style"],
                "bleed": True,
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "Image",
                                "url": config["icon"],
                                "size": "Small",
                                "style": "person",
                            }
                        ],
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": title,
                                "weight": "Bolder",
                                "size": "Medium",
                            },
                            {
                                "type": "TextBlock",
                                "text": f"Dirigido a: {config['audience']}",
                                "isSubtle": True,
                                "spacing": "None",
                            },
                        ],
                    },
                ],
            },
            {"type": "TextBlock", "text": body, "wrap": True, "spacing": "Small"},
            {
                "type": "Table",
                "columns": [
                    {"width": 0.8},
                    {"width": 1.2},
                ],
                "rows": detail_rows or [
                    _row("Ticket", ticket_id or "N/A"),
                    _row("Umbral", umbral or "-"),
                ],
            },
            {
                "type": "ActionSet",
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "Ver tablero",
                        "url": url,
                    }
                ],
            },
        ],
    }


def demo_alert_card() -> Dict[str, Any]:
    """Alerta visual para incidentes críticos."""

    payload = {
        "nivel": "Nivel 1",
        "titulo": "Alerta temprana de ticket sin atención",
        "cuerpo": "El ticket #147 (“Reporte de Incidentes”) lleva 1.2 días sin atención desde su asignación. Se ha escalado a supervisor_mesa.",
        "url": "https://atenciónalcliente.criteria.pe",
    }
    return build_alert_card(payload)


def demo_summary_card() -> Dict[str, Any]:
    """Resumen diario estilo boletín."""

    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": "Resumen diario",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                "type": "TextBlock",
                "text": "Martes, 12 de noviembre",
                "isSubtle": True,
                "spacing": "None",
            },
            {
                "type": "ColumnSet",
                "spacing": "Medium",
                "columns": [
                    {
                        "type": "Column",
                        "width": 1,
                        "items": [
                            {"type": "TextBlock", "text": "Tickets abiertos", "isSubtle": True},
                            {"type": "TextBlock", "text": "6", "weight": "Bolder", "size": "Large"},
                        ],
                    },
                    {
                        "type": "Column",
                        "width": 1,
                        "items": [
                            {"type": "TextBlock", "text": "Tickets cerrados", "isSubtle": True},
                            {"type": "TextBlock", "text": "4", "weight": "Bolder", "size": "Large"},
                        ],
                    },
                    {
                        "type": "Column",
                        "width": 1,
                        "items": [
                            {"type": "TextBlock", "text": "Pendientes críticos", "isSubtle": True},
                            {"type": "TextBlock", "text": "2", "weight": "Bolder", "size": "Large"},
                        ],
                    },
                ],
            },
            {
                "type": "TextBlock",
                "text": "Notas rápidas:",
                "weight": "Bolder",
                "spacing": "Medium",
            },
            {
                "type": "TextBlock",
                "text": "• Mayoría de tickets en Service Desk Plus.\n• Caso MCP sigue en evaluación.\n• Dos solicitudes permanecen en pausa por fabricante.",
                "wrap": True,
            },
        ],
    }
