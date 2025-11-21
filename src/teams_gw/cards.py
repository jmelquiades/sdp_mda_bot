from __future__ import annotations

from typing import Any, Dict


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


def demo_alert_card() -> Dict[str, Any]:
    """Alerta visual para incidentes críticos."""

    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "Container",
                "style": "attention",
                "bleed": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "Alerta crítica",
                        "weight": "Bolder",
                        "size": "Medium",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Servicio ERP con latencia elevada desde 10:32.",
                        "wrap": True,
                        "spacing": "Small",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Impacto: Usuarios de facturación.",
                        "wrap": True,
                        "spacing": "Small",
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {"title": "Severidad", "value": "High"},
                            {"title": "Owner", "value": "NOC"},
                            {"title": "Ticket", "value": "#INC-4021"},
                        ],
                    },
                ],
            },
            {
                "type": "ActionSet",
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "Ver tablero",
                        "url": "https://contoso.com/alertas/inc-4021",
                    }
                ],
            },
        ],
    }


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
