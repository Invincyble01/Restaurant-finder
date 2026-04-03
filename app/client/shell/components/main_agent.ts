import { provide } from "@lit/context"
import { consume } from "@lit/context"
import {
  LitElement,
  html,
  css,
  nothing,
  HTMLTemplateResult,
  unsafeCSS,
} from "lit"
import { customElement, property, state } from "lit/decorators.js"
import { theme as uiTheme } from "../theme/default-theme.js"
import { A2UIRouter, routerContext } from "../services/a2ui-router.js"
import {
  SnackbarAction,
  SnackbarMessage,
  SnackbarUUID,
  SnackType,
} from "../types/types.js"
import { type Snackbar } from "../ui/snackbar.js"
import { repeat } from "lit/directives/repeat.js"
import { v0_8 } from "@a2ui/lit"
import * as UI from "@a2ui/lit/ui"

import "../ui/ui.js"
import "./config_canvas.js"

import { AppConfig } from "../configs/types.js"
import { config as restaurantConfig } from "../configs/restaurant.js"

@customElement("dynamic-module")
export class DynamicModule extends LitElement {
  @provide({ context: UI.Context.themeContext })
  accessor theme: v0_8.Types.Theme = uiTheme

  @consume({ context: routerContext })
  accessor router!: A2UIRouter

  @property({ type: String })
  accessor title = ""

  @property({ type: String })
  accessor subtitle = ""

  @property({ type: String })
  accessor color = "transparent"

  @property({ type: Object })
  accessor config: AppConfig = restaurantConfig

  @state()
  accessor response = ""

  @state()
  accessor status: Array<{ timestamp: string; message: string; type: string }> = [
    { timestamp: new Date().toISOString(), message: "Ready", type: "initial" },
  ]

  @state()
  accessor #requesting = false

  @state()
  accessor #error: string | null = null

  @state()
  accessor #lastMessages: v0_8.Types.ServerToClientMessage[] = []

  @state()
  accessor #loadingTextIndex = 0

  @state()
  accessor #startTime: number | null = null

  @state()
  accessor #elapsedTime: number | null = null

  @state()
  accessor #currentElapsedTime: number | null = null

  @state()
  accessor #showStatusFeed = false

  #processor = v0_8.Data.createSignalA2uiMessageProcessor()
  #loadingInterval: number | undefined
  #stopwatchInterval: number | undefined
  #snackbar: Snackbar | undefined = undefined
  #pendingSnackbarMessages: Array<{
    message: SnackbarMessage
    replaceAll: boolean
  }> = []

  #onStreamingEvent = (event: Event) => {
    const streamingEvent = (event as CustomEvent).detail
    this.updateStatusFromStreamingEvent(streamingEvent)
    this.processMessages(streamingEvent)
  }

  #onMessageSent = (event: Event) => {
    const sentEvent = (event as CustomEvent).detail
    if (sentEvent.serverUrl !== this.config.serverUrl) {
      return
    }

    this.#requesting = true
    this.#error = null
    this.#startTime = sentEvent.timestamp
    this.#elapsedTime = null
    this.#currentElapsedTime = 0
    this.#startLoadingAnimation()
    this.#startStopwatch()
  }

  static styles = [
    unsafeCSS(v0_8.Styles.structuralStyles),
    css`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        height: 100%;
        color: var(--rf-ink);
        font-family: var(--font-copy);
      }

      .module-shell {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 20px;
        height: 100%;
        min-height: 0;
        padding: 20px;
      }

      .module-shell.with-status {
        grid-template-columns: minmax(0, 1fr) 320px;
      }

      .main-panel,
      .status-shell {
        min-height: 0;
        border-radius: 28px;
        background: rgba(255, 255, 255, 0.68);
        backdrop-filter: blur(20px);
        box-shadow: var(--rf-shadow);
      }

      .main-panel {
        display: grid;
        grid-template-rows: auto auto 1fr;
        overflow: hidden;
      }

      .panel-header {
        display: grid;
        gap: 18px;
        padding: 24px 24px 18px;
        border-bottom: 1px solid rgba(109, 122, 119, 0.08);
      }

      .panel-topline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
      }

      .panel-controls {
        display: inline-flex;
        align-items: center;
        justify-content: flex-end;
        gap: 10px;
        flex-wrap: wrap;
      }

      .panel-kicker {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--rf-tertiary);
      }

      .panel-kicker::before {
        content: "";
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: linear-gradient(135deg, var(--rf-primary), var(--rf-primary-strong));
        box-shadow: 0 0 0 6px rgba(134, 246, 228, 0.18);
      }

      .state-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 9px 14px;
        border-radius: 999px;
        background: rgba(243, 243, 243, 0.88);
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--rf-muted);
      }

      .state-pill strong {
        color: var(--rf-ink);
        font-weight: 600;
      }

      .feed-toggle {
        appearance: none;
        border: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 10px 14px;
        border-radius: 999px;
        background: rgba(243, 243, 243, 0.9);
        color: var(--rf-ink);
        font-family: var(--font-copy);
        font-size: 0.84rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: inset 0 0 0 1px rgba(109, 122, 119, 0.12);
        transition: background 160ms ease, transform 160ms ease;
      }

      .feed-toggle:hover {
        background: rgba(228, 226, 225, 0.92);
        transform: translateY(-1px);
      }

      .feed-toggle-indicator {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: linear-gradient(135deg, var(--rf-primary), var(--rf-primary-strong));
      }

      .title-wrap {
        display: grid;
        gap: 10px;
      }

      .title-wrap h2 {
        margin: 0;
        font-family: var(--font-display);
        font-size: clamp(1.45rem, 2vw, 2.2rem);
        line-height: 1.05;
        letter-spacing: -0.04em;
        font-weight: 800;
      }

      .title-wrap p {
        margin: 0;
        max-width: 68ch;
        color: var(--rf-ink-muted);
        font-size: 0.96rem;
        line-height: 1.65;
      }

      .headline-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .meta-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        border-radius: 18px;
        background: rgba(243, 243, 243, 0.9);
        color: var(--rf-ink-muted);
        font-size: 0.84rem;
        line-height: 1.3;
      }

      .meta-chip strong {
        color: var(--rf-ink);
        font-weight: 600;
      }

      .error {
        margin: 0 24px;
        padding: 16px 18px;
        border-radius: 20px;
        color: var(--e-30);
        background: rgba(255, 218, 214, 0.78);
      }

      .stage {
        min-height: 0;
        overflow: auto;
        padding: 0 24px 24px;
      }

      .stage.has-results {
        overflow: hidden;
      }

      .pending,
      .ready-state,
      .surfaces-container {
        min-height: 100%;
      }

      .pending {
        display: grid;
        place-items: center;
        padding: 28px 0;
      }

      .pending-shell {
        width: min(100%, 760px);
        display: grid;
        gap: 26px;
        justify-items: center;
        padding: 36px 20px 8px;
      }

      .loading-core {
        position: relative;
        width: min(68vw, 360px);
        aspect-ratio: 1;
        display: grid;
        place-items: center;
      }

      .ring,
      .ring::before,
      .ring::after {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 50%;
        border: 1px solid rgba(109, 122, 119, 0.18);
      }

      .ring::before {
        inset: 32px;
        border-color: rgba(0, 104, 93, 0.18);
      }

      .ring::after {
        inset: 72px;
        border-color: rgba(0, 102, 109, 0.24);
      }

      .ring {
        animation: pulseRing 4s cubic-bezier(0.4, 0, 0.2, 1) infinite;
      }

      .crosshair-x,
      .crosshair-y {
        position: absolute;
        background: linear-gradient(90deg, transparent, rgba(109, 122, 119, 0.22), transparent);
      }

      .crosshair-x {
        width: 100%;
        height: 1px;
      }

      .crosshair-y {
        width: 1px;
        height: 100%;
        background: linear-gradient(180deg, transparent, rgba(109, 122, 119, 0.22), transparent);
      }

      .core-box {
        position: relative;
        display: grid;
        place-items: center;
        width: 126px;
        height: 126px;
        border-radius: 28px;
        background: var(--rf-surface-elevated);
        box-shadow: 0 20px 40px rgba(0, 107, 95, 0.08);
      }

      .core-box::before,
      .core-box::after {
        content: "";
        position: absolute;
        inset: 16px;
      }

      .core-box::before {
        border: 2px solid rgba(0, 104, 93, 0.18);
        transform: rotate(45deg);
      }

      .core-box::after {
        inset: 26px;
        border: 1px solid rgba(0, 102, 109, 0.28);
      }

      .core-icon {
        position: relative;
        z-index: 1;
        font-family: "Material Symbols Outlined", "Google Symbols";
        font-size: 2.85rem;
        color: var(--rf-primary);
        font-variation-settings: "FILL" 1, "wght" 400, "GRAD" 0, "opsz" 48;
      }

      .floating-chip,
      .floating-chip-secondary {
        position: absolute;
        padding: 8px 12px;
        border-radius: 999px;
        font-family: var(--font-mono);
        font-size: 0.7rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .floating-chip {
        top: 58px;
        right: 10px;
        background: rgba(228, 226, 225, 0.84);
        color: var(--rf-muted);
      }

      .floating-chip-secondary {
        bottom: 54px;
        left: 12px;
        background: rgba(134, 246, 228, 0.28);
        color: #005048;
      }

      .pending-copy {
        display: grid;
        gap: 12px;
        text-align: center;
        max-width: 560px;
      }

      .pending-kicker {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--rf-tertiary);
      }

      .pending-copy h3 {
        margin: 0;
        font-family: var(--font-display);
        font-size: clamp(1.6rem, 2.5vw, 2.4rem);
        line-height: 1.06;
        letter-spacing: -0.04em;
      }

      .pending-copy p {
        margin: 0;
        color: var(--rf-ink-muted);
        line-height: 1.65;
      }

      .pending-meta {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 8px;
      }

      .pending-meta span {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 12px;
        border-radius: 16px;
        background: rgba(243, 243, 243, 0.84);
        color: var(--rf-muted);
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .ready-state {
        display: grid;
        align-content: start;
        gap: 24px;
        padding: 10px 0 0;
      }

      .ready-hero {
        display: grid;
        grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.9fr);
        gap: 16px;
      }

      .ready-copy,
      .ready-panel {
        padding: 24px;
        border-radius: 28px;
        background: rgba(243, 243, 243, 0.82);
      }

      .ready-copy {
        display: grid;
        gap: 14px;
      }

      .ready-copy span,
      .ready-panel span {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--rf-tertiary);
      }

      .ready-copy h3,
      .ready-panel h3 {
        margin: 0;
        font-family: var(--font-display);
        font-size: clamp(1.5rem, 2.1vw, 2.1rem);
        line-height: 1.08;
        letter-spacing: -0.04em;
      }

      .ready-copy p,
      .ready-panel p {
        margin: 0;
        color: var(--rf-ink-muted);
        line-height: 1.65;
      }

      .prompt-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
      }

      .prompt-card {
        display: grid;
        gap: 10px;
        padding: 18px;
        border-radius: 22px;
        background: rgba(255, 255, 255, 0.72);
        box-shadow: inset 0 0 0 1px rgba(109, 122, 119, 0.08);
      }

      .prompt-card strong {
        font-family: var(--font-display);
        font-size: 1rem;
        letter-spacing: -0.02em;
      }

      .prompt-card p {
        margin: 0;
        color: var(--rf-ink-muted);
        line-height: 1.55;
        font-size: 0.9rem;
      }

      .surfaces-container {
        display: grid;
        grid-template-rows: auto 1fr;
        gap: 18px;
        min-height: 100%;
        height: 100%;
        padding-top: 10px;
      }

      .surfaces-intro {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
      }

      .surfaces-intro strong {
        font-family: var(--font-display);
        font-size: 1.1rem;
        letter-spacing: -0.03em;
      }

      .surfaces-intro span {
        color: var(--rf-ink-muted);
        font-size: 0.92rem;
      }

      .surfaces {
        display: grid;
        gap: 18px;
        min-height: 0;
      }

      .surface-frame {
        display: grid;
        gap: 12px;
        min-height: 0;
      }

      .surface-note {
        font-family: var(--font-mono);
        font-size: 0.68rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--rf-muted);
        padding-left: 8px;
      }

      a2ui-surface {
        display: block;
        border-radius: 28px;
        background: rgba(243, 243, 243, 0.82);
        padding: 18px;
        height: 100%;
        min-height: 0;
        overflow: hidden;
      }

      .status-shell {
        display: grid;
        grid-template-rows: auto auto 1fr;
        overflow: hidden;
      }

      .status-header {
        display: grid;
        gap: 10px;
        padding: 22px 22px 18px;
        border-bottom: 1px solid rgba(109, 122, 119, 0.08);
      }

      .status-header h3 {
        margin: 0;
        font-family: var(--font-display);
        font-size: 1.15rem;
        line-height: 1.05;
        letter-spacing: -0.03em;
      }

      .status-header p {
        margin: 0;
        color: var(--rf-ink-muted);
        line-height: 1.55;
        font-size: 0.88rem;
      }

      .status-summary {
        display: grid;
        gap: 12px;
        padding: 18px 22px;
        border-bottom: 1px solid rgba(109, 122, 119, 0.08);
      }

      .summary-card {
        display: grid;
        gap: 6px;
        padding: 16px 18px;
        border-radius: 20px;
        background: rgba(243, 243, 243, 0.92);
      }

      .summary-label {
        font-family: var(--font-mono);
        font-size: 0.68rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--rf-muted);
      }

      .summary-value {
        color: var(--rf-ink);
        font-size: 0.94rem;
        line-height: 1.5;
        font-weight: 600;
      }

      .status-feed {
        min-height: 0;
        overflow: auto;
        padding: 10px 12px 12px;
      }

      .status-item {
        display: grid;
        gap: 6px;
        margin-bottom: 10px;
        padding: 14px 14px 14px 16px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.8);
      }

      .status-item:last-child {
        margin-bottom: 0;
      }

      .status-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
      }

      .status-time,
      .status-kind {
        font-family: var(--font-mono);
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      .status-time {
        color: var(--rf-muted);
      }

      .status-kind {
        color: var(--rf-tertiary);
      }

      .status-message {
        color: var(--rf-ink);
        font-size: 0.88rem;
        line-height: 1.55;
      }

      @keyframes pulseRing {
        0% {
          transform: scale(0.96);
          opacity: 0.55;
        }

        50% {
          transform: scale(1.02);
          opacity: 0.18;
        }

        100% {
          transform: scale(0.96);
          opacity: 0.55;
        }
      }

      @media (max-width: 1120px) {
        .module-shell {
          grid-template-columns: 1fr;
        }

        .status-shell {
          min-height: 320px;
        }
      }

      @media (max-width: 820px) {
        .panel-header,
        .stage,
        .status-header,
        .status-summary {
          padding-left: 16px;
          padding-right: 16px;
        }

        .ready-hero,
        .prompt-grid {
          grid-template-columns: 1fr;
        }

        .pending-shell {
          padding-left: 0;
          padding-right: 0;
        }

        .loading-core {
          width: min(78vw, 300px);
        }

        a2ui-surface {
          padding: 14px;
          border-radius: 22px;
        }
      }
    `,
  ]

  connectedCallback() {
    super.connectedCallback()

    if (this.config.theme) {
      this.theme = this.config.theme
    }

    window.document.title = this.config.title
    window.document.documentElement.style.setProperty("--background", this.config.background)

    if (this.router) {
      this.router.addEventListener("streaming-event", this.#onStreamingEvent)
      this.router.addEventListener("message-sent", this.#onMessageSent)
    }
  }

  disconnectedCallback() {
    if (this.router) {
      this.router.removeEventListener("streaming-event", this.#onStreamingEvent)
      this.router.removeEventListener("message-sent", this.#onMessageSent)
    }

    this.#stopLoadingAnimation()
    this.#stopStopwatch()
    super.disconnectedCallback()
  }

  #startLoadingAnimation() {
    if (Array.isArray(this.config.loadingText) && this.config.loadingText.length > 1) {
      this.#loadingTextIndex = 0
      this.#loadingInterval = window.setInterval(() => {
        this.#loadingTextIndex =
          (this.#loadingTextIndex + 1) % (this.config.loadingText as string[]).length
      }, 2000)
    }
  }

  #stopLoadingAnimation() {
    if (this.#loadingInterval) {
      clearInterval(this.#loadingInterval)
      this.#loadingInterval = undefined
    }
  }

  #startStopwatch() {
    this.#stopStopwatch()
    this.#stopwatchInterval = window.setInterval(() => {
      if (this.#startTime && this.#elapsedTime === null) {
        this.#currentElapsedTime = Date.now() - this.#startTime
        this.requestUpdate()
      }
    }, 100)
  }

  #stopStopwatch() {
    if (this.#stopwatchInterval) {
      clearInterval(this.#stopwatchInterval)
      this.#stopwatchInterval = undefined
    }
    this.#currentElapsedTime = null
  }

  private updateStatusFromStreamingEvent(event: any) {
    if (event.serverUrl !== this.config.serverUrl) return

    if (event.kind === "status-update") {
      const status = event.status
      const isFinal = event.final
      const state = status?.state
      const hasMessage = status?.message?.parts?.length > 0

      const serverState: Array<any> = hasMessage
        ? event.status.message.parts
        : [{ text: "Server did not send any message parts" }]
      const serverMessage = serverState[0].text || "No text content"

      if (state === "failed") {
        this.status = [
          ...this.status,
          {
            timestamp: new Date().toISOString(),
            message: "Task failed - An error occurred",
            type: event.kind,
          },
        ]
      } else {
        this.status = [
          ...this.status,
          {
            timestamp: new Date().toISOString(),
            message: serverMessage,
            type: event.kind,
          },
        ]
      }

      if (hasMessage && this.#startTime) {
        this.#elapsedTime = Date.now() - this.#startTime
        this.#stopStopwatch()
      }

      if (isFinal || state === "completed" || state === "failed") {
        this.#requesting = false
        this.#stopLoadingAnimation()
      }
    } else if (event.kind === "task") {
      this.status = [
        ...this.status,
        {
          timestamp: new Date().toISOString(),
          message: "Task management event received",
          type: event.kind,
        },
      ]
    } else if (event.kind === "message") {
      this.status = [
        ...this.status,
        {
          timestamp: new Date().toISOString(),
          message: "Direct message received",
          type: event.kind,
        },
      ]
    } else {
      this.status = [
        ...this.status,
        {
          timestamp: new Date().toISOString(),
          message: `Event type: ${event.kind || "unknown"}`,
          type: event.kind,
        },
      ]
    }
  }

  private processMessages(event: any) {
    if (event.serverUrl !== this.config.serverUrl) return

    if (event.kind === "status-update" && event.status?.message?.parts) {
      const newMessages: v0_8.Types.ServerToClientMessage[] = []
      for (const part of event.status.message.parts) {
        if (part.kind === "data") {
          const a2uiMessage = part.data as v0_8.Types.ServerToClientMessage
          newMessages.push(a2uiMessage)
        }
      }

      if (newMessages.length > 0) {
        this.#lastMessages = newMessages
        this.#processor.clearSurfaces()
        this.#processor.processMessages(this.#lastMessages)
        this.#requesting = false
        this.#stopLoadingAnimation()
      }
    }
  }

  snackbar(
    message: string | HTMLTemplateResult,
    type: SnackType,
    actions: SnackbarAction[] = [],
    persistent = false,
    id = globalThis.crypto.randomUUID(),
    replaceAll = false
  ) {
    if (!this.#snackbar) {
      this.#pendingSnackbarMessages.push({
        message: {
          id,
          message,
          type,
          persistent,
          actions,
        },
        replaceAll,
      })
      return
    }

    return this.#snackbar.show(
      {
        id,
        message,
        type,
        persistent,
        actions,
      },
      replaceAll
    )
  }

  unsnackbar(id?: SnackbarUUID) {
    if (!this.#snackbar) {
      return
    }

    this.#snackbar.hide(id)
  }

  #currentStateLabel() {
    if (this.#requesting) {
      return "Streaming"
    }

    if (this.#error) {
      return "Error"
    }

    if (this.#surfaceCount() > 0) {
      return "Results"
    }

    return "Ready"
  }

  #surfaceCount() {
    return this.#processor.getSurfaces().size
  }

  #latestStatus() {
    return this.status.length > 0 ? this.status[this.status.length - 1] : null
  }

  #elapsedLabel() {
    const value = this.#elapsedTime ?? this.#currentElapsedTime
    return value ? this.#formatDuration(value) : "Idle"
  }

  #formatDuration(durationMs: number) {
    if (durationMs < 1000) {
      return `${durationMs} ms`
    }

    const seconds = durationMs / 1000
    if (seconds < 60) {
      return `${seconds.toFixed(seconds >= 10 ? 1 : 2)} s`
    }

    const minutes = Math.floor(seconds / 60)
    const remainderSeconds = Math.round(seconds % 60)
    return `${minutes}m ${String(remainderSeconds).padStart(2, "0")}s`
  }

  render() {
    const hasResults = this.#surfaceCount() > 0

    return html`
      <div class=${this.#showStatusFeed ? "module-shell with-status" : "module-shell"}>
        <section class="main-panel">
          <header class="panel-header">
            <div class="panel-topline">
              <span class="panel-kicker">Dining intelligence</span>
              <div class="panel-controls">
                <span class="state-pill"
                  >State <strong>${this.#currentStateLabel()}</strong></span
                >
                <button class="feed-toggle" @click=${this.#toggleStatusFeed}>
                  <span class="feed-toggle-indicator"></span>
                  ${this.#showStatusFeed ? "Hide activity feed" : "Show activity feed"}
                </button>
              </div>
            </div>

            <div class="title-wrap">
              <h2>${this.title || this.config.title}</h2>
              <p>
                ${this.subtitle ||
                "A single surface for search, restaurant comparison, live map context, and reservation confirmation."}
              </p>
            </div>

            <div class="headline-meta">
              <span class="meta-chip"><strong>Server</strong> ${this.config.serverUrl}</span>
              <span class="meta-chip"><strong>Latency</strong> ${this.#elapsedLabel()}</span>
              <span class="meta-chip"
                ><strong>Latest</strong> ${this.#latestStatus()?.message ?? "Awaiting query"}</span
              >
            </div>
          </header>

          ${this.#maybeRenderError()}

          <section class=${hasResults ? "stage has-results" : "stage"}>${this.#maybeRenderData()}</section>
        </section>

        ${this.#showStatusFeed ? this.#renderStatusWindow() : nothing}
      </div>
    `
  }

  #maybeRenderError() {
    if (!this.#error) return nothing

    return html`<div class="error">${this.#error}</div>`
  }

  #maybeRenderData() {
    if (this.#requesting) {
      let text = "Architecting your dining options..."
      if (this.config.loadingText) {
        if (Array.isArray(this.config.loadingText)) {
          text = this.config.loadingText[this.#loadingTextIndex]
        } else {
          text = this.config.loadingText
        }
      }

      return this.#renderLoadingState(text)
    }

    const surfaces = this.#processor.getSurfaces()
    if (surfaces.size === 0) {
      return this.#renderReadyState()
    }

    return html`<div class="surfaces-container">
      <div class="surfaces-intro">
        <strong>Result canvas</strong>
        <span>
          Review restaurants, inspect the live map, and move directly into the reservation flow.
        </span>
      </div>

      <section class="surfaces">
        ${repeat(
          surfaces,
          ([surfaceId]) => surfaceId,
          ([surfaceId, surface]) => {
            return html`<div class="surface-frame">
              <a2ui-surface
                @restaurant-pin-selected=${this.#onRestaurantPinSelected}
                @a2uiaction=${async (evt: v0_8.Events.StateEvent<"a2ui.action">) => {
                  const [target] = evt.composedPath()
                  if (!(target instanceof HTMLElement)) {
                    return
                  }

                  const context: v0_8.Types.A2UIClientEventMessage["userAction"]["context"] = {}
                  if (evt.detail.action.context) {
                    const srcContext = evt.detail.action.context
                    for (const item of srcContext) {
                      if (item.value.literalBoolean) {
                        context[item.key] = item.value.literalBoolean
                      } else if (item.value.literalNumber) {
                        context[item.key] = item.value.literalNumber
                      } else if (item.value.literalString) {
                        context[item.key] = item.value.literalString
                      } else if (item.value.path) {
                        const path = this.#processor.resolvePath(
                          item.value.path,
                          evt.detail.dataContextPath
                        )
                        const value = this.#processor.getData(
                          evt.detail.sourceComponent,
                          path,
                          surfaceId
                        )
                        context[item.key] = value
                      }
                    }
                  }

                  const message: v0_8.Types.A2UIClientEventMessage = {
                    userAction: {
                      name: evt.detail.action.name,
                      surfaceId,
                      sourceComponentId: target.id,
                      timestamp: new Date().toISOString(),
                      context,
                    },
                  }

                  if (this.router) {
                    this.#requesting = true
                    this.#startLoadingAnimation()
                    try {
                      await this.router.sendA2UIMessage(
                        this.config.serverUrl || "http://localhost:10002",
                        message
                      )
                    } catch (err) {
                      this.snackbar(err as string, SnackType.ERROR)
                    } finally {
                      this.#requesting = false
                      this.#stopLoadingAnimation()
                    }
                  }
                }}
                .surfaceId=${surfaceId}
                .enableCustomElements=${true}
                .surface=${surface}
                .processor=${this.#processor}
              ></a2ui-surface>
              <span class="surface-note">Map pins stay synced with cards and clicking a pin jumps to that restaurant.</span>
            </div>`
          }
        )}
      </section>
    </div>`
  }

  #renderLoadingState(text: string) {
    return html`<div class="pending">
      <div class="pending-shell">
        <div class="loading-core" aria-hidden="true">
          <div class="ring"></div>
          <div class="crosshair-x"></div>
          <div class="crosshair-y"></div>
          <div class="core-box">
            <span class="core-icon g-icon filled">terminal</span>
          </div>
          <span class="floating-chip">v0.8 surface</span>
          <span class="floating-chip-secondary">Map + reservation</span>
        </div>

        <div class="pending-copy">
          <span class="pending-kicker">Live generation in progress</span>
          <h3>${text}</h3>
          <p>
            ${this.#latestStatus()?.message ??
            "Streaming status updates arrive here while restaurant cards and map data are prepared."}
          </p>
          <div class="pending-meta">
            <span>Neural sync</span>
            <span>Spatial mapping</span>
            <span>Reservation framing</span>
          </div>
        </div>
      </div>
    </div>`
  }

  #renderReadyState() {
    return html`<div class="ready-state">
      <div class="ready-hero">
        <section class="ready-copy">
          <span>Search ready</span>
          <h3>Describe the kind of restaurant you want to find.</h3>
          <p>
            Try a cuisine and city, a mood and time of day, or a more expressive dining brief.
            Results will arrive as restaurant cards paired with a live map and booking actions.
          </p>
        </section>

        <aside class="ready-panel">
          <span>Current workflow</span>
          <h3>Search, compare, reserve.</h3>
          <p>
            The query bar stays persistent while the response surface updates underneath, so the
            transition from landing to results stays uninterrupted.
          </p>
        </aside>
      </div>

      <div class="prompt-grid">
        <article class="prompt-card">
          <strong>City + cuisine</strong>
          <p>Best ramen spots in Seattle with strong reviews and easy reservations.</p>
        </article>
        <article class="prompt-card">
          <strong>Mood + occasion</strong>
          <p>Quiet anniversary dinner in Chicago with a modern dining room and good wine.</p>
        </article>
        <article class="prompt-card">
          <strong>Casual planning</strong>
          <p>Top brunch restaurants in Austin with outdoor seating and easy group booking.</p>
        </article>
      </div>
    </div>`
  }

  #renderStatusWindow() {
    const latestStatus = this.#latestStatus()

    return html`<aside class="status-shell">
      <div class="status-header">
        <h3>Activity feed</h3>
        <p>
          Stream status, routing messages, and response timing stay visible while the main surface
          focuses on restaurants and reservations.
        </p>
      </div>

      <div class="status-summary">
        <div class="summary-card">
          <span class="summary-label">Current state</span>
          <span class="summary-value">${this.#currentStateLabel()}</span>
        </div>
        <div class="summary-card">
          <span class="summary-label">Elapsed</span>
          <span class="summary-value">${this.#elapsedLabel()}</span>
        </div>
        <div class="summary-card">
          <span class="summary-label">Latest message</span>
          <span class="summary-value">${latestStatus?.message ?? "Ready to receive a query."}</span>
        </div>
      </div>

      <div class="status-feed">
        ${repeat(
          [...this.status].reverse(),
          (item) => `${item.timestamp}-${item.message}`,
          (item) => html`<div class="status-item">
            <div class="status-meta">
              <span class="status-time">${new Date(item.timestamp).toLocaleTimeString()}</span>
              <span class="status-kind">${item.type || "status"}</span>
            </div>
            <div class="status-message">${item.message}</div>
          </div>`
        )}
      </div>
    </aside>`
  }

  #toggleStatusFeed = () => {
    this.#showStatusFeed = !this.#showStatusFeed
  }

  #onRestaurantPinSelected = (event: Event) => {
    const detail = (event as CustomEvent).detail as
      | { surfaceId?: string | null; restaurantKey?: string | null; restaurantName?: string | null }
      | undefined

    const restaurantKey = detail?.restaurantKey?.trim()
    if (!restaurantKey) {
      return
    }

    this.#scrollRestaurantCard(detail?.surfaceId ?? null, restaurantKey)
  }

  #scrollRestaurantCard(surfaceId: string | null, restaurantKey: string) {
    const surfaceElements = Array.from(this.renderRoot.querySelectorAll("a2ui-surface")) as Array<HTMLElement & {
      surfaceId?: string | null
      shadowRoot?: ShadowRoot | null
      showListPane?: () => void
    }>

    for (const surfaceElement of surfaceElements) {
      if (surfaceId && surfaceElement.surfaceId && surfaceElement.surfaceId !== surfaceId) {
        continue
      }

      const card = this.#findRestaurantCard(surfaceElement.shadowRoot, restaurantKey)
      if (!card) {
        continue
      }

      surfaceElement.showListPane?.()
      requestAnimationFrame(() => {
        const revealedCard = this.#findRestaurantCard(surfaceElement.shadowRoot, restaurantKey)
        if (!revealedCard) {
          return
        }

        revealedCard.scrollIntoView({ behavior: "smooth", block: "start", inline: "nearest" })
        this.#flashRestaurantCard(revealedCard)
      })
      break
    }
  }

  #findRestaurantCard(root: ShadowRoot | null | undefined, restaurantKey: string) {
    if (!root) {
      return null
    }

    const cards = Array.from(root.querySelectorAll("a2ui-card[data-restaurant-key]")) as HTMLElement[]
    return cards.find((card) => card.getAttribute("data-restaurant-key") === restaurantKey) ?? null
  }

  #flashRestaurantCard(card: HTMLElement) {
    card.animate(
      [
        { transform: "translateY(0)", boxShadow: "0 0 0 rgba(0, 0, 0, 0)" },
        { transform: "translateY(-4px)", boxShadow: "0 24px 42px rgba(0, 107, 95, 0.18)" },
        { transform: "translateY(0)", boxShadow: "0 0 0 rgba(0, 0, 0, 0)" },
      ],
      { duration: 700, easing: "ease" }
    )
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "dynamic-module": DynamicModule
  }
}
