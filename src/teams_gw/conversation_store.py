from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ChannelAccount, ConversationAccount, ConversationReference


@dataclass
class StoredConversation:
    reference: ConversationReference
    conversation_id: str
    user_id: Optional[str]
    aad_object_id: Optional[str]
    tenant_id: Optional[str]
    service_url: Optional[str]
    user_name: Optional[str]

    def summary(self) -> Dict[str, Optional[str]]:
        payload = asdict(self)
        payload.pop("reference", None)
        return payload


class ConversationStore:
    """In-memory registry of conversation references for proactive messaging."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._by_conversation: Dict[str, StoredConversation] = {}
        self._user_index: Dict[str, str] = {}
        self._aad_index: Dict[str, str] = {}

    async def remember(self, activity: Activity) -> Optional[StoredConversation]:
        reference = TurnContext.get_conversation_reference(activity)
        convo = reference.conversation or ConversationAccount()
        user = reference.user or ChannelAccount()

        conversation_id = convo.id
        if not conversation_id:
            return None

        stored = StoredConversation(
            reference=reference,
            conversation_id=conversation_id,
            user_id=user.id,
            aad_object_id=getattr(user, "aad_object_id", None),
            tenant_id=getattr(convo, "tenant_id", None),
            service_url=reference.service_url,
            user_name=user.name,
        )

        async with self._lock:
            self._by_conversation[conversation_id] = stored
            if stored.user_id:
                self._user_index[stored.user_id] = conversation_id
            if stored.aad_object_id:
                self._aad_index[stored.aad_object_id] = conversation_id
        return stored

    async def resolve(
        self,
        *,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        aad_object_id: Optional[str] = None,
    ) -> Optional[ConversationReference]:
        async with self._lock:
            key = conversation_id
            if not key and user_id:
                key = self._user_index.get(user_id)
            if not key and aad_object_id:
                key = self._aad_index.get(aad_object_id)
            stored = self._by_conversation.get(key) if key else None
            return stored.reference if stored else None

    async def summaries(self) -> List[Dict[str, Optional[str]]]:
        async with self._lock:
            return [stored.summary() for stored in self._by_conversation.values()]


conversation_store = ConversationStore()
