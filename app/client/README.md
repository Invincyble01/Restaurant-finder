# Client README

For full setup from scratch, start with the root `README.md`.

This folder is the client workspace for the Restaurant Finder demo.

## Important

Before this client can run, these local packages must already be built:

- `renderers/web_core`
- `renderers/lit`

The root `README.md` explains the correct build order.

## Install Client Dependencies

From this folder:

```bash
npm install
```

## Run Only the Client

```bash
npm run serve:shell
```

## Run the Full Demo

This starts both the client and the server together:

```bash
npm run demo:restaurant
```

The server command assumes the Python server environment in `app/server` was already set up with `uv sync`.
