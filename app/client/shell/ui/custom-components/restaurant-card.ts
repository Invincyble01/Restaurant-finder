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

import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { componentRegistry, Root } from "@a2ui/lit/ui";

type StringBinding = string | { literalString?: string; path?: string } | null;

interface RatingDisplay {
  score: string | null;
  detail: string | null;
}

@customElement("a2ui-restaurant-card")
export class A2uiRestaurantCard extends Root {
  @property({ attribute: false })
  accessor name: StringBinding = null;

  @property({ attribute: false })
  accessor detail: StringBinding = null;

  @property({ attribute: false })
  accessor rating: StringBinding = null;

  @property({ attribute: false })
  accessor tags: StringBinding = null;

  @property({ attribute: false })
  accessor address: StringBinding = null;

  @property({ attribute: false })
  accessor imageUrl: StringBinding = null;

  @property({ attribute: false })
  accessor infoLink: StringBinding = null;

  @property({ attribute: false })
  accessor infoLinkMarkdown: StringBinding = null;

  static styles = [
    css`
      :host {
        display: block;
        width: 100%;
      }

      * {
        box-sizing: border-box;
      }

      .card {
        display: grid;
        overflow: hidden;
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 20px 42px rgba(12, 76, 69, 0.1);
      }

      .media {
        position: relative;
        min-height: 270px;
        background:
          linear-gradient(180deg, rgba(0, 0, 0, 0.02), rgba(0, 0, 0, 0.14)),
          linear-gradient(135deg, rgba(0, 104, 93, 0.12), rgba(0, 104, 93, 0.04));
      }

      .media img {
        display: block;
        width: 100%;
        height: 270px;
        object-fit: cover;
      }

      .media-fallback {
        display: grid;
        min-height: 270px;
        place-items: center;
        padding: 24px;
        color: #5d6d69;
        font-family: var(--font-display);
        font-size: 1.1rem;
        text-align: center;
        background:
          radial-gradient(circle at 20% 18%, rgba(134, 246, 228, 0.28), transparent 0 18%),
          linear-gradient(145deg, rgba(0, 104, 93, 0.12), rgba(243, 243, 243, 0.9));
      }

      .rating-badge {
        position: absolute;
        top: 16px;
        right: 16px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        min-height: 40px;
        padding: 10px 14px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.94);
        color: #11211e;
        box-shadow: 0 12px 26px rgba(17, 33, 30, 0.12);
        backdrop-filter: blur(12px);
      }

      .rating-badge svg {
        width: 16px;
        height: 16px;
        fill: #ffb938;
        flex: 0 0 auto;
      }

      .rating-score {
        font-family: var(--font-copy);
        font-size: 0.9rem;
        font-weight: 700;
        line-height: 1;
        letter-spacing: -0.02em;
      }

      .body {
        display: grid;
        gap: 18px;
        padding: 22px 24px 20px;
      }

      .title-block {
        display: grid;
        gap: 10px;
      }

      .title-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 14px;
      }

      .title {
        margin: 0;
        color: #10211d;
        font-family: var(--font-display);
        font-size: 1.32rem;
        line-height: 1.05;
        letter-spacing: -0.03em;
        font-weight: 800;
        flex: 1 1 auto;
        min-width: 0;
      }

      .rating-count {
        flex: 0 0 auto;
        color: #6b7b77;
        font-family: var(--font-copy);
        font-size: 0.86rem;
        font-weight: 600;
        line-height: 1.3;
        white-space: nowrap;
      }

      .detail {
        margin: 0;
        color: #465754;
        font-family: var(--font-copy);
        font-size: 0.96rem;
        line-height: 1.55;
      }

      .tags {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .tag {
        display: inline-flex;
        align-items: center;
        min-height: 34px;
        padding: 8px 14px;
        border-radius: 999px;
        background: #f2f5f4;
        color: #49635d;
        font-family: var(--font-copy);
        font-size: 0.84rem;
        font-weight: 600;
        line-height: 1.2;
        letter-spacing: -0.01em;
      }

      .footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        padding: 18px 24px 22px;
        border-top: 1px solid #eceeed;
      }

      .footer-copy {
        display: grid;
        gap: 8px;
        min-width: 0;
      }

      .footer-meta {
        margin: 0;
        color: #6b7b77;
        font-family: var(--font-copy);
        font-size: 0.84rem;
        line-height: 1.45;
      }

      .site-link {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: #00685d;
        font-family: var(--font-copy);
        font-size: 0.95rem;
        font-weight: 700;
        line-height: 1.2;
        text-decoration: none;
      }

      .site-link:hover {
        color: #005248;
      }

      .site-link svg {
        width: 14px;
        height: 14px;
        flex: 0 0 auto;
        stroke: currentColor;
        stroke-width: 2;
        fill: none;
      }

      a2ui-reservation-dialog {
        flex: 0 0 auto;
      }

      @media (max-width: 640px) {
        .media,
        .media img,
        .media-fallback {
          min-height: 220px;
          height: 220px;
        }

        .body {
          padding: 20px 20px 18px;
        }

        .title-row {
          align-items: flex-start;
          flex-direction: column;
          gap: 6px;
        }

        .rating-count {
          white-space: normal;
        }

        .footer {
          align-items: stretch;
          flex-direction: column;
          padding: 18px 20px 20px;
        }

        a2ui-reservation-dialog {
          width: 100%;
        }
      }
    `,
  ];

  #resolveStringValue(value: StringBinding): string | null {
    if (value == null) {
      return null;
    }

    if (
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean"
    ) {
      return String(value);
    }

    if (typeof value === "object") {
      if ("literalString" in value && typeof value.literalString === "string") {
        return value.literalString;
      }

      if ("path" in value && typeof value.path === "string") {
        if (!this.processor || !this.component) {
          return null;
        }

        const resolved = this.processor.getData(
          this.component,
          value.path,
          this.surfaceId ?? "@default"
        );
        return this.#coerceString(resolved);
      }
    }

    return null;
  }

  #coerceString(value: unknown): string | null {
    if (value == null) {
      return null;
    }

    if (
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean"
    ) {
      const text = String(value).trim();
      return text ? text : null;
    }

    return null;
  }

  #splitTags(value: string | null) {
    if (!value) {
      return [];
    }

    return value
      .split("|")
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0)
      .slice(0, 2);
  }

  #extractLinkHref() {
    const directLink = this.#resolveStringValue(this.infoLink);
    if (directLink) {
      return directLink;
    }

    const markdownLink = this.#resolveStringValue(this.infoLinkMarkdown);
    if (!markdownLink) {
      return null;
    }

    const match = markdownLink.match(/^\[[^\]]+\]\((https?:\/\/[^)]+)\)$/);
    return match?.[1] ?? null;
  }

  #extractRating(rawRating: string | null): RatingDisplay {
    if (!rawRating) {
      return { score: null, detail: null };
    }

    const cleaned = rawRating.trim();
    if (!cleaned) {
      return { score: null, detail: null };
    }

    const parts = cleaned
      .split("|")
      .map((part) => part.trim())
      .filter((part) => part.length > 0);
    const scoreSource = parts[0] ?? cleaned;

    let score = /^\d+(?:\.\d+)?$/.test(scoreSource) ? scoreSource : null;
    if (!score && /\u2605/.test(scoreSource)) {
      const fullStars = (scoreSource.match(/\u2605/g) ?? []).length;
      if (fullStars > 0) {
        score = `${Math.min(fullStars, 5)}.0`;
      }
    }

    let detail: string | null = null;
    if (parts.length > 1) {
      detail = parts.slice(1).join(" / ");
    } else if (parts.length === 1 && parts[0] !== score && !/\u2605/.test(parts[0])) {
      detail = parts[0];
    }

    return { score, detail };
  }

  #joinMeta(...values: Array<string | null>) {
    return values.filter((value): value is string => Boolean(value)).join(" / ");
  }

  render() {
    const name = this.#resolveStringValue(this.name) ?? "Restaurant";
    const detail = this.#resolveStringValue(this.detail);
    const address = this.#resolveStringValue(this.address);
    const imageUrl = this.#resolveStringValue(this.imageUrl);
    const linkHref = this.#extractLinkHref();
    const rating = this.#extractRating(this.#resolveStringValue(this.rating));
    const tags = this.#splitTags(this.#resolveStringValue(this.tags));
    const footerMeta = this.#joinMeta(address);

    return html`
      <article class="card">
        <div class="media">
          ${imageUrl
            ? html`<img src=${imageUrl} alt=${name} />`
            : html`<div class="media-fallback">${name}</div>`}
          ${rating.score
            ? html`<div class="rating-badge" aria-label=${`Rated ${rating.score}`}>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 2.75l2.84 5.76 6.36.92-4.6 4.48 1.08 6.34L12 17.27l-5.68 2.98 1.08-6.34-4.6-4.48 6.36-.92L12 2.75z"></path>
                </svg>
                <span class="rating-score">${rating.score}</span>
              </div>`
            : nothing}
        </div>

        <div class="body">
          <div class="title-block">
            <div class="title-row">
              <h3 class="title">${name}</h3>
              ${rating.detail ? html`<span class="rating-count">${rating.detail}</span>` : nothing}
            </div>
            ${detail ? html`<p class="detail">${detail}</p>` : nothing}
          </div>

          ${tags.length
            ? html`<div class="tags">
                ${tags.map((tag) => html`<span class="tag">${tag}</span>`) }
              </div>`
            : nothing}
        </div>

        <div class="footer">
          <div class="footer-copy">
            ${footerMeta ? html`<p class="footer-meta">${footerMeta}</p>` : nothing}
            ${linkHref
              ? html`<a class="site-link" href=${linkHref} target="_blank" rel="noreferrer noopener">
                  <span>Visit site</span>
                  <svg viewBox="0 0 16 16" aria-hidden="true">
                    <path d="M3.5 12.5L12.5 3.5"></path>
                    <path d="M6 3.5h6.5V10"></path>
                  </svg>
                </a>`
              : nothing}
          </div>

          <a2ui-reservation-dialog
            .triggerLabel=${"Book Now"}
            .restaurantName=${name}
            .restaurantImageUrl=${imageUrl ?? ""}
            .restaurantAddress=${address ?? ""}
          ></a2ui-reservation-dialog>
        </div>
      </article>
    `;
  }
}

componentRegistry.register(
  "RestaurantCard",
  A2uiRestaurantCard,
  "a2ui-restaurant-card"
);

declare global {
  interface HTMLElementTagNameMap {
    "a2ui-restaurant-card": A2uiRestaurantCard;
  }
}
