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

## Probar desde Teams

1. Registra el bot en Azure y apunta el **Messaging endpoint** a `https://<tu-servicio>/api/messages`.
2. Escribe cualquier texto (ej. `Hola`). El bot responderá con `BOT_DEFAULT_REPLY`.
3. El bot guardará la `conversation.id` y el `user_id` para permitir envíos proactivos.

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

2. Usa cualquiera de los identificadores (`conversation_id`, `user_id` o `aad_object_id`) para enviar un mensaje:

```bash
curl -X POST https://<tu-servicio>/api/proactive \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <token>" \
  -d '{
        "conversation_id": "19:abc123@thread.v2",
        "message": "Hola, este es un recordatorio proactivo"
      }'
```

Si el usuario ya inició conversación y el `serviceUrl` sigue vigente, recibirá el mensaje como si el bot lo hubiera escrito manualmente.

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
| `src/teams_gw/settings.py` | Maneja configuración vía Pydantic `BaseSettings`. |
| `src/teams_gw/health.py` | Endpoints de diagnóstico (`/__ready`, `/health`, `/__env`, `/__auth-probe`). |
| `tests/test_formatters.py` | Pruebas para el `ConversationStore`. |

Con esta plantilla puedes ampliar fácilmente la lógica del bot (ej. hooks a otro backend, tarjetas, acciones, etc.) manteniendo una base lista para responder y enviar mensajes proactivos.
