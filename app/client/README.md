To run the client with `Lit` use. Requires node

First, set up the renderers:

Navigate to [renderers/web_core](../../renderers/web_core/) and run:

```bash
npm install
npm run build
```

Do the same on [renderers/lit](../../renderers/lit/) and run:

```bash
npm install
npm run build
```

Then go to the application folder [app/client](./) (this folder) and run:

```bash
npm install
npm run serve:shell
```

To run all with the server side using A2A do:

```bash
npm run demo:restaurant
```

`package.json` Commands are optimized for **Windows** using `shx` package, change to linux if required.

Make sure to run the MCP tool servers from the agent side:

Go to [server](../server/) and run using UV:

```bash
uv run agent/mcp/data_server.py
uv run agent/mcp/food_place_server.py
```

Both commands should be executed on different terminal instances since those are their own application MCP servers.

## Structure

1. [Components](./shell/components/) this folder contains the main application content for the three different calls, including the chat text area to send queries.
2. [Services](./shell/services/) this folder is critical since is routing text and a2ui messages to the different server endpoints, in charge of packing and streaming of events.