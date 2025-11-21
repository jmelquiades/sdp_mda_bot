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
