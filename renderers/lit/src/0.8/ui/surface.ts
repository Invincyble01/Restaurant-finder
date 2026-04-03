/*
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */

import { html, css, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import * as Types from "@a2ui/web_core/types/types";
import { A2uiMessageProcessor } from "@a2ui/web_core/data/model-processor";
import { Root } from "./root.js";
import { styleMap } from "lit/directives/style-map.js";

@customElement("a2ui-surface")
export class Surface extends Root {
  @property()
  accessor surfaceId: Types.SurfaceID | null = null;

  @property()
  accessor surface: Types.Surface | null = null;

  @property()
  accessor processor: A2uiMessageProcessor | null = null;

  @property({ reflect: true, attribute: "mobile-pane" })
  accessor mobilePane: "list" | "map" = "list";

  @state()
  accessor #showMobilePaneToggle = false;

  static styles = [
    css`
      :host {
        --results-workspace-height: min(780px, calc(100dvh - 240px));
        display: flex;
        min-height: 0;
        max-height: 100%;
        flex-direction: column;
        gap: 18px;
        overflow: visible;
      }

      #surface-logo {
        display: flex;
        justify-content: center;

        & img {
          width: 50%;
          max-width: 220px;
        }
      }

      a2ui-root {
        flex: 1;
        min-height: 0;
        max-height: none;
      }

      a2ui-row#results-row {
        --a2ui-row-wrap: nowrap;
        align-items: stretch;
        gap: 22px;
        height: 100%;
        min-height: 0;
      }

      a2ui-column#results-column,
      a2ui-column#map-column {
        box-sizing: border-box;
        min-width: 0;
        min-height: 0;
        border-radius: 30px;
        border: 1px solid rgba(109, 122, 119, 0.12);
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 248, 247, 0.9));
        box-shadow:
          inset 0 1px 0 rgba(255, 255, 255, 0.78),
          0 18px 34px rgba(17, 33, 30, 0.06);
        overflow: hidden;
      }

      a2ui-column#results-column {
        position: relative;
        flex: 0 0 clamp(360px, 44%, 560px);
        max-width: clamp(360px, 44%, 560px);
        height: var(--results-workspace-height);
        padding: 58px 18px 18px;
      }

      a2ui-column#results-column::before {
        content: "Available restaurants";
        position: absolute;
        top: 18px;
        left: 18px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(243, 243, 243, 0.92);
        box-shadow: inset 0 0 0 1px rgba(109, 122, 119, 0.12);
        color: var(--rf-muted);
        font-family: var(--font-mono);
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        z-index: 1;
      }

      a2ui-column#map-column {
        flex: 1 1 56%;
        max-width: none;
        position: sticky;
        top: 8px;
        align-self: flex-start;
        height: var(--results-workspace-height);
        padding: 18px;
      }

      a2ui-column#map-column a2ui-custom-map,
      a2ui-custom-map#map-view {
        height: 100%;
        min-height: 0;
        top: auto;
      }

      a2ui-list#item-list {
        height: 100%;
        min-height: 0;
        overflow-x: hidden;
        overflow-y: scroll;
        padding-right: 6px;
        scrollbar-gutter: stable;
        scrollbar-width: thin;
        scrollbar-color: rgba(0, 104, 93, 0.45) rgba(243, 243, 243, 0.96);
        overscroll-behavior: contain;
      }

      a2ui-card[data-restaurant-key] {
        overflow: visible;
      }

      a2ui-list#item-list::-webkit-scrollbar {
        width: 12px;
      }

      a2ui-list#item-list::-webkit-scrollbar-track {
        border-radius: 999px;
        background: rgba(243, 243, 243, 0.96);
        box-shadow: inset 0 0 0 1px rgba(109, 122, 119, 0.08);
      }

      a2ui-list#item-list::-webkit-scrollbar-thumb {
        border: 3px solid rgba(243, 243, 243, 0.96);
        border-radius: 999px;
        background: linear-gradient(180deg, rgba(0, 131, 118, 0.72), rgba(0, 104, 93, 0.92));
        min-height: 56px;
      }

      a2ui-list#item-list::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, rgba(0, 131, 118, 0.82), rgba(0, 104, 93, 1));
      }

      a2ui-list#item-list::-webkit-scrollbar-button {
        display: none;
        width: 0;
        height: 0;
      }

      a2ui-card#item-card-template {
        width: min(100%, 480px);
        --a2ui-card-background: transparent;
        --a2ui-card-border-radius: 0;
        --a2ui-card-box-shadow: none;
        --a2ui-card-border: none;
        --a2ui-card-padding: 0;
        --a2ui-card-overflow: visible;
      }

      a2ui-restaurant-card#restaurant-card {
        min-width: 0;
      }

      .mobile-pane-toggle {
        display: none;
      }

      .mobile-pane-toggle button {
        appearance: none;
        border: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 44px;
        padding: 10px 16px;
        border-radius: 999px;
        background: rgba(243, 243, 243, 0.88);
        color: var(--rf-muted);
        font-family: var(--font-copy);
        font-size: 0.88rem;
        font-weight: 700;
        cursor: pointer;
        box-shadow: inset 0 0 0 1px rgba(109, 122, 119, 0.12);
        transition: background 160ms ease, color 160ms ease, transform 160ms ease;
      }

      .mobile-pane-toggle button:hover {
        transform: translateY(-1px);
      }

      .mobile-pane-toggle button.is-active {
        background: linear-gradient(135deg, var(--rf-primary), var(--rf-primary-strong));
        color: var(--rf-primary-contrast);
        box-shadow: 0 12px 24px rgba(0, 107, 95, 0.18);
      }

      @media (max-width: 900px) {
        :host {
          --results-workspace-height: auto;
          gap: 14px;
        }

        .mobile-pane-toggle {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding: 6px;
          width: fit-content;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.88);
          box-shadow: inset 0 0 0 1px rgba(109, 122, 119, 0.12);
        }

        a2ui-row#results-row {
          --a2ui-row-wrap: nowrap;
          gap: 0;
          height: auto;
        }

        a2ui-column#results-column,
        a2ui-column#map-column {
          flex: 1 1 100%;
          max-width: 100%;
          width: 100%;
        }

        a2ui-column#results-column {
          height: min(68svh, 820px);
          padding: 54px 14px 14px;
        }

        a2ui-column#map-column {
          position: static;
          top: auto;
          height: min(68svh, 700px);
          padding: 14px;
        }

        a2ui-list#item-list {
          height: 100%;
          overflow-y: auto;
          padding-right: 0;
          scrollbar-width: auto;
        }

        a2ui-card#item-card-template {
          width: 100%;
        }

        a2ui-restaurant-card#restaurant-card {
          width: 100%;
        }

        :host([mobile-pane="list"]) a2ui-column#map-column {
          display: none;
        }

        :host([mobile-pane="map"]) a2ui-column#results-column {
          display: none;
        }
      }
    `,
  ];

  #renderLogo() {
    if (!this.surface?.styles.logoUrl) {
      return nothing;
    }

    return html`<div id="surface-logo">
      <img src=${this.surface.styles.logoUrl} />
    </div>`;
  }

  @property()
  accessor enableCustomElements = false;

  protected willUpdate(changedProperties: PropertyValues<this>) {
    super.willUpdate(changedProperties);

    if (changedProperties.has("surface") || changedProperties.has("surfaceId")) {
      this.#showMobilePaneToggle = this.#isRestaurantResultsSurface();
      if (this.mobilePane !== "list") {
        this.mobilePane = "list";
      }
    }
  }

  updated(changedProperties: PropertyValues<this>) {
    super.updated(changedProperties);

    if (changedProperties.has("mobilePane") && this.mobilePane === "map") {
      this.#scheduleMapResize();
    }
  }

  showListPane() {
    if (!this.#showMobilePaneToggle) {
      return;
    }
    this.mobilePane = "list";
  }

  showMapPane() {
    if (!this.#showMobilePaneToggle) {
      return;
    }
    this.mobilePane = "map";
    this.#scheduleMapResize();
  }

  #isRestaurantResultsSurface() {
    const componentMap = this.surface?.components;
    if (!componentMap) {
      return false;
    }

    return (
      componentMap.has("results-row") &&
      componentMap.has("results-column") &&
      componentMap.has("map-column") &&
      componentMap.has("item-list") &&
      componentMap.has("map-view")
    );
  }

  #scheduleMapResize() {
    requestAnimationFrame(() => {
      const mapElement = this.renderRoot.querySelector("a2ui-custom-map") as
        | { resizeMap?: () => void }
        | null;
      mapElement?.resizeMap?.();
    });
  }

  #renderMobilePaneToggle() {
    if (!this.#showMobilePaneToggle) {
      return nothing;
    }

    return html`<div class="mobile-pane-toggle" aria-label="Choose result pane">
      <button
        class=${this.mobilePane === "list" ? "is-active" : ""}
        aria-pressed=${this.mobilePane === "list"}
        @click=${() => {
          this.showListPane();
        }}
      >
        List
      </button>
      <button
        class=${this.mobilePane === "map" ? "is-active" : ""}
        aria-pressed=${this.mobilePane === "map"}
        @click=${() => {
          this.showMapPane();
        }}
      >
        Map
      </button>
    </div>`;
  }


  #renderSurface() {
    const styles: Record<string, string> = {};
    if (this.surface?.styles) {
      for (const [key, value] of Object.entries(this.surface.styles)) {
        switch (key) {
          // Here we generate a palette from the singular primary color received
          // from the surface data. We will want the values to range from
          // 0 <= x <= 100, where 0 = back, 100 = white, and 50 = the primary
          // color itself. As such we use a color-mix to create the intermediate
          // values.
          //
          // Note: since we use half the range for black to the primary color,
          // and half the range for primary color to white the mixed values have
          // to go up double the amount, i.e., a range from black to primary
          // color needs to fit in 0 -> 50 rather than 0 -> 100.
          case "primaryColor": {
            styles["--p-100"] = "#ffffff";
            styles["--p-99"] = `color-mix(in srgb, ${value} 2%, white 98%)`;
            styles["--p-98"] = `color-mix(in srgb, ${value} 4%, white 96%)`;
            styles["--p-95"] = `color-mix(in srgb, ${value} 10%, white 90%)`;
            styles["--p-90"] = `color-mix(in srgb, ${value} 20%, white 80%)`;
            styles["--p-80"] = `color-mix(in srgb, ${value} 40%, white 60%)`;
            styles["--p-70"] = `color-mix(in srgb, ${value} 60%, white 40%)`;
            styles["--p-60"] = `color-mix(in srgb, ${value} 80%, white 20%)`;
            styles["--p-50"] = value;
            styles["--p-40"] = `color-mix(in srgb, ${value} 80%, black 20%)`;
            styles["--p-35"] = `color-mix(in srgb, ${value} 70%, black 30%)`;
            styles["--p-30"] = `color-mix(in srgb, ${value} 60%, black 40%)`;
            styles["--p-25"] = `color-mix(in srgb, ${value} 50%, black 50%)`;
            styles["--p-20"] = `color-mix(in srgb, ${value} 40%, black 60%)`;
            styles["--p-15"] = `color-mix(in srgb, ${value} 30%, black 70%)`;
            styles["--p-10"] = `color-mix(in srgb, ${value} 20%, black 80%)`;
            styles["--p-5"] = `color-mix(in srgb, ${value} 10%, black 90%)`;
            styles["--0"] = "#00000";
            break;
          }

          case "font": {
            styles["--font-family"] = value;
            styles["--font-family-flex"] = value;
            break;
          }
        }
      }
    }

    return html`<a2ui-root
      style=${styleMap(styles)}
      .surfaceId=${this.surfaceId}
      .processor=${this.processor}
      .childComponents=${this.surface?.componentTree
        ? [this.surface.componentTree]
        : null}
      .enableCustomElements=${this.enableCustomElements}
    ></a2ui-root>`;
  }

  render() {
    if (!this.surface) {
      return nothing;
    }

    return html`${[this.#renderLogo(), this.#renderMobilePaneToggle(), this.#renderSurface()]}`;
  }
}
