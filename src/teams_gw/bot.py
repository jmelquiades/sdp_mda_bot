from __future__ import annotations

import logging

from botbuilder.core import ActivityHandler, ConversationState, TurnContext

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
        reply_text = self._render_reply(incoming_text)
        await turn_context.send_activity(reply_text)

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
