Setup (requires `uv`)

1. Create `.env` from [`./.env.example`](./.env.example).
2. Fill required OCI variables:
   - `COMPARTMENT_ID`
   - `AUTH_PROFILE`
   - `SERVICE_ENDPOINT`
3. Fill required Apify variables:
   - `APIFY_TOKEN`
   - `APIFY_ACTOR` (default: `compass/crawler-google-places`)
   - `APIFY_BASE_URL` (default: `https://api.apify.com`)
   - `APIFY_DATA_MODE` (default: `live`)
   - `DEFAULT_LOCATION` (fallback location for search queries without a place)

Mode behavior

- `APIFY_DATA_MODE=live`:
  - Calls Apify actor endpoint directly with schema-aligned input.
  - If `APIFY_TOKEN` is missing/placeholder, the server logs an error and returns empty results.
- `APIFY_DATA_MODE=static` (debug only):
  - Loads local fixture data from `APIFY_STATIC_DIR` / `APIFY_STATIC_FILE` (or default fixture).

Run the server

```bash
uv run __main__.py
```

Optional reset if environment metadata is broken:

```bash
uv init
uv sync
```
