# SDP MDA Bot (Teams Gateway)

Bot y frontend FastAPI para mostrar dashboards de backlog/umbrales en Microsoft Teams y recibir notificaciones proactivas desde el controller.

## Qué incluye
- Tabs web embebibles en Teams:
  - `/dashboard` (roles: Supervisor, Jefe Operación, Jefe Servicios, Gerente).
  - `/dashboard/risk` (tiempo, personas, servicios con filtros y colores por banda).
  - `/dashboard/service` (disponibilidad del controller).
- Endpoints proactivos (Bot Framework) para enviar Adaptive Cards desde el controller.
- Demos de tarjetas en `src/teams_gw/cards.py` (Ticket, Tabla, Reporte, Alerta, Resumen).

## Ejecutar local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # completa valores
uvicorn src.teams_gw.app:app --reload --port 8000
```
- Health: `GET /__ready`
- Bot emulator: `POST /api/messages`
- Dashboards: `GET /dashboard`, `/dashboard/risk`, `/dashboard/service`

## Variables de entorno principales
| Variable | Descripción |
|----------|-------------|
| `MICROSOFT_APP_ID` / `MICROSOFT_APP_PASSWORD` / `MICROSOFT_APP_TENANT_ID` / `MICROSOFT_APP_OAUTH_SCOPE` | Credenciales del bot de Teams |
| `BOT_DISPLAY_NAME` | Alias opcional en plantillas |
| `BOT_DEFAULT_REPLY` | Respuesta por defecto a mensajes entrantes |
| `PROACTIVE_API_KEY` | Token para `/api/conversations` y `/api/proactive` |
| `CONTROLLER_METRICS_URL` | URL del controller (`/controller/metrics`) |
| `DASHBOARD_ROLES` | Roles visibles en tabs (`supervisor,jefe_operacion,jefe_servicios,gerente`) |
| `LOG_LEVEL` | Nivel de logging |

## Cómo usar en Teams
1) Registra el bot en Azure y apunta el **Messaging endpoint** a `https://<tu-servicio>/api/messages`.  
2) Añade un Tab en Teams apuntando a `/dashboard` o `/dashboard/risk`.  
3) Habilita notificaciones proactivas: desde el controller llama a `/api/proactive` con `conversation_id` y el payload de la tarjeta.  

Ejemplo rápido de envío proactivo (requiere `PROACTIVE_API_KEY`):
```bash
curl -X POST https://<tu-servicio>/api/proactive \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <token>" \
  -d '{
        "conversation_id": "<id>",
        "payload": {
          "type": "Alerta",
          "nivel": "Nivel 1",
          "titulo": "Alerta temprana",
          "cuerpo": "El ticket #147 lleva 1.2 días sin atención.",
          "url": "https://mi-tablero"
        }
      }'
```

## Tests
```bash
pytest
```

## Notas de UI
- Dropdowns personalizados con alto z-index para Teams.
- Colores por banda de riesgo (rojo/naranja/amarillo/verde) y KPIs de umbral.
