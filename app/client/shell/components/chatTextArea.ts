import { LitElement, html, css } from "lit"
import { customElement, state } from "lit/decorators.js"
import { consume } from "@lit/context"
import { routerContext, A2UIRouter } from "../services/a2ui-router.js"
import { config as restaurantConfig } from "../configs/restaurant.js"

@customElement("chat-input")
export class ChatInput extends LitElement {
  @consume({ context: routerContext })
  accessor router!: A2UIRouter;

  @state()
  accessor #inputValue = ""

  private agentDefaultServer = restaurantConfig.serverUrl;

  static styles = css`
    :host {
      display: block;
      width: 100%;
    }

    .input-shell {
      display: grid;
      gap: 10px;
    }

    .hint-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 0 8px;
    }

    .hint {
      font-family: var(--font-mono);
      font-size: 0.72rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--rf-muted);
    }

    .capsule {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: var(--rf-radius-pill);
      background: rgba(255, 255, 255, 0.62);
      box-shadow: inset 0 0 0 1px rgba(109, 122, 119, 0.12);
      color: var(--rf-tertiary);
      font-family: var(--font-mono);
      font-size: 0.72rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    form {
      position: relative;
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      align-items: center;
      gap: 12px;
      padding: 12px;
      border-radius: 32px;
      background: rgba(255, 255, 255, 0.84);
      backdrop-filter: blur(26px);
      box-shadow: 0 30px 64px rgba(0, 107, 95, 0.16);
      border: 1px solid rgba(255, 255, 255, 0.7);
      overflow: hidden;
    }

    form::before {
      content: "";
      position: absolute;
      inset: -1px;
      border-radius: inherit;
      background: linear-gradient(135deg, rgba(134, 246, 228, 0.34), rgba(150, 241, 250, 0.08), rgba(0, 104, 93, 0.18));
      opacity: 0;
      transition: opacity 180ms ease;
      pointer-events: none;
    }

    form:focus-within::before {
      opacity: 1;
    }

    .search-icon {
      position: relative;
      z-index: 1;
      display: grid;
      place-items: center;
      width: 52px;
      height: 52px;
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(0, 104, 93, 0.14), rgba(0, 104, 93, 0.04));
      color: var(--rf-primary);
    }

    .material-symbols-outlined {
      font-family: "Material Symbols Outlined";
      font-weight: 400;
      font-style: normal;
      font-size: 24px;
      display: inline-block;
      line-height: 1;
      letter-spacing: normal;
      text-transform: none;
      white-space: nowrap;
      word-wrap: normal;
      direction: ltr;
      font-feature-settings: "liga";
      -webkit-font-feature-settings: "liga";
      -webkit-font-smoothing: antialiased;
      font-variation-settings: "FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24;
      user-select: none;
      overflow: hidden;
    }

    .field {
      position: relative;
      z-index: 1;
      display: grid;
      gap: 6px;
      min-width: 0;
    }

    .field-label {
      font-family: var(--font-mono);
      font-size: 0.68rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--rf-muted);
    }

    input {
      width: 100%;
      min-width: 0;
      border: none;
      background: transparent;
      color: var(--rf-ink);
      outline: none;
      font-family: var(--font-copy);
      font-size: clamp(0.98rem, 1.8vw, 1.15rem);
      font-weight: 500;
      letter-spacing: -0.02em;
      padding: 0;
    }

    input::placeholder {
      color: color-mix(in srgb, var(--rf-muted) 74%, white 26%);
    }

    button {
      position: relative;
      z-index: 1;
      appearance: none;
      border: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      min-width: 152px;
      padding: 0 20px;
      min-height: 56px;
      border-radius: 22px;
      background: linear-gradient(135deg, var(--rf-primary), var(--rf-primary-strong));
      color: var(--rf-primary-contrast);
      font-family: var(--font-copy);
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      cursor: pointer;
      box-shadow: 0 18px 40px rgba(0, 107, 95, 0.2);
      transition: transform 160ms ease, box-shadow 160ms ease, opacity 160ms ease;
    }

    button:hover {
      transform: translateY(-1px);
      box-shadow: 0 24px 44px rgba(0, 107, 95, 0.24);
    }

    button:active {
      transform: translateY(0);
    }

    button:disabled {
      cursor: default;
      opacity: 0.6;
      box-shadow: none;
    }

    .send-icon {
      font-size: 20px;
    }

    @media (max-width: 760px) {
      .hint-row {
        display: none;
      }

      form {
        grid-template-columns: 1fr;
        gap: 10px;
        padding: 14px;
        border-radius: 24px;
      }

      .search-icon {
        width: 46px;
        height: 46px;
        border-radius: 16px;
      }

      .field {
        order: 1;
      }

      button {
        width: 100%;
        min-width: 0;
        min-height: 50px;
        border-radius: 18px;
      }
    }
  `

  private async handleSubmit() {
    if (!this.#inputValue.trim() || !this.router) {
      return
    }

    try {
      this.router.sendTextMessage(this.agentDefaultServer, this.#inputValue.trim())
      this.#inputValue = ""
    } catch (error) {
      console.error("Failed to send message:", error)
    }
  }

  private handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault()
      this.handleSubmit()
    }
  }

  render() {
    return html`
      <div class="input-shell">
        <div class="hint-row" aria-hidden="true">
          <span class="hint">Describe cuisine, city, mood, or occasion</span>
          <span class="capsule">Live search canvas</span>
        </div>
        <form
          @submit=${(e: Event) => {
            e.preventDefault()
            this.handleSubmit()
          }}
        >
          <div class="search-icon" aria-hidden="true">
            <span class="material-symbols-outlined">search</span>
          </div>
          <label class="field">
            <span class="field-label">Dining brief</span>
            <input
              type="text"
              .value=${this.#inputValue}
              @input=${(e: Event) => (this.#inputValue = (e.target as HTMLInputElement).value)}
              @keydown=${this.handleKeyDown}
              placeholder=${restaurantConfig.placeholder}
            />
          </label>
          <button type="submit" ?disabled=${!this.#inputValue.trim()}>
            <span>Search</span>
            <span class="material-symbols-outlined send-icon" aria-hidden="true"
              >arrow_forward</span
            >
          </button>
        </form>
      </div>
    `
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "chat-input": ChatInput
  }
}
