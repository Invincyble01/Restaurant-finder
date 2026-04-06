import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agent.graph.places_providers import (
    McpPlacesProvider,
    actor_name_to_mcp_tool_name,
    resolve_places_provider_mode,
)


class PlacesProviderModeTests(unittest.TestCase):
    def test_accepts_rest_mode(self):
        with patch.dict(os.environ, {"PLACES_PROVIDER": "rest"}, clear=True):
            self.assertEqual(resolve_places_provider_mode(), "rest")

    def test_prefers_explicit_places_provider(self):
        with patch.dict(os.environ, {"PLACES_PROVIDER": "mcp"}):
            self.assertEqual(resolve_places_provider_mode(), "mcp")

    def test_defaults_to_static_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_places_provider_mode(), "static")

    def test_defaults_to_static_with_unrelated_environment(self):
        with patch.dict(os.environ, {"UNRELATED_ENV": "live"}, clear=True):
            self.assertEqual(resolve_places_provider_mode(), "static")

    def test_invalid_places_provider_raises(self):
        with patch.dict(os.environ, {"PLACES_PROVIDER": "weird"}, clear=True):
            with self.assertRaisesRegex(ValueError, "Unsupported PLACES_PROVIDER"):
                resolve_places_provider_mode()


class McpHelperTests(unittest.TestCase):
    def test_actor_name_to_tool_name(self):
        self.assertEqual(
            actor_name_to_mcp_tool_name("compass/crawler-google-places"),
            "compass--crawler-google-places",
        )
        self.assertEqual(
            actor_name_to_mcp_tool_name("acme.dev/my-actor"),
            "acme-dot-dev--my-actor",
        )

    def test_extract_dataset_id_from_structured_content(self):
        provider = McpPlacesProvider(actor_id="compass/crawler-google-places")
        result = {"structuredContent": {"datasetId": "dataset-123"}}
        self.assertEqual(provider._extract_dataset_id(result), "dataset-123")

    def test_extract_dataset_id_from_text_fallback(self):
        provider = McpPlacesProvider(actor_id="compass/crawler-google-places")
        result = {
            "content": [
                {
                    "type": "text",
                    "text": '```json\n{"datasetId": "dataset-456"}\n```',
                }
            ]
        }
        self.assertEqual(provider._extract_dataset_id(result), "dataset-456")

    def test_extract_dataset_id_from_wrapped_structured_content(self):
        provider = McpPlacesProvider(actor_id="compass/crawler-google-places")
        result = {"structuredContent": {"result": {"datasetId": "dataset-789"}}}
        self.assertEqual(provider._extract_dataset_id(result), "dataset-789")

    def test_extract_output_items_from_structured_content(self):
        result = {
            "structuredContent": {
                "items": [{"title": "One"}, {"title": "Two"}],
                "totalItemCount": 2,
            }
        }
        items, total = McpPlacesProvider._extract_output_items(result)
        self.assertEqual(items, [{"title": "One"}, {"title": "Two"}])
        self.assertEqual(total, 2)

    def test_extract_output_items_from_wrapped_structured_content(self):
        result = {
            "structuredContent": {
                "result": {
                    "items": [{"title": "Wrapped"}],
                    "totalItemCount": 1,
                }
            }
        }
        items, total = McpPlacesProvider._extract_output_items(result)
        self.assertEqual(items, [{"title": "Wrapped"}])
        self.assertEqual(total, 1)

    def test_extract_output_items_from_direct_structured_content_list(self):
        result = {"structuredContent": [{"title": "Direct"}]}
        items, total = McpPlacesProvider._extract_output_items(result)
        self.assertEqual(items, [{"title": "Direct"}])
        self.assertIsNone(total)

    def test_extract_output_items_from_text_fallback(self):
        result = {
            "content": [
                {
                    "type": "text",
                    "text": '```json\n[{"title": "One"}]\n```',
                }
            ]
        }
        items, total = McpPlacesProvider._extract_output_items(result)
        self.assertEqual(items, [{"title": "One"}])
        self.assertIsNone(total)


class FakeStreamContext:
    async def __aenter__(self):
        return (object(), object(), lambda: None)

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, actor_result, page_results=None):
        self.actor_result = actor_result
        self.page_results = list(page_results or [])
        self.raw_call_count = 0
        self.actor_call_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def initialize(self):
        return None

    async def call_tool(self, name, arguments=None, read_timeout_seconds=None):
        if name == "compass--crawler-google-places":
            self.actor_call_count += 1
            raise AssertionError("Actor tool should use raw MCP request")
        if name == "get-actor-output":
            if self.page_results:
                return self.page_results.pop(0)
            return {"structuredContent": {"items": []}}
        raise AssertionError(f"Unexpected tool call: {name}")

    async def send_request(
        self,
        request,
        result_type,
        request_read_timeout_seconds=None,
        metadata=None,
        progress_callback=None,
    ):
        self.raw_call_count += 1
        return self.actor_result

    async def list_tools(self):
        return SimpleNamespace(
            tools=[SimpleNamespace(name="compass--crawler-google-places")]
        )


class McpFetchItemsTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_items_falls_back_to_direct_actor_items(self):
        with patch.dict(os.environ, {"APIFY_TOKEN": "test-token"}):
            provider = McpPlacesProvider(actor_id="compass/crawler-google-places")
            actor_result = {
                "content": [
                    {
                        "type": "text",
                        "text": '```json\n[{"title": "Jiang Nan Flushing", "address": "Queens"}]\n```',
                    }
                ]
            }
            fake_session = FakeSession(actor_result)

            with (
                patch(
                    "agent.graph.places_providers.streamable_http_client",
                    return_value=FakeStreamContext(),
                ),
                patch(
                    "agent.graph.places_providers.ClientSession",
                    return_value=fake_session,
                ),
            ):
                items = await provider.fetch_items(
                    {
                        "locationQuery": "New York",
                        "searchStringsArray": ["chinese restaurants"],
                    }
                )

        self.assertEqual(items, [{"title": "Jiang Nan Flushing", "address": "Queens"}])
        self.assertEqual(fake_session.raw_call_count, 1)
        self.assertEqual(fake_session.actor_call_count, 0)
        await provider.close()

    async def test_fetch_items_prefers_full_dataset_when_available(self):
        with patch.dict(os.environ, {"APIFY_TOKEN": "test-token"}):
            provider = McpPlacesProvider(actor_id="compass/crawler-google-places")
            actor_result = {
                "structuredContent": {
                    "result": {
                        "datasetId": "dataset-123",
                        "previewItems": [{"title": "Preview"}],
                    }
                }
            }
            page_results = [
                {
                    "structuredContent": {
                        "items": [{"title": "Full 1"}, {"title": "Full 2"}],
                        "totalItemCount": 2,
                    }
                }
            ]
            fake_session = FakeSession(actor_result, page_results=page_results)

            with (
                patch(
                    "agent.graph.places_providers.streamable_http_client",
                    return_value=FakeStreamContext(),
                ),
                patch(
                    "agent.graph.places_providers.ClientSession",
                    return_value=fake_session,
                ),
            ):
                items = await provider.fetch_items(
                    {
                        "locationQuery": "New York",
                        "searchStringsArray": ["chinese restaurants"],
                    }
                )

        self.assertEqual(items, [{"title": "Full 1"}, {"title": "Full 2"}])
        self.assertEqual(fake_session.raw_call_count, 1)
        self.assertEqual(fake_session.actor_call_count, 0)
        await provider.close()

    async def test_fetch_items_requires_token_in_mcp_mode(self):
        with patch.dict(os.environ, {"APIFY_TOKEN": ""}, clear=False):
            provider = McpPlacesProvider(actor_id="compass/crawler-google-places")
            items = await provider.fetch_items(
                {
                    "locationQuery": "New York",
                    "searchStringsArray": ["chinese restaurants"],
                }
            )

        self.assertEqual(items, [])
        await provider.close()


if __name__ == "__main__":
    unittest.main()
