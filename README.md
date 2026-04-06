# Restaurant Finder

This repository contains a restaurant-finding demo built on A2UI.

A2UI lets an agent build the UI for a task at runtime. In this demo, the server turns a restaurant request into a live interface with a search flow, restaurant cards, a map, and reservation actions.

This README is the main setup guide. Start here.

## Before You Start

You must set up your OCI profile first. This repo depends on OCI-backed models, so the app will not run correctly until your local machine already has working OCI credentials and a valid profile.

After your OCI profile is ready, come back here and continue.

## What You Will Install

If you have never used Node or npm before:

- `Node.js` runs the JavaScript and TypeScript parts of the project.
- `npm` comes with Node.js and installs project dependencies.
- `uv` manages the Python environment and Python packages for the server.

For this repo, you need:

- Git
- Node.js `22.22.0`
- npm (included with Node.js)
- `uv`
- Python `3.13` (you can install it with `uv`)
- A browser
- An OCI profile that already works on your machine

## Repo Layout

- `app/server` - Python server and agent graph
- `renderers/web_core` - shared A2UI renderer package used by the UI
- `renderers/lit` - Lit renderer package used by the client shell
- `app/client` - client workspace that starts the Vite app and the server demo

Important: do not run `npm install` at the repository root. This repo does not have a runnable root-level npm project.

## macOS Setup From Scratch

These steps assume a fresh macOS machine after your OCI profile is already configured.

### 1. Install Homebrew

If `brew` is not installed yet, install it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then open a new Terminal window.

### 2. Install Git, nvm, and uv

```bash
brew install git nvm uv
```

### 3. Clone the Repository

```bash
git clone <your-repository-url>
cd Restaurant-finder
```

### 4. Configure `nvm`

macOS uses `zsh` by default. Run the commands below exactly once:

```bash
mkdir -p "$HOME/.nvm"
cat <<'EOF' >> "$HOME/.zshrc"
export NVM_DIR="$HOME/.nvm"
[ -s "$(brew --prefix nvm)/nvm.sh" ] && . "$(brew --prefix nvm)/nvm.sh"
EOF
source "$HOME/.zshrc"
```

If you use `bash` instead of `zsh`, replace `.zshrc` with `.bashrc`.

### 5. Install the Correct Node.js Version

This repo pins Node in `.nvmrc`.

From the repo root, run:

```bash
nvm install
nvm use
node -v
npm -v
```

`node -v` should show `v22.22.0`.

### 6. Install Python 3.13 With `uv`

```bash
uv python install 3.13
uv --version
```

You do not need to create a Python virtual environment manually. `uv sync` will handle that for this project.

### 7. Create the Server Environment File

Copy the template:

```bash
cp app/server/.env.example app/server/.env
```

Open `app/server/.env` in your editor and fill in the OCI values:

- `COMPARTMENT_ID`
- `AUTH_PROFILE`
- `SERVICE_ENDPOINT`

For the easiest first run, use the minimal static-mode setup below in `app/server/.env`:

```env
COMPARTMENT_ID=<your-compartment-id>
AUTH_PROFILE=<your-oci-profile-name>
SERVICE_ENDPOINT=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com

PLACES_PROVIDER=static
DEFAULT_LOCATION=Austin, TX
```

Notes:

- Static mode is the easiest first run because it does not need an Apify token.
- Even in static mode, the app still needs working OCI access.
- In static mode, the server uses the built-in fixture defaults automatically.
- You can switch later to `PLACES_PROVIDER=rest` or `PLACES_PROVIDER=mcp` for live data.

### 8. Install Server Dependencies

```bash
cd app/server
uv sync
cd ../..
```

This creates the local Python environment for the server.

### 9. Build the Local Renderer Packages

The client depends on local renderer packages, so they must be built before the app can run.

Build `renderers/web_core`:

```bash
cd renderers/web_core
npm install
npm run build
cd ../..
```

Build `renderers/lit`:

```bash
cd renderers/lit
npm install
npm run build
cd ../..
```

### 10. Install Client Dependencies

```bash
cd app/client
npm install
cd shell
npm run build
cd ../..
```

### 11. Run the Full Demo

From `app/client`, start both the server and the client together:

```bash
cd app/client
npm run demo:restaurant
```

What this does:

- starts the Python server on `http://localhost:10002`
- starts the Vite client dev server

When Vite starts, it will print a local URL in the terminal. In most setups this is `http://localhost:5173`, but use the exact URL Vite prints.

Open that URL in your browser.

## Fastest Daily Run After Initial Setup

After the first setup is done, you usually only need:

```bash
cd /path/to/Restaurant-finder
nvm use
cd app/client
npm run demo:restaurant
```

If you pull changes that affect dependencies or renderer code, rebuild the affected packages.

## Run Server and Client Separately

Use this if you want one terminal per process.

Terminal 1:

```bash
cd /path/to/Restaurant-finder/app/server
uv run __main__.py
```

Terminal 2:

```bash
cd /path/to/Restaurant-finder/app/client
npm run serve:shell
```

## Switch to Live Apify Data Later

Once the static setup works, you can switch to live data.

`PLACES_PROVIDER` is the strict mode switch:

- `static` reads built-in fixtures only
- `rest` calls the Apify REST API only
- `mcp` calls the Apify MCP server only

If `PLACES_PROVIDER` is omitted, the server defaults to `static`.
Unsupported values cause server startup to fail.

Update `app/server/.env`:

```env
APIFY_TOKEN=<your-apify-token>
APIFY_ACTOR=compass/crawler-google-places
DEFAULT_LOCATION=Austin, TX
```

For direct REST mode:

```env
PLACES_PROVIDER=rest
APIFY_BASE_URL=https://api.apify.com
```

For hosted Apify MCP mode:

```env
PLACES_PROVIDER=mcp
APIFY_MCP_URL=https://mcp.apify.com?tools=compass/crawler-google-places
APIFY_MCP_TOOL_NAME=compass--crawler-google-places
APIFY_MCP_PAGE_SIZE=50
```

Optional advanced settings:

```env
APIFY_TIMEOUT_SECONDS=120
APIFY_MCP_GET_OUTPUT_TOOL=get-actor-output
```

Then restart the demo.

## Troubleshooting

### `nvm: command not found`

- Close Terminal and open it again.
- Or run `source "$HOME/.zshrc"`.

### `npm: command not found`

- Node.js is not active yet.
- Run:

```bash
nvm use
```

### `uv: command not found`

- Install it with Homebrew:

```bash
brew install uv
```

### The server fails to start or the UI stays empty

- Check that your OCI profile is already working outside this repo.
- Re-open `app/server/.env` and confirm:
  - `COMPARTMENT_ID`
  - `AUTH_PROFILE`
  - `SERVICE_ENDPOINT`
- For the easiest test, confirm you are using `PLACES_PROVIDER=static` first.
- In static mode, you do not need to set `APIFY_STATIC_DIR` or `APIFY_STATIC_FILE` unless you want to override the built-in fixture selection.

### The client cannot connect to the server

- Make sure the server is running on `http://localhost:10002`
- Use `localhost`, not `127.0.0.1`
- Do not change the server port unless you also update the client code

### You changed code in `renderers/web_core` or `renderers/lit`

Rebuild the changed renderer package, then restart the client:

```bash
cd /path/to/Restaurant-finder/renderers/web_core
npm run build

cd /path/to/Restaurant-finder/renderers/lit
npm run build
```

### You want to reset the Python environment

```bash
cd /path/to/Restaurant-finder/app/server
uv sync --reinstall
```

## Windows Setup Notes

macOS is the primary setup path for this project. Windows should still work.

### 1. Install Tools

Open PowerShell and install:

```powershell
winget install Git.Git
winget install CoreyButler.NVMforWindows
winget install AstralSoftware.UV
```

Open a new PowerShell window, then install the pinned Node version:

```powershell
nvm install 22.22.0
nvm use 22.22.0
node -v
npm -v
```

Install Python 3.13 with `uv`:

```powershell
uv python install 3.13
uv --version
```

### 2. Clone and Configure

```powershell
git clone <your-repository-url>
cd Restaurant-finder
Copy-Item app\server\.env.example app\server\.env
```

Edit `app\server\.env` the same way described in the macOS section. The easiest first run is still static mode.

### 3. Install and Run

```powershell
cd app\server
uv sync
cd ..\..

cd renderers\web_core
npm install
npm run build
cd ..\..

cd renderers\lit
npm install
npm run build
cd ..\..

cd app\client
npm install
cd shell
npm run build
cd ..
npm run demo:restaurant
```

## More README Files

These folder-level READMEs are now secondary references:

- `app/server/README.md`
- `app/client/README.md`
- `renderers/lit/README.md`

For first-time setup, always use this main README.
