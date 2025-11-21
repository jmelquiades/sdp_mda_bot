from __future__ import annotations

import logging
from typing import Any

from botbuilder.core import ActivityHandler, ConversationState, MessageFactory, TurnContext
from botbuilder.schema import Attachment

from .cards import demo_table_card, demo_ticket_card
from .conversation_store import conversation_store
from .settings import settings

log = logging.getLogger("teams_gw.bot")


class TeamsGatewayBot(ActivityHandler):
    """Minimal bot that replies to any incoming text and stores conversation references."""

    def __init__(self, conversation_state: ConversationState):
        self.conversation_state = conversation_state

    async def on_message_activity(self, turn_context: TurnContext):
        stored = await conversation_store.remember(turn_context.activity)
        if stored:
            log.debug(
                "Stored conversation reference: conversation_id=%s user_id=%s aad_object_id=%s",
                stored.conversation_id,
                stored.user_id,
                stored.aad_object_id,
            )

        incoming_text = (turn_context.activity.text or "").strip()
        normalized = incoming_text.lower()

        if normalized.startswith("ticket"):
            await self._send_card(turn_context, demo_ticket_card(), title="Demo: Ticket")
            return

        if normalized.startswith("tabla"):
            await self._send_card(turn_context, demo_table_card(), title="Demo: Tabla")
            return

        reply_text = self._render_reply(incoming_text)
        await turn_context.send_activity(reply_text)

    async def _send_card(self, turn_context: TurnContext, payload: dict[str, Any], title: str | None = None):
        if title:
            await turn_context.send_activity(title)
        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=payload,
        )
        await turn_context.send_activity(MessageFactory.attachment(attachment))

    def _render_reply(self, user_text: str) -> str:
        template = settings.BOT_DEFAULT_REPLY or "Hola, soy tu bot de Teams."
        placeholders = {
            "user_input": user_text or "",
            "bot_name": settings.BOT_DISPLAY_NAME,
        }
        try:
            return template.format(**placeholders)
        except KeyError:
            # In case the template uses unknown placeholders, just return it raw.
            return template
