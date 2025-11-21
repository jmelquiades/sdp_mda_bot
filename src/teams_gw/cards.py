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
                        "text": "Supervisor de Mesa",
                        "weight": "Bolder",
                        "size": "Medium",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Ticket #118 — Solicitud de actualizar sistema MCP 09-11-2025",
                        "wrap": True,
                        "spacing": "Small",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Solicitante: MCP Mesa de Servicios",
                        "wrap": True,
                        "spacing": "Small",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Creado: 2025-11-12 15:20",
                        "wrap": True,
                        "spacing": "Small",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Umbral: 7.0 días",
                        "weight": "Bolder",
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
                "text": "Reporte de incidencias",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                "type": "TextBlock",
                "text": "Ejemplo de tabla renderizada en Adaptive Cards.",
                "isSubtle": True,
                "wrap": True,
                "spacing": "Small",
            },
            {
                "type": "Table",
                "firstRowAsHeader": True,
                "columns": [
                    {"width": 1},
                    {"width": 1},
                    {"width": 1},
                ],
                "rows": [
                    {
                        "type": "TableRow",
                        "cells": [
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Ticket"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Área"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Estado"}]},
                        ],
                    },
                    {
                        "type": "TableRow",
                        "cells": [
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "118"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Soporte"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Pendiente"}]},
                        ],
                    },
                    {
                        "type": "TableRow",
                        "cells": [
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "119"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Infraestructura"}]},
                            {"type": "TableCell", "items": [{"type": "TextBlock", "text": "Completado"}]},
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
                    {"title": "Tickets atendidos", "value": "42"},
                    {"title": "Promedio SLA", "value": "97%"},
                    {"title": "Escalados", "value": "4"},
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
                "text": "- Incidente de VPN resuelto.\n- Nuevo flujo de alertas habilitado.",
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
                        "color": "Light",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Servicio ERP con latencia elevada desde 10:32.",
                        "wrap": True,
                        "spacing": "Small",
                        "color": "Light",
                    },
                    {
                        "type": "TextBlock",
                        "text": "Impacto: Usuarios de facturación.",
                        "wrap": True,
                        "spacing": "Small",
                        "color": "Light",
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
                            {"type": "TextBlock", "text": "15", "weight": "Bolder", "size": "Large"},
                        ],
                    },
                    {
                        "type": "Column",
                        "width": 1,
                        "items": [
                            {"type": "TextBlock", "text": "Tickets cerrados", "isSubtle": True},
                            {"type": "TextBlock", "text": "22", "weight": "Bolder", "size": "Large"},
                        ],
                    },
                    {
                        "type": "Column",
                        "width": 1,
                        "items": [
                            {"type": "TextBlock", "text": "Pendientes críticos", "isSubtle": True},
                            {"type": "TextBlock", "text": "3", "weight": "Bolder", "size": "Large"},
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
                "text": "• Equipo de redes trabajando en migración.\n• Se planifica ventana de mantenimiento el viernes.",
                "wrap": True,
            },
        ],
    }
