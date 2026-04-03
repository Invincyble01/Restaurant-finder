import { LitElement, html, css } from "lit"
import { customElement, state } from "lit/decorators.js"
import { provide } from "@lit/context"
import { a2uiRouter, routerContext } from "./services/a2ui-router.js"
import { config as restaurantConfig } from "./configs/restaurant.js"
import "./components/chatTextArea"
import "./components/main_agent"

@customElement("app-container")
export class AppContainer extends LitElement {
  @provide({ context: routerContext })
  accessor router = a2uiRouter;

  @state()
  accessor #hasQueried = false

  #onMessageSent = (event: Event) => {
    const detail = (event as CustomEvent).detail
    if (detail?.serverUrl === restaurantConfig.serverUrl) {
      this.#hasQueried = true
    }
  }

  static styles = css`
    :host {
      display: block;
      width: 100%;
      min-height: 100svh;
      color: var(--rf-ink);
      font-family: var(--font-copy);
    }

    .shell {
      position: relative;
      display: grid;
      grid-template-rows: auto 1fr auto;
      min-height: 100svh;
      padding: 24px;
      gap: 22px;
    }

    .shell.results-mode {
      grid-template-rows: 1fr auto;
    }

    .shell::before,
    .shell::after {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      z-index: 0;
    }

    .shell::before {
      inset: 24px;
      border-radius: 36px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0));
      border: 1px solid rgba(255, 255, 255, 0.55);
      mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.92), transparent 100%);
    }

    .shell::after {
      background:
        radial-gradient(circle at top left, rgba(134, 246, 228, 0.22), transparent 0 18%),
        radial-gradient(circle at 85% 12%, rgba(150, 241, 250, 0.16), transparent 0 14%);
      filter: blur(18px);
    }

    .masthead,
    .workspace,
    .search-dock {
      position: relative;
      z-index: 1;
    }

    .masthead {
      display: grid;
      grid-template-columns: minmax(0, 1.5fr) minmax(260px, 0.9fr);
      gap: 18px;
      align-items: start;
    }

    .brand {
      display: grid;
      gap: 14px;
      padding: 20px 22px;
      border-radius: 28px;
      background: rgba(255, 255, 255, 0.62);
      backdrop-filter: blur(20px);
      box-shadow: var(--rf-shadow);
      border: 1px solid rgba(255, 255, 255, 0.66);
    }

    .eyebrow {
      display: inline-flex;
      width: fit-content;
      align-items: center;
      gap: 10px;
      font-family: var(--font-mono);
      font-size: 0.7rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--rf-tertiary);
    }

    .eyebrow::after {
      content: "";
      width: 44px;
      height: 1px;
      background: rgba(0, 104, 93, 0.2);
    }

    h1 {
      margin: 0;
      font-family: var(--font-display);
      font-size: clamp(2.2rem, 5vw, 4.3rem);
      line-height: 0.94;
      letter-spacing: -0.05em;
      font-weight: 800;
      color: var(--rf-ink);
      max-width: 11ch;
    }

    .accent {
      color: var(--rf-primary);
      font-style: italic;
    }

    .lede {
      max-width: 54ch;
      margin: 0;
      font-size: 1rem;
      line-height: 1.65;
      color: var(--rf-ink-muted);
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .stat {
      padding: 16px 18px;
      border-radius: 22px;
      background: rgba(243, 243, 243, 0.86);
      box-shadow: inset 0 0 0 1px rgba(109, 122, 119, 0.08);
    }

    .stat-label {
      display: block;
      margin-bottom: 8px;
      font-family: var(--font-mono);
      font-size: 0.68rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--rf-muted);
    }

    .stat-value {
      display: block;
      font-family: var(--font-display);
      font-size: 1.35rem;
      font-weight: 750;
      letter-spacing: -0.03em;
      color: var(--rf-ink);
    }

    .meta-panel {
      display: grid;
      gap: 16px;
      padding: 22px;
      border-radius: 30px;
      background: rgba(243, 243, 243, 0.82);
      backdrop-filter: blur(18px);
      box-shadow: var(--rf-shadow);
    }

    .meta-title {
      margin: 0;
      font-family: var(--font-display);
      font-size: 1.1rem;
      font-weight: 700;
      letter-spacing: -0.03em;
      color: var(--rf-ink);
    }

    .meta-copy {
      margin: 0;
      color: var(--rf-ink-muted);
      line-height: 1.6;
      font-size: 0.94rem;
    }

    .meta-list {
      display: grid;
      gap: 12px;
    }

    .meta-item {
      display: grid;
      gap: 4px;
      padding: 14px 16px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.7);
    }

    .meta-kicker {
      font-family: var(--font-mono);
      font-size: 0.68rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--rf-tertiary);
    }

    .meta-value {
      font-size: 0.94rem;
      line-height: 1.5;
      color: var(--rf-ink-muted);
    }

    .workspace {
      min-height: 0;
      display: grid;
    }

    .canvas {
      min-height: 0;
      height: 100%;
      border-radius: 34px;
      background: rgba(255, 255, 255, 0.46);
      backdrop-filter: blur(20px);
      box-shadow: var(--rf-shadow-strong);
      overflow: hidden;
    }

    .search-dock {
      position: sticky;
      bottom: 0;
      display: grid;
      justify-items: center;
      padding-bottom: env(safe-area-inset-bottom, 0px);
    }

    chat-input {
      width: min(960px, 100%);
    }

    .results-mode .masthead {
      display: none;
    }

    .results-mode .workspace {
      min-height: calc(100svh - 150px);
    }

    @media (max-width: 1120px) {
      .masthead {
        grid-template-columns: 1fr;
      }

      h1 {
        max-width: 14ch;
      }
    }

    @media (max-width: 720px) {
      .shell {
        padding: 14px;
        gap: 14px;
      }

      .shell::before {
        inset: 14px;
        border-radius: 24px;
      }

      .brand,
      .meta-panel,
      .canvas {
        border-radius: 24px;
      }

      .stats {
        grid-template-columns: 1fr;
      }

      h1 {
        font-size: 2.25rem;
        max-width: none;
      }

      .lede {
        font-size: 0.95rem;
      }
    }
  `

  connectedCallback() {
    super.connectedCallback()
    this.router.addEventListener("message-sent", this.#onMessageSent)
  }

  disconnectedCallback() {
    this.router.removeEventListener("message-sent", this.#onMessageSent)
    super.disconnectedCallback()
  }

  render() {
    return html`
      <div class=${this.#hasQueried ? "shell results-mode" : "shell"}>
        <header class="masthead">
          <section class="brand">
            <span class="eyebrow">A2UI x Lit x MapLibre</span>
            <h1>Find restaurants with a more <span class="accent">intentional</span> lens.</h1>
            <p class="lede">
              Search by city, cuisine, mood, or occasion. Review top-rated spots, compare them
              on a live map, and move straight into reservation without leaving the results flow.
            </p>
            <div class="stats">
              <div class="stat">
                <span class="stat-label">Discovery</span>
                <span class="stat-value">Query-driven search</span>
              </div>
              <div class="stat">
                <span class="stat-label">Spatial View</span>
                <span class="stat-value">Pinned live map</span>
              </div>
              <div class="stat">
                <span class="stat-label">Reservation</span>
                <span class="stat-value">Book then review</span>
              </div>
            </div>
          </section>

          <aside class="meta-panel" aria-label="Product overview">
            <h2 class="meta-title">Architectural dining discovery</h2>
            <p class="meta-copy">
              The interface keeps the workflow compact: describe what you want, inspect the list,
              verify location fit on the map, and confirm a reservation in one continuous surface.
            </p>
            <div class="meta-list">
              <div class="meta-item">
                <span class="meta-kicker">Input</span>
                <span class="meta-value">Freeform dining queries with a command-bar search pattern.</span>
              </div>
              <div class="meta-item">
                <span class="meta-kicker">Output</span>
                <span class="meta-value">Restaurant imagery, ratings, tags, links, and reservation actions.</span>
              </div>
              <div class="meta-item">
                <span class="meta-kicker">Flow</span>
                <span class="meta-value">Search, stream, compare, reserve, then revisit confirmation.</span>
              </div>
            </div>
          </aside>
        </header>

        <main class="workspace">
          <section class="canvas">
            <dynamic-module
              title="Restaurant Finder"
              subtitle="Search, compare, map, and reserve in one interface"
              color="transparent"
            >
            </dynamic-module>
          </section>
        </main>

        <footer class="search-dock">
          <chat-input></chat-input>
        </footer>
      </div>
    `
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "app-container": AppContainer
  }
}
