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

import { html, css, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { Root } from "./root.js";
import { classMap } from "lit/directives/class-map.js";
import { styleMap } from "lit/directives/style-map.js";
import { structuralStyles } from "./styles.js";

@customElement("a2ui-card")
export class Card extends Root {
  static styles = [
    structuralStyles,
    css`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        flex: var(--weight);
        min-height: 0;
        overflow: visible;
        scroll-margin-top: 24px;
      }

      section {
        display: flex;
        flex-direction: column;
        height: 100%;
        width: 100%;
        min-height: 0;
        overflow: hidden;
        box-sizing: border-box;

        ::slotted(*) {
          height: 100%;
          width: 100%;
        }
      }
    `,
  ];

  updated(): void {
    this.#syncRestaurantMetadata();
  }

  #syncRestaurantMetadata() {
    if (!this.processor || !this.component || !this.surfaceId) {
      return;
    }

    const restaurantName = this.#coerceString(this.processor.getData(this.component, "name", this.surfaceId));
    const restaurantAddress = this.#coerceString(this.processor.getData(this.component, "address", this.surfaceId));
    const restaurantImageUrl = this.#coerceString(this.processor.getData(this.component, "imageUrl", this.surfaceId));
    const restaurantKey = this.#restaurantKey(restaurantName, restaurantAddress, restaurantImageUrl);

    if (restaurantName) {
      this.setAttribute("data-restaurant-name", restaurantName);
    } else {
      this.removeAttribute("data-restaurant-name");
    }

    if (restaurantKey) {
      this.setAttribute("data-restaurant-key", restaurantKey);
    } else {
      this.removeAttribute("data-restaurant-key");
    }
  }

  #coerceString(value: unknown): string | null {
    if (value == null) {
      return null;
    }

    if (typeof value === "string") {
      const trimmed = value.trim();
      return trimmed ? trimmed : null;
    }

    if (typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }

    return null;
  }

  #restaurantKey(name: string | null, address: string | null, imageUrl: string | null): string | null {
    if (!name && !address && !imageUrl) {
      return null;
    }

    const normalize = (value: string | null, fallback: string) =>
      value?.trim().toLowerCase() || fallback;

    return `${normalize(name, "unknown-restaurant")}::${normalize(address, "no-address")}::${normalize(imageUrl, "no-image")}`;
  }

  render() {
    return html` <section
      class=${classMap(this.theme.components.Card)}
      style=${this.theme.additionalStyles?.Card
        ? styleMap(this.theme.additionalStyles?.Card)
        : nothing}
    >
      <slot></slot>
    </section>`;
  }
}
