from __future__ import annotations

import inspect
import logging
import os
import time
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    MessageFactory,
    TurnContext,
)
from botbuilder.schema import Activity, Attachment
from botframework.connector import models as connector_models  # <-- para capturar el error
from botframework.connector.auth import MicrosoftAppCredentials
from botframework.connector.auth import microsoft_app_credentials as mac
from msal import ConfidentialClientApplication

from .bot import TeamsGatewayBot
from .cards import build_alert_card
from .conversation_store import conversation_store
from .dashboard import (
    build_dashboard_payload,
    fetch_controller_generic,
    fetch_controller_metrics,
    normalize_roles,
    render_dashboard_html,
    render_risk_dashboard_html,
    render_service_dashboard_html,
    render_tactical_dashboard_html,
    render_executive_dashboard_html,
)
from .health import router as health_router
from .settings import settings

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("teams_gw.app")


class ProactiveMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: Optional[str] = Field(default=None, description="Texto opcional que se enviará al usuario.")
    conversation_id: Optional[str] = Field(default=None, description="conversation.id almacenado previamente.")
    user_id: Optional[str] = Field(default=None, description="ChannelAccount.id del usuario.")
    aad_object_id: Optional[str] = Field(default=None, description="Azure AD object id del usuario.")
    payload: Optional[dict[str, Any]] = Field(default=None, description="Payload opcional para renderizar tarjetas.")

    @model_validator(mode="after")
    def validate_target(self) -> "ProactiveMessageRequest":
        if not any([self.conversation_id, self.user_id, self.aad_object_id]):
            raise ValueError("Debes indicar conversation_id, user_id o aad_object_id.")
        if not (self.message or self.payload):
            raise ValueError("Debes enviar al menos message o payload.")
        return self


async def verify_api_key(
    x_api_key: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
) -> None:
    expected = settings.PROACTIVE_API_KEY
    if not expected:
        return
    provided = x_api_key
    if not provided and authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer":
            provided = token.strip()
    if provided != expected:
        raise HTTPException(status_code=401, detail="invalid_api_key")


app = FastAPI(title="teams_gw")
app.include_router(health_router)

for env_key, env_value in {
    "MicrosoftAppType": "SingleTenant",
    "MicrosoftAppTenantId": settings.MICROSOFT_APP_TENANT_ID,
    "MicrosoftAppOAuthScope": settings.MICROSOFT_APP_OAUTH_SCOPE,
}.items():
    if env_value:
        os.environ[env_key] = env_value

log.info(
    "Adapter auth env → type=%s tenant=%s scope=%s app_id=%s",
    os.getenv("MicrosoftAppType"),
    os.getenv("MicrosoftAppTenantId"),
    os.getenv("MicrosoftAppOAuthScope"),
    settings.MICROSOFT_APP_ID,
)


def _msal_authority(creds: MicrosoftAppCredentials) -> str:
    authority = getattr(creds, "authority", None)
    if authority:
        return authority
    tenant = getattr(creds, "oauth_tenant", None) or os.getenv("MicrosoftAppTenantId") or "botframework.com"
    return f"https://login.microsoftonline.com/{tenant}"


def _patched_get_access_token(self: MicrosoftAppCredentials) -> str:
    cached = getattr(self, "_patched_token", None)
    expires_at = getattr(self, "_patched_token_expires_at", 0)
    if cached and expires_at - time.time() > 300:
        return cached

    scope = getattr(self, "oauth_scope", None) or os.getenv("MicrosoftAppOAuthScope") or "https://api.botframework.com/.default"
    scope = scope.strip()
    if not scope.endswith("/.default"):
        scope = f"{scope.rstrip('/')}/.default"
    app = getattr(self, "_patched_msal_app", None)
    if not app:
        app = ConfidentialClientApplication(
            client_id=getattr(self, "microsoft_app_id", None) or settings.MICROSOFT_APP_ID,
            client_credential=getattr(self, "microsoft_app_password", None) or settings.MICROSOFT_APP_PASSWORD,
            authority=_msal_authority(self),
        )
        self._patched_msal_app = app

    result = app.acquire_token_for_client(scopes=[scope])
    token = result.get("access_token")
    if not token:
        raise RuntimeError(f"Could not acquire access token via MSAL: {result}")
    ttl = int(result.get("expires_in", 3600))
    self._patched_token = token
    self._patched_token_expires_at = time.time() + ttl
    return token


mac.MicrosoftAppCredentials.get_access_token = _patched_get_access_token


adapter_settings = BotFrameworkAdapterSettings(
    settings.MICROSOFT_APP_ID,
    settings.MICROSOFT_APP_PASSWORD,
)
adapter = BotFrameworkAdapter(adapter_settings)
ADAPTER_KIND = "BotFrameworkAdapter"


conversation_state = ConversationState(MemoryStorage())
bot = TeamsGatewayBot(conversation_state)
ACTIVE_DASHBOARD_ROLES = normalize_roles(settings.DASHBOARD_ROLES)

@app.post("/api/messages")
async def messages(request: Request):
    body = await request.json()
    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")

    rid = (activity.recipient and activity.recipient.id) or ""
    rid_norm = rid.split(":", 1)[-1] if rid else ""
    log.info(
        "Incoming activity: {'type': %s, 'channel_id': %s, 'service_url': %s, "
        "'conversation_id': %s, 'from_id': %s, 'recipient_id': %s, "
        "'recipient_id_normalized': %s, 'env_app_id': %s}",
        activity.type,
        activity.channel_id,
        activity.service_url,
        (activity.conversation and activity.conversation.id),
        (activity.from_property and activity.from_property.id),
        rid,
        rid_norm,
        settings.MICROSOFT_APP_ID,
    )

    # Confiamos explíticamente serviceUrl y host base (bien para Teams)
    svc = getattr(activity, "service_url", None)
    if svc:
        try:
            p = urlparse(svc)
            # host raíz
            host_root = f"{p.scheme}://{p.netloc}/"
            # base regional (primer segmento del path, p.ej. "amer/")
            path_parts = [seg for seg in p.path.split("/") if seg]
            region_base = f"{p.scheme}://{p.netloc}/{path_parts[0]}/" if path_parts else host_root

            # Confiar: URL completa, host raíz y base regional (ambos con/sin "/")
            variants = {svc, host_root, region_base}
            variants |= {u.rstrip("/") for u in variants if u.endswith("/")}

            for u in variants:
                if u:
                    MicrosoftAppCredentials.trust_service_url(u)

            log.info("Trusted service URLs: %s", sorted(variants))
        except Exception as e:
            log.warning("Could not trust serviceUrl variants: %s (%s)", svc, e)
   

    async def aux_logic(turn_context: TurnContext):
        await bot.on_turn(turn_context)

    try:
        await adapter.process_activity(activity, auth_header, aux_logic)
        return {"ok": True}
    except connector_models.ErrorResponseException as e:
        status, reason, body_text = await _extract_error_details(e)
        inner_details = _format_inner_error(e)
        log.error(
            "Connector reply failed: status=%s reason=%s url=%s convo=%s activityId=%s body=%s raw=%r inner=%r inner_details=%s",
            status, reason, activity.service_url,
            (activity.conversation and activity.conversation.id),
            getattr(activity, "id", None),
            body_text, e, getattr(e, "inner_exception", None), inner_details,
        )
        return JSONResponse(status_code=502, content={"ok": False, "error": "connector_unauthorized"})
    except Exception as e:
        if isinstance(e, KeyError) and e.args == ("access_token",):
            await _log_auth_context()
        log.exception("Unexpected error replying to Teams: %s", e)
        return JSONResponse(status_code=500, content={"ok": False, "error": "unexpected"})


@app.get("/api/conversations")
async def list_conversations(_: None = Depends(verify_api_key)):
    items = await conversation_store.summaries()
    return {"items": items}


@app.post("/api/proactive")
async def send_proactive(payload: ProactiveMessageRequest, _: None = Depends(verify_api_key)):
    reference = await conversation_store.resolve(
        conversation_id=payload.conversation_id,
        user_id=payload.user_id,
        aad_object_id=payload.aad_object_id,
    )
    if not reference:
        raise HTTPException(status_code=404, detail="conversation_reference_not_found")

    async def _send_proactive(turn_context: TurnContext):
        if payload.message:
            await turn_context.send_activity(payload.message)
        attachment = _maybe_build_attachment(payload.payload)
        if attachment:
            await turn_context.send_activity(attachment)

    await adapter.continue_conversation(reference, _send_proactive, settings.MICROSOFT_APP_ID)
    return {"ok": True}


def _maybe_build_attachment(custom_payload: Optional[dict[str, Any]]):
    if not custom_payload or not isinstance(custom_payload, dict):
        return None
    payload_type = (custom_payload.get("type") or "").lower()
    card_content: Optional[dict[str, Any]] = None

    if payload_type == "alerta":
        card_content = build_alert_card(custom_payload)

    if not card_content:
        return None

    attachment = Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card_content,
    )
    return MessageFactory.attachment(attachment)


async def _extract_error_details(error: connector_models.ErrorResponseException) -> tuple[Any, Any, str]:
    """Try to pull status/headers/body information from BotFramework error responses."""

    def _maybe_decode(value: Any) -> str:
        if value is None:
            return "<no-body>"
        if isinstance(value, bytes):
            return value.decode("utf-8", "replace")
        return str(value)

    status = None
    reason = None
    body_text = "<no-body>"

    response = getattr(error, "response", None)
    candidates = [response] if response else []
    http_response = getattr(response, "http_response", None) if response else None
    if http_response:
        candidates.append(http_response)

    for candidate in filter(None, candidates):
        status = status or getattr(candidate, "status", None) or getattr(candidate, "status_code", None)
        reason = reason or getattr(candidate, "reason", None)

        for accessor_name in ("text", "read"):
            accessor = getattr(candidate, accessor_name, None)
            if not callable(accessor):
                continue
            try:
                payload = accessor()
                if inspect.isawaitable(payload):
                    payload = await payload
                if payload is not None:
                    body_text = _maybe_decode(payload)
                    break
            except Exception:
                continue
        else:
            raw_body = getattr(candidate, "body", None)
            if raw_body is not None:
                body_text = _maybe_decode(raw_body)

        if body_text != "<no-body>":
            break

    return status, reason, body_text


def _format_inner_error(error: connector_models.ErrorResponseException) -> dict[str, Any]:
    inner = getattr(error, "inner_exception", None)
    if not inner:
        return {}
    payload: dict[str, Any] = {}
    err_obj = getattr(inner, "error", None)
    if err_obj:
        payload["code"] = getattr(err_obj, "code", None)
        payload["message"] = getattr(err_obj, "message", None)
        payload["inner_error"] = getattr(err_obj, "inner_error", None)
    for attr in ("status", "status_code", "response"):
        val = getattr(inner, attr, None)
        if val is not None and attr not in payload:
            payload[attr] = val
    return payload
        
@app.get("/")
async def root():
    return {"service": app.title, "adapter": ADAPTER_KIND, "ready": True}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return render_dashboard_html(ACTIVE_DASHBOARD_ROLES)


@app.get("/dashboard/service", response_class=HTMLResponse)
async def service_dashboard_page():
    return render_service_dashboard_html()


@app.get("/dashboard/risk", response_class=HTMLResponse)
async def risk_dashboard_page():
    return render_risk_dashboard_html()

@app.get("/dashboard/tactico", response_class=HTMLResponse)
async def tactical_dashboard_page():
    return render_tactical_dashboard_html()


@app.get("/dashboard/ejecutivo", response_class=HTMLResponse)
async def executive_dashboard_page():
    return render_executive_dashboard_html()


@app.get("/dashboard/data")
async def dashboard_data():
    if not settings.CONTROLLER_METRICS_URL:
        raise HTTPException(status_code=503, detail="controller_metrics_url_not_configured")
    try:
        raw = await fetch_controller_metrics(settings.CONTROLLER_METRICS_URL)
    except Exception as exc:
        log.error("Error consulting controller metrics: %s", exc)
        raise HTTPException(status_code=502, detail="controller_metrics_unavailable")
    return build_dashboard_payload(raw, ACTIVE_DASHBOARD_ROLES)


def _controller_base_url() -> str:
    if settings.CONTROLLER_BASE_URL:
        return settings.CONTROLLER_BASE_URL.rstrip("/")
    # Derivar base removiendo el último segmento de metrics
    url = settings.CONTROLLER_METRICS_URL.rstrip("/")
    parts = url.rsplit("/", 1)
    return parts[0] if len(parts) == 2 else url


@app.get("/dashboard/data/risk")
async def dashboard_risk(request: Request):
    base = _controller_base_url()
    qs = request.url.query
    url = f"{base}/risk"
    if qs:
        url = f"{url}?{qs}"
    try:
        return await fetch_controller_generic(url)
    except Exception as exc:
        log.error("Error consulting controller risk: %s", exc)
        raise HTTPException(status_code=502, detail="controller_risk_unavailable")


@app.get("/dashboard/data/runs")
async def dashboard_runs():
    base = _controller_base_url()
    url = f"{base}/runs"
    try:
        return await fetch_controller_generic(url)
    except Exception as exc:
        log.error("Error consulting controller runs: %s", exc)
        raise HTTPException(status_code=502, detail="controller_runs_unavailable")

@app.get("/dashboard/data/risk/summary")
async def dashboard_risk_summary():
    base = _controller_base_url()
    url = f"{base}/risk/summary"
    try:
        return await fetch_controller_generic(url)
    except Exception as exc:
        log.error("Error consulting controller risk summary: %s", exc)
        raise HTTPException(status_code=502, detail="controller_risk_summary_unavailable")

@app.get("/controller/tactical")
async def controller_tactical_proxy():
    base = _controller_base_url()
    url = f"{base}/controller/tactical"
    try:
        return await fetch_controller_generic(url)
    except Exception as exc:
        log.error("Error consulting controller tactical: %s", exc)
        raise HTTPException(status_code=502, detail="controller_tactical_unavailable")

@app.get("/controller/executive")
async def controller_executive_proxy():
    base = _controller_base_url()
    url = f"{base}/controller/executive"
    try:
        return await fetch_controller_generic(url)
    except Exception as exc:
        log.error("Error consulting controller executive: %s", exc)
        raise HTTPException(status_code=502, detail="controller_executive_unavailable")


@app.get("/dashboard/data/operations")
async def dashboard_operations():
    base = _controller_base_url()
    url = f"{base}/operations"
    try:
        return await fetch_controller_generic(url)
    except Exception as exc:
        log.error("Error consulting controller operations: %s", exc)
        raise HTTPException(status_code=502, detail="controller_operations_unavailable")


@app.get("/dashboard/data/executive")
async def dashboard_executive():
    base = _controller_base_url()
    url = f"{base}/executive"
    try:
        return await fetch_controller_generic(url)
    except Exception as exc:
        log.error("Error consulting controller executive: %s", exc)
        raise HTTPException(status_code=502, detail="controller_executive_unavailable")

@app.get("/__bf-token")
async def bf_token():
    from botframework.connector.auth import MicrosoftAppCredentials
    creds = MicrosoftAppCredentials(
        settings.MICROSOFT_APP_ID,
        settings.MICROSOFT_APP_PASSWORD,
        settings.MICROSOFT_APP_TENANT_ID,
        settings.MICROSOFT_APP_OAUTH_SCOPE,
    )
    tok = creds.get_access_token()
    if inspect.isawaitable(tok):
        tok = await tok
    # Solo inspección: header.payload (sin verificación)
    import base64, json
    def _b64url_decode(seg):
        seg += '=' * (-len(seg) % 4)
        return base64.urlsafe_b64decode(seg.encode())
    parts = tok.split(".")
    payload = {}
    try:
        payload = json.loads(_b64url_decode(parts[1]))
    except Exception:
        pass
    return {
        "oauth_scope": getattr(creds, "oauth_scope", "<unknown>"),
        "aud": payload.get("aud"),
        "appid": payload.get("appid"),
        "iss": payload.get("iss"),
    }


async def _log_auth_context() -> None:
    """Emit diagnostic information when AppCredentials cannot produce an access token."""
    log.error(
        "AppCredentials debug → type=%s tenant=%s scope=%s app_id=%s",
        os.getenv("MicrosoftAppType"),
        os.getenv("MicrosoftAppTenantId"),
        os.getenv("MicrosoftAppOAuthScope"),
        settings.MICROSOFT_APP_ID,
    )
    creds = MicrosoftAppCredentials(
        settings.MICROSOFT_APP_ID,
        settings.MICROSOFT_APP_PASSWORD,
        settings.MICROSOFT_APP_TENANT_ID,
        settings.MICROSOFT_APP_OAUTH_SCOPE,
    )
    try:
        tok = creds.get_access_token()
        if inspect.isawaitable(tok):
            tok = await tok
    except Exception as auth_exc:
        log.error("Access-token fetch raised: %r", auth_exc)
        return

    if isinstance(tok, str):
        log.error("Access-token sample (first 32 chars): %s…", tok[:32])
    else:
        log.error("Access-token payload (non-string): %r", tok)
