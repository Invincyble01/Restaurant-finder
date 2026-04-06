# Server README

For full project setup from a fresh machine, start with the root `README.md`.

This folder contains the Python server for the Restaurant Finder demo.

## What This Folder Needs

- A working OCI profile on your machine
- `uv`
- The environment file at `app/server/.env`

Create the environment file from the template:

```bash
cp .env.example .env
```

For the easiest first run, use this minimal static setup in `.env`:

```env
PLACES_PROVIDER=static
DEFAULT_LOCATION=Austin, TX
```

You do not need to set `APIFY_STATIC_DIR` or `APIFY_STATIC_FILE` unless you want to override the built-in fixture defaults.

You still must fill these OCI values:

- `COMPARTMENT_ID`
- `AUTH_PROFILE`
- `SERVICE_ENDPOINT`

## Provider Modes

- `PLACES_PROVIDER=static` uses built-in fixtures.
- `PLACES_PROVIDER=rest` uses the direct Apify REST actor endpoint.
- `PLACES_PROVIDER=mcp` uses the hosted Apify MCP server and fetches full dataset items page by page.

These modes stay isolated: `mcp` does not fall back to REST, and `rest` does not use MCP.

If `PLACES_PROVIDER` is omitted, the server defaults to `static`.
Unsupported values cause server startup to fail.

For live modes, set `APIFY_TOKEN` and `APIFY_ACTOR`.

For REST mode, also set:

- `APIFY_BASE_URL`

For MCP mode, also set:

- `APIFY_MCP_URL`
- `APIFY_MCP_TOOL_NAME`
- `APIFY_MCP_PAGE_SIZE`

Optional advanced settings:

- `APIFY_TIMEOUT_SECONDS`
- `APIFY_MCP_GET_OUTPUT_TOOL`

## Install Dependencies

```bash
uv sync
```

## Run Only the Server

```bash
uv run __main__.py
```

By default, the server runs at `http://localhost:10002`.

Use `localhost`, not `127.0.0.1`, because the client is configured for the localhost flow.
