import json
import logging
import os
import re
from collections.abc import Sequence
from datetime import timedelta
from typing import Any, Optional, Protocol

import httpx
import mcp.types as mcp_types
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "rest"
DEFAULT_MCP_PAGE_SIZE = 50
DEFAULT_TIMEOUT_SECONDS = 120
GET_ACTOR_OUTPUT_TOOL = "get-actor-output"


class PlacesProvider(Protocol):
    async def initialize(self) -> None: ...

    async def fetch_items(
        self, actor_input: dict[str, Any]
    ) -> list[dict[str, Any]]: ...

    async def close(self) -> None: ...


def resolve_places_provider_mode() -> str:
    explicit_mode = (os.getenv("PLACES_PROVIDER") or "").strip().lower()
    if explicit_mode in {"static", "rest", "mcp"}:
        return explicit_mode
    if explicit_mode:
        logger.warning(
            "Unsupported PLACES_PROVIDER='%s'. Falling back to '%s'.",
            explicit_mode,
            DEFAULT_PROVIDER,
        )
        return DEFAULT_PROVIDER

    legacy_mode = (os.getenv("APIFY_DATA_MODE", "live") or "live").strip().lower()
    if legacy_mode == "static":
        return "static"
    if legacy_mode == "live":
        return DEFAULT_PROVIDER

    logger.warning(
        "Unsupported APIFY_DATA_MODE='%s'. Falling back to '%s'.",
        legacy_mode,
        DEFAULT_PROVIDER,
    )
    return DEFAULT_PROVIDER


def actor_name_to_mcp_tool_name(actor_name: str) -> str:
    if "/" not in actor_name:
        return actor_name
    username, actor_slug = actor_name.split("/", 1)
    safe_username = username.replace(".", "-dot-")
    return f"{safe_username}--{actor_slug}"


def create_places_provider(
    actor_id: str,
    default_location: str,
) -> PlacesProvider:
    provider_mode = resolve_places_provider_mode()
    if provider_mode == "static":
        return StaticPlacesProvider(default_location=default_location)
    if provider_mode == "mcp":
        return McpPlacesProvider(actor_id=actor_id)
    return RestPlacesProvider(actor_id=actor_id)


class RestPlacesProvider:
    def __init__(self, actor_id: str):
        self.actor_id = actor_id
        self.base_url = os.getenv("APIFY_BASE_URL", "https://api.apify.com")
        self.token = (os.getenv("APIFY_TOKEN") or "").strip()
        self.timeout_seconds = _read_positive_int_env(
            "APIFY_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS
        )
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout_seconds)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch_items(self, actor_input: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.token or self.token.startswith("<"):
            logger.error(
                "APIFY_TOKEN is missing or placeholder; live REST call skipped."
            )
            return []

        await self.initialize()
        assert self._client is not None

        url = f"{self.base_url}/v2/acts/{self.actor_id.replace('/', '~')}/run-sync-get-dataset-items"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Apify-Token": self.token,
        }
        logger.info(
            "Running Apify REST actor '%s' with input: %s",
            self.actor_id,
            json.dumps(actor_input),
        )
        try:
            resp = await self._client.post(url, json=actor_input, headers=headers)
            if resp.status_code >= 400:
                logger.error(
                    "Apify REST call failed: %s %s — %s",
                    resp.status_code,
                    resp.reason_phrase,
                    resp.text[:500],
                )
                return []
            data = resp.json()
            return _coerce_items(data)
        except httpx.RequestError as exc:
            logger.exception("Apify REST network error: %s", exc)
            return []
        except Exception as exc:
            logger.exception("Apify REST unexpected error: %s", exc)
            return []


class StaticPlacesProvider:
    def __init__(self, default_location: str):
        self.default_location = default_location
        self.static_dir = os.getenv(
            "APIFY_STATIC_DIR",
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "static_data", "apify"
            ),
        )
        self.static_file = (os.getenv("APIFY_STATIC_FILE") or "").strip()

    async def initialize(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def fetch_items(self, actor_input: dict[str, Any]) -> list[dict[str, Any]]:
        return self._load_static_items(actor_input)

    def _load_static_items(self, actor_input: dict[str, Any]) -> list[dict[str, Any]]:
        if self.static_file:
            path = os.path.join(self.static_dir, self.static_file)
            return self._read_json_list(path)

        query = "".join(actor_input.get("searchStringsArray", [])[:1]).lower()
        location = (
            str(actor_input.get("locationQuery", "")).lower().replace(",", "").strip()
        )

        def slug(*parts: str) -> str:
            return (
                "_".join(
                    [str(part).strip().replace(" ", "-") for part in parts if part]
                ).lower()
                + ".json"
            )

        candidates: list[str] = []
        if "chinese" in query and ("austin" in query or "austin" in location):
            candidates.append(slug("chinese", "in", "austin"))
        if "italian" in query and ("hyderabad" in query or "hyderabad" in location):
            candidates.append(slug("italian", "in", "hyderabad"))
        if "continental" in query and ("london" in query or "london" in location):
            candidates.append(slug("continental", "in", "london"))
        if "indian" in query and (
            "new york" in query or "new-york" in location or "nyc" in location
        ):
            candidates.append("7_indian_in_new-york.json")
        if ("cafe" in query or "cafes" in query) and (
            "france" in query or "france" in location
        ):
            candidates.append(slug("cafes", "in", "france"))

        if not candidates and query:
            first = query.split()[0]
            if location:
                candidates.append(slug(first, "in", location))

        for name in candidates:
            path = os.path.join(self.static_dir, name)
            if os.path.exists(path):
                return self._read_json_list(path)

        default_path = os.path.join(self.static_dir, "default.json")
        if os.path.exists(default_path):
            return self._read_json_list(default_path)

        logger.warning("No matching static Apify fixture found. Returning empty list.")
        return []

    @staticmethod
    def _read_json_list(path: str) -> list[dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            logger.error("Failed reading static data file %s: %s", path, exc)
            return []
        return _coerce_items(data)


class McpPlacesProvider:
    def __init__(self, actor_id: str):
        self.actor_id = actor_id
        self.mcp_url = os.getenv(
            "APIFY_MCP_URL",
            f"https://mcp.apify.com?tools={actor_id}",
        )
        self.token = (os.getenv("APIFY_TOKEN") or "").strip()
        self.tool_name = (
            os.getenv("APIFY_MCP_TOOL_NAME") or actor_name_to_mcp_tool_name(actor_id)
        ).strip()
        self.get_output_tool_name = (
            os.getenv("APIFY_MCP_GET_OUTPUT_TOOL", GET_ACTOR_OUTPUT_TOOL)
            or GET_ACTOR_OUTPUT_TOOL
        ).strip()
        self.page_size = _read_positive_int_env(
            "APIFY_MCP_PAGE_SIZE", DEFAULT_MCP_PAGE_SIZE
        )
        self.timeout_seconds = _read_positive_int_env(
            "APIFY_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS
        )
        self._http_client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        if self._http_client is not None:
            return
        headers = {}
        if self.token and not self.token.startswith("<"):
            headers["Authorization"] = f"Bearer {self.token}"
        self._http_client = httpx.AsyncClient(
            headers=headers,
            timeout=self.timeout_seconds,
        )

    async def close(self) -> None:
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def fetch_items(self, actor_input: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.token or self.token.startswith("<"):
            logger.error(
                "APIFY_TOKEN is missing or placeholder; live MCP call skipped."
            )
            return []

        await self.initialize()
        assert self._http_client is not None

        logger.info(
            "Running Apify MCP actor '%s' via tool '%s' with input: %s",
            self.actor_id,
            self.tool_name,
            json.dumps(actor_input),
        )

        try:
            async with streamable_http_client(
                self.mcp_url,
                http_client=self._http_client,
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    actor_result = await self._call_actor_tool_raw(session, actor_input)
                    if getattr(actor_result, "isError", False):
                        logger.error(
                            "Apify MCP actor tool '%s' returned an MCP error: %s",
                            self.tool_name,
                            _summarize_tool_result(actor_result),
                        )
                        return []

                    direct_items, _ = self._extract_output_items(actor_result)
                    dataset_id = self._extract_dataset_id(actor_result)
                    logger.info(
                        "Apify MCP actor tool '%s' returned dataset_id=%s, direct_items=%s.",
                        self.tool_name,
                        dataset_id or "<none>",
                        len(direct_items),
                    )

                    if dataset_id:
                        try:
                            full_items = await self._fetch_full_dataset(
                                session, dataset_id
                            )
                            if full_items:
                                return full_items
                            logger.warning(
                                "Apify MCP dataset '%s' returned no paged items; falling back to direct actor items.",
                                dataset_id,
                            )
                        except Exception as exc:
                            logger.exception(
                                "Apify MCP full dataset fetch failed for dataset '%s'; falling back to direct actor items. Error: %s",
                                dataset_id,
                                exc,
                            )

                    if direct_items:
                        logger.warning(
                            "Using direct Apify MCP actor items for tool '%s'.",
                            self.tool_name,
                        )
                        return direct_items

                    await self._log_available_tools(session)
                    logger.error(
                        "Apify MCP actor '%s' returned neither datasetId nor parseable items.",
                        self.tool_name,
                    )
                    return []
        except Exception as exc:
            logger.exception("Apify MCP unexpected error: %s", exc)
            return []

    async def _call_actor_tool_raw(
        self,
        session: ClientSession,
        actor_input: dict[str, Any],
    ) -> mcp_types.CallToolResult:
        return await session.send_request(
            mcp_types.ClientRequest(
                mcp_types.CallToolRequest(
                    params=mcp_types.CallToolRequestParams(
                        name=self.tool_name,
                        arguments=actor_input,
                    )
                )
            ),
            mcp_types.CallToolResult,
            request_read_timeout_seconds=timedelta(seconds=self.timeout_seconds),
        )

    async def _fetch_full_dataset(
        self,
        session: ClientSession,
        dataset_id: str,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        offset = 0

        while True:
            page_result = await session.call_tool(
                self.get_output_tool_name,
                arguments={
                    "datasetId": dataset_id,
                    "offset": offset,
                    "limit": self.page_size,
                },
                read_timeout_seconds=timedelta(seconds=self.timeout_seconds),
            )
            page_items, total_items = self._extract_output_items(page_result)
            logger.info(
                "Apify MCP dataset '%s' page offset=%s returned %s items%s.",
                dataset_id,
                offset,
                len(page_items),
                f", total={total_items}" if total_items is not None else "",
            )
            if not page_items:
                break

            items.extend(page_items)
            offset += len(page_items)
            if total_items is not None and len(items) >= total_items:
                break
            if len(page_items) < self.page_size:
                break

        logger.info(
            "Fetched %s full dataset items from Apify MCP dataset '%s'.",
            len(items),
            dataset_id,
        )
        return items

    async def _log_available_tools(self, session: ClientSession) -> None:
        try:
            tools_result = await session.list_tools()
        except Exception as exc:
            logger.warning("Unable to list Apify MCP tools for debugging: %s", exc)
            return

        tool_names = [
            tool.name
            for tool in getattr(tools_result, "tools", [])
            if getattr(tool, "name", None)
        ]
        logger.info(
            "Available Apify MCP tools: %s",
            ", ".join(tool_names) if tool_names else "<none>",
        )

    @staticmethod
    def _extract_dataset_id(result: Any) -> Optional[str]:
        structured = _extract_structured_content(result)
        dataset_id = _find_dataset_id(structured)
        if dataset_id:
            return dataset_id

        for text in _extract_text_blobs(result):
            payload = _try_parse_json_text(text)
            dataset_id = _find_dataset_id(payload)
            if dataset_id:
                return dataset_id
            match = re.search(r'"datasetId"\s*:\s*"([^"]+)"', text)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _extract_output_items(
        result: Any,
    ) -> tuple[list[dict[str, Any]], Optional[int]]:
        structured = _extract_structured_content(result)
        items, total = _find_items_payload(structured)
        if items:
            return items, total

        for text in _extract_text_blobs(result):
            payload = _try_parse_json_text(text)
            items, total = _find_items_payload(payload)
            if items:
                return items, total
        return [], None


def _read_positive_int_env(name: str, default: int) -> int:
    raw_value = (os.getenv(name) or "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        logger.warning(
            "Invalid integer for %s='%s'. Using %s.", name, raw_value, default
        )
        return default
    if value <= 0:
        logger.warning(
            "Non-positive integer for %s='%s'. Using %s.", name, raw_value, default
        )
        return default
    return value


def _extract_structured_content(result: Any) -> Any:
    if hasattr(result, "structuredContent"):
        return getattr(result, "structuredContent")
    if isinstance(result, dict):
        return result.get("structuredContent")
    return None


def _extract_text_blobs(result: Any) -> list[str]:
    raw_content = getattr(result, "content", None)
    if raw_content is None and isinstance(result, dict):
        raw_content = result.get("content")
    if not isinstance(raw_content, Sequence):
        return []

    texts: list[str] = []
    for part in raw_content:
        if hasattr(part, "type") and getattr(part, "type", None) == "text":
            text = getattr(part, "text", None)
            if isinstance(text, str) and text:
                texts.append(text)
            continue
        if isinstance(part, dict) and part.get("type") == "text":
            text = part.get("text")
            if isinstance(text, str) and text:
                texts.append(text)
    return texts


def _try_parse_json_text(text: str) -> Any:
    cleaned = (text or "").strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:].strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    try:
        return json.loads(cleaned)
    except Exception:
        return None


def _coerce_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        payload = payload.get("items")
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _find_dataset_id(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ("datasetId", "defaultDatasetId"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for key in (
            "result",
            "data",
            "output",
            "payload",
            "response",
            "actorRun",
            "run",
        ):
            nested_id = _find_dataset_id(payload.get(key))
            if nested_id:
                return nested_id

        for value in payload.values():
            nested_id = _find_dataset_id(value)
            if nested_id:
                return nested_id
    elif isinstance(payload, list):
        for value in payload:
            nested_id = _find_dataset_id(value)
            if nested_id:
                return nested_id
    return None


def _find_items_payload(payload: Any) -> tuple[list[dict[str, Any]], Optional[int]]:
    if isinstance(payload, list):
        direct_items = _coerce_items(payload)
        if direct_items:
            return direct_items, None
        return [], None

    if not isinstance(payload, dict):
        return [], None

    for key in ("items", "previewItems", "datasetItems", "results"):
        items = _coerce_items(payload.get(key))
        if items:
            return items, _extract_total_count(payload)

    for key in ("result", "data", "output", "payload", "response"):
        items, total = _find_items_payload(payload.get(key))
        if items:
            return items, total

    return [], None


def _extract_total_count(payload: dict[str, Any]) -> Optional[int]:
    for key in ("totalItemCount", "total", "count", "itemsCount"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
    return None


def _summarize_tool_result(result: Any) -> str:
    texts = _extract_text_blobs(result)
    if texts:
        return texts[0][:300]

    structured = _extract_structured_content(result)
    if structured is not None:
        try:
            return json.dumps(structured)[:300]
        except Exception:
            return str(structured)[:300]

    return "<no error details>"
