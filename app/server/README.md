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
APIFY_DATA_MODE=static
DEFAULT_LOCATION=Austin, TX
```

You do not need to set `APIFY_STATIC_DIR` or `APIFY_STATIC_FILE` unless you want to override the built-in fixture defaults.

You still must fill these OCI values:

- `COMPARTMENT_ID`
- `AUTH_PROFILE`
- `SERVICE_ENDPOINT`

Only add `APIFY_TOKEN`, `APIFY_ACTOR`, and `APIFY_BASE_URL` if you later switch to live Apify mode.

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
