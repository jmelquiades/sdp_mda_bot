# Teams In/Out

Pequeña plantilla para bots de Microsoft Teams escrita en FastAPI + Bot Framework.  
El flujo es mínimo: cuando alguien escribe en Teams, el bot responde con un mensaje parametrizable (ej. "`Hola, soy tu bot de Teams`").  
Además expone un endpoint HTTP para enviar mensajes proactivos vía `curl` u otra integración.

## Características

- Respuesta inmediata sin depender de backends externos.
- Registro en memoria de las conversaciones para reutilizarlas en envíos proactivos.
- API administrativa protegible por token (`/api/conversations`, `/api/proactive`).

## Requisitos previos

- Python 3.11.
- Credenciales de un Bot de Microsoft Teams (AppId/AppPassword/Tenant/Scope).
- (Opcional) un `PROACTIVE_API_KEY` para proteger los endpoints administrativos.

## Uso local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # completa valores
uvicorn src.teams_gw.app:app --reload --port 8000
```

- Health: `GET http://localhost:8000/__ready`
- Emulator: apuntar a `http://localhost:8000/api/messages`

## Tests

```bash
pytest
```

## Variables de entorno

| Categoría | Variable | Descripción |
|-----------|----------|-------------|
| Bot | `MICROSOFT_APP_ID` | AppId del bot de Teams |
| | `MICROSOFT_APP_PASSWORD` | Client secret del AppId |
| | `MICROSOFT_APP_TENANT_ID` | Tenant del bot (SingleTenant) |
| | `MICROSOFT_APP_OAUTH_SCOPE` | Scope para obtener el token (ej. `https://api.botframework.com/.default`) |
| Mensajes | `BOT_DISPLAY_NAME` | Alias opcional usado en plantillas |
| | `BOT_DEFAULT_REPLY` | Respuesta que se envía a todo mensaje entrante (`Hola, soy tu bot de Teams.` por defecto) |
| Proactivo | `PROACTIVE_DEFAULT_MESSAGE` | Texto fallback para los envíos manuales |
| | `PROACTIVE_API_KEY` | Token requerido en `X-API-Key`/`Authorization: Bearer` para usar `/api/conversations` y `/api/proactive` |
| Otros | `LOG_LEVEL` | Nivel de logging (`INFO`) |
| Dashboard | `CONTROLLER_METRICS_URL` | Endpoint del controller que expone `/controller/metrics` |
| | `DASHBOARD_ROLES` | Lista de roles visibles en el Tab (`supervisor,jefe_operacion,jefe_servicios,gerente`) |

## Probar desde Teams

1. Registra el bot en Azure y apunta el **Messaging endpoint** a `https://<tu-servicio>/api/messages`.
2. Escribe cualquier texto (ej. `Hola`). El bot responderá con `BOT_DEFAULT_REPLY`.
3. El bot guardará la `conversation.id` y el `user_id` para permitir envíos proactivos.
4. Envía `Ticket`, `Tabla`, `Reporte`, `Alerta` o `Resumen` para ver las tarjetas AdaptiveCard de demostración (`src/teams_gw/cards.py`). Así puedes enseñarle al cliente distintos layouts antes de conectarte al backend definitivo.

### Catálogo de demos

| Comando | Tarjeta enviada | Breve descripción |
|---------|-----------------|-------------------|
| `Ticket` | `demo_ticket_card()` | Encabezado simple usando los campos reales de `display_id`, `subject`, `requester`, etc. |
| `Tabla` | `demo_table_card()` | Tabla de incidencias con filas reales (tickets 147, 128, 118). |
| `Reporte` | `demo_report_card()` | Reporte semanal armado con métricas derivadas del JSON (abiertos, asignados, pausados). |
| `Alerta` | `demo_alert_card()` | Alerta crítica con estilo `attention`, datos clave y botón “Ver tablero”. |
| `Resumen` | `demo_summary_card()` | Resumen diario con columnas de métricas y notas rápidas basadas en la muestra. |

Los textos e indicadores mostrados en estas tarjetas provienen del JSON de ejemplo (`open_tickets`), así puedes mostrar algo muy cercano a la realidad. Cada función vive en `src/teams_gw/cards.py`, por lo que luego puedes parametrizarlas según el `type` que te envíe tu backend.

### Ejemplo de payload real

Puedes conectarte a cualquier backend que te devuelva JSON. Por ejemplo, el endpoint público de referencia:

```bash
curl -s https://criteria-sdp-api-gw-op.onrender.com/request/open_tickets \
  -H "X-Cliente: Criteria Technologies" \
  -H "X-Api-Key: d9b4d847-1fd1-4f1d-b5da-8c6ab9a3a568"
```

Respuesta (recortada):

```json
[
  {
    "display_id": "147",
    "subject": "Reporte de Incidentes",
    "requester": {"name": "Luis Flores"},
    "technician": {"name": "Juan Carlos Melquiades"},
    "status": {"name": "Asignado"},
    "priority": {"name": "4.Baja"},
    "site": {"name": "Criteria Technologies"},
    "dates": {
      "created": {"display": "Nov 20, 2025 06:13 PM"},
      "status_changed": {"display": "Nov 20, 2025 06:44 PM"}
    }
  },
  {
    "display_id": "118",
    "subject": "Solicitud de actualizar sistema MCP 09-11-2025",
    "requester": {"name": "MCP Mesa de Servicios"},
    "status": {"name": "En Evaluación"},
    "site": {"name": "Minera Colquisiri"},
    "dates": {"created": {"display": "Nov 12, 2025 10:20 AM"}}
  }
]
```

Puedes usar esos campos para poblar las Adaptive Cards demo (p. ej., mostrar `display_id`, `subject`, `status.name`, `requester.name`, `site.name`, etc.). Basta con mapear `type` → función dentro de `cards.py` y reemplazar los valores literales de cada tarjeta por los que vengan en el JSON.

#### Ejemplo específico para alertas

El controlador de alertas puede enviar algo como:

```json
{
  "type": "Alerta",
  "nivel": "Nivel 1",
  "titulo": "Alerta temprana de ticket sin atención",
  "cuerpo": "El ticket #147 (“Reporte de Incidentes”) lleva 1.2 días sin atención desde su asignación. Se ha escalado a supervisor_mesa.",
  "url": "https://atenciónalcliente.criteria.pe"
}
```

Ese payload se corresponde con la tarjeta `demo_alert_card()` (botón “Ir al tablero”). Cuando conectes tu backend, bastará con mapear `type == "Alerta"` a la función que renderiza la card con esos campos.

Los niveles se transforman automáticamente en colores y destinatarios:

| Nivel | Destinatario | Estilo |
|-------|--------------|--------|
| `Nivel 1` | Supervisor de Mesa | `attention` (rojo) |
| `Nivel 2` | Jefe de Operaciones | `warning` (ámbar) |
| `Nivel 3` | Jefe de Servicios | `accent` (azul) |
| `Nivel 4` | Gerente de TI | `emphasis` (gris) |

Si en el futuro agregas otro nivel, sólo debes extender el mapa en `ALERT_LEVEL_CONFIG` dentro de `cards.py`.

## Envío proactivo vía curl

1. Lista las conversaciones conocidas (requiere `PROACTIVE_API_KEY` si está configurado):

```bash
curl -H "X-API-Key: <token>" https://<tu-servicio>/api/conversations
```

Respuesta tipo:

```json
{
  "items": [
    {
      "conversation_id": "19:abc123@thread.v2",
      "user_id": "29:1a2b",
      "aad_object_id": "0000-1111-2222",
      "tenant_id": "xxxx-tenant",
      "service_url": "https://smba.trafficmanager.net/amer/",
      "user_name": "Juan"
    }
  ]
}
```

2. Usa cualquiera de los identificadores (`conversation_id`, `user_id` o `aad_object_id`) para enviar un mensaje. Desde la versión actual puedes omitir `message` si sólo quieres mostrar una tarjeta (por ejemplo, `payload.type == "Alerta"`):

```bash
curl -X POST https://<tu-servicio>/api/proactive \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <token>" \
  -d '{
        "conversation_id": "19:abc123@thread.v2",
        "payload": {
          "type": "Alerta",
          "nivel": "Nivel 1",
          "titulo": "Alerta temprana",
          "cuerpo": "El ticket #147 lleva 1.2 días sin atención.",
          "url": "https://mi-tablero",
          "ticket_id": "147",
          "subject": "Reporte de incidentes",
          "umbral": "1.2 días"
        }
      }'
```

Si el usuario ya inició conversación y el `serviceUrl` sigue vigente, recibirá la Adaptive Card (y, si incluyes `message`, también el texto antes o después de la tarjeta).

### Ejemplo real (Render + Teams)

````bash
curl -H "X-API-Key: <tu token>" https://sdp-mda-bot.onrender.com/api/conversations
# =>
# {"items":[{"conversation_id":"a:1r4hcvyU4Inm9Jp8LuzwuC7H_6TOjS7WV7bhPH4qYOEBJG6uOP-7cSY0jY6tyneHY_iRtZZSERGEw-45gI_qsmQERII9ZboG1Q5ufUw00YnkF4KCCgFu_QoErsiLyx0Y3","user_id":"29:1BZc2KzAzKqK3rGtICfbDTB0rvbRGyGK4iiEt_2zZeGCSOY6viACXkJsjMvmxcrhg6a439a2V4-RFWYccfV3DDg","aad_object_id":"e299239f-95ce-41dd-911c-0f6f17f2be1b","tenant_id":"46d67256-4eb1-491e-93ed-c27f8262d672","service_url":"https://smba.trafficmanager.net/amer/46d67256-4eb1-491e-93ed-c27f8262d672/","user_name":"Juan Carlos   Melquiades"}]}

curl -X POST https://sdp-mda-bot.onrender.com/api/proactive \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <tu token>" \
  -d '{
        "conversation_id": "a:1r4hcvyU4Inm9Jp8LuzwuC7H_6TOjS7WV7bhPH4qYOEBJG6uOP-7cSY0jY6tyneHY_iRtZZSERGEw-45gI_qsmQERII9ZboG1Q5ufUw00YnkF4KCCgFu_QoErsiLyx0Y3",
        "message": "¿Estás ahí?"
      }'
# => {"ok": true}
````

## Arquitectura y flujo

1. **Teams → FastAPI**: `/api/messages` recibe cada actividad y la entrega al `BotFrameworkAdapter`.
2. **Adapter → Bot**: `TeamsGatewayBot` genera una respuesta basada en `BOT_DEFAULT_REPLY` y registra la conversación en `conversation_store`.
3. **API proactiva**: `GET /api/conversations` devuelve las referencias almacenadas. `POST /api/proactive` usa `adapter.continue_conversation` para enviar mensajes sin intervención del usuario.

## Archivos principales

| Archivo | Descripción |
|---------|-------------|
| `src/teams_gw/app.py` | Inicializa FastAPI, aplica el parche MSAL, confía en `serviceUrl`, expone `/api/messages`, `/api/conversations`, `/api/proactive` y rutas de salud. |
| `src/teams_gw/bot.py` | Bot mínimo que guarda conversaciones y responde usando plantillas configurables. |
| `src/teams_gw/conversation_store.py` | Registro en memoria de las conversaciones; permite buscarlas por `conversation_id`, `user_id` o `aad_object_id`. |
| `src/teams_gw/cards.py` | Plantillas de Adaptive Cards (Ticket, Tabla, Reporte, Alerta, Resumen) que se envían como demos al recibir esos comandos. |
| `src/teams_gw/settings.py` | Maneja configuración vía Pydantic `BaseSettings`. |
| `src/teams_gw/health.py` | Endpoints de diagnóstico (`/__ready`, `/health`, `/__env`, `/__auth-probe`). |
| `tests/test_formatters.py` | Pruebas para el `ConversationStore`. |

Con esta plantilla puedes ampliar fácilmente la lógica del bot (ej. hooks a otro backend, tarjetas, acciones, etc.) manteniendo una base lista para responder y enviar mensajes proactivos.

## Dashboards web

El bot expone dos vistas basadas en los datos del controller (`CONTROLLER_METRICS_URL`):

1. `/dashboard/service`: KPIs de disponibilidad del controller (corridas totales, tickets procesados, alertas del día, tabla de corridas e histórico).
2. `/dashboard`: tablero de backlog por rol (Supervisor, Jefe de Operaciones, Jefe de Servicios y Gerente), con sus alertas recientes y niveles.

Ambas se actualizan consumiendo `/dashboard/data`. Para usarlas como Tab en Teams:

1. Configura `CONTROLLER_METRICS_URL` y `DASHBOARD_ROLES` en Render.
2. Asegúrate de que el controller esté accesible (ej. `https://criteriat-sdp-mda-controller.onrender.com/controller/metrics`).
3. Despliega el bot y apunta el Tab de Teams a `https://<bot>/dashboard/service` (disponibilidad) o `https://<bot>/dashboard` (roles).

`/dashboard/data` entrega el JSON ya normalizado, por lo que también puedes reutilizarlo en otras UIs si es necesario.
