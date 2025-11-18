import asyncio

from botbuilder.schema import ChannelAccount, ConversationAccount, ConversationReference

from src.teams_gw.conversation_store import ConversationStore


def build_reference(conversation_id: str, user_id: str, aad_id: str | None = None):
    return ConversationReference(
        service_url="https://example.org",
        channel_id="msteams",
        conversation=ConversationAccount(id=conversation_id, tenant_id="tenant-123"),
        user=ChannelAccount(id=user_id, name="Tester", aad_object_id=aad_id),
        bot=ChannelAccount(id="bot-id"),
    )


def test_store_resolves_by_conversation_id():
    async def _run():
        store = ConversationStore()
        reference = build_reference("conv-1", "user-1", "aad-1")
        summary = await store.remember(reference)

        assert summary.conversation_id == "conv-1"
        resolved = await store.resolve(conversation_id="conv-1")
        assert resolved.conversation.id == "conv-1"

    asyncio.run(_run())


def test_store_resolves_by_user_indexes():
    async def _run():
        store = ConversationStore()
        reference = build_reference("conv-2", "user-2", "aad-2")
        await store.remember(reference)

        by_user = await store.resolve(user_id="user-2")
        assert by_user.user.id == "user-2"

        by_aad = await store.resolve(aad_object_id="aad-2")
        assert getattr(by_aad.user, "aad_object_id", None) == "aad-2"

    asyncio.run(_run())


def test_store_returns_summaries():
    async def _run():
        store = ConversationStore()
        await store.remember(build_reference("conv-3", "user-3"))
        await store.remember(build_reference("conv-4", "user-4"))

        summaries = await store.summaries()
        assert len(summaries) == 2
        assert any(item["conversation_id"] == "conv-3" for item in summaries)

    asyncio.run(_run())
