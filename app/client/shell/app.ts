import { LitElement, html, css } from "lit"
import { customElement } from "lit/decorators.js"
import { provide } from "@lit/context"
import { a2uiRouter, routerContext } from "./services/a2ui-router.js"
import "./components/chatTextArea"
import "./components/main_agent"

@customElement("app-container")
export class AppContainer extends LitElement {
  @provide({ context: routerContext })
  accessor router = a2uiRouter;

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      width: 100%;
      height: 100%;
      overflow: auto;
      background: #1a2332;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .container {
      display: flex;
      flex-direction: column;
      height: 100%;
      padding: 0.5rem;
      gap: 0.5rem;
    }

    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: white;
      font-size: 1rem;
      font-weight: 300;
      margin-bottom: 0rem;
    }

    .controls {
      display: flex;
      gap: 1rem;
      align-items: center;
    }

    .control {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: white;
      font-size: 1rem;
    }

    .modules {
      display: flex;
      flex-wrap: wrap;
      gap: 1.5rem;
      flex: 1;
      width: 100%;
    }
  `

  render() {
    return html`
      <div class="container">
        <div class="header">
          RESTAURANT FINDER
        </div>
        <div class="modules">
          <dynamic-module
            title="Dynamic agent"
            subtitle="App using agent cluster and A2UI events for dynamic UI"
            color="#3c5d8b">
          </dynamic-module>
        </div>
        <chat-input></chat-input>
      </div>
    `
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "app-container": AppContainer
  }
}
