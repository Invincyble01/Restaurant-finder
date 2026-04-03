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
import { customElement, property, query, state } from "lit/decorators.js";
import { componentRegistry, Root } from "@a2ui/lit/ui";

type ReservationStep = "form" | "confirmation";
type StringBinding = string | { literalString?: string; path?: string } | null;
type PrimitiveDataValue = string | number | boolean | null;

interface ReservationConfirmation {
  guestName: string;
  guestCount: number;
  reservationDateTime: string;
}

interface TimeOption {
  value: string;
  label: string;
}

const SESSION_RESERVATIONS = new Map<string, ReservationConfirmation>();
const VIEW_RESERVATION_LABEL = "View reservation";
const QUARTER_HOUR_OPTIONS: TimeOption[] = Array.from({ length: 96 }, (_, index) => {
  const hour = Math.floor(index / 4);
  const minute = (index % 4) * 15;
  const hourString = String(hour).padStart(2, "0");
  const minuteString = String(minute).padStart(2, "0");
  const displayHour = hour % 12 === 0 ? 12 : hour % 12;
  const meridiem = hour < 12 ? "AM" : "PM";
  return {
    value: `${hourString}:${minuteString}`,
    label: `${displayHour}:${minuteString} ${meridiem}`,
  };
});

@customElement("a2ui-reservation-dialog")
export class A2uiReservationDialog extends Root {
  @property({ attribute: false })
  accessor triggerLabel: StringBinding = null;

  @property({ attribute: false })
  accessor restaurantName: StringBinding = null;

  @property({ attribute: false })
  accessor restaurantImageUrl: StringBinding = null;

  @property({ attribute: false })
  accessor restaurantAddress: StringBinding = null;

  @state()
  accessor #step: ReservationStep = "form";

  @state()
  accessor #name = "";

  @state()
  accessor #guestCount = "2";

  @state()
  accessor #reservationDate = "";

  @state()
  accessor #reservationTime = "";

  @state()
  accessor #errors: { name?: string; guestCount?: string; dateTime?: string } = {};

  @state()
  accessor #confirmation: ReservationConfirmation | null = null;

  @query("dialog")
  accessor #dialogRef: HTMLDialogElement | null = null;

  static styles = [
    css`
      :host {
        display: block;
        flex: var(--weight);
      }

      button {
        font: inherit;
      }

      .trigger {
        appearance: none;
        border: 0;
        border-radius: 999px;
        padding: 0.7rem 1.1rem;
        background: linear-gradient(135deg, var(--rf-primary), var(--rf-primary-strong));
        color: var(--rf-primary-contrast);
        font-size: 0.82rem;
        font-weight: 700;
        cursor: pointer;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        transition: transform 120ms ease, box-shadow 140ms ease, opacity 140ms ease;
        box-shadow: 0 16px 34px rgba(0, 107, 95, 0.18);
      }

      .trigger:hover {
        transform: translateY(-1px);
        box-shadow: 0 20px 38px rgba(0, 107, 95, 0.22);
      }

      .trigger:active {
        transform: translateY(0);
      }

       .trigger-booked {
        background: rgba(243, 243, 243, 0.92);
        color: var(--rf-primary);
        box-shadow: inset 0 0 0 1px rgba(0, 104, 93, 0.16);
      }

      dialog {
        border: 0;
        padding: 0;
        background: transparent;
      }

      dialog::backdrop {
        background: rgba(24, 28, 28, 0.24);
        backdrop-filter: blur(10px);
      }

      .panel {
        width: min(760px, calc(100vw - 2rem));
        max-height: calc(100vh - 2rem);
        overflow: auto;
        border-radius: 30px;
        border: 1px solid rgba(255, 255, 255, 0.8);
        background:
          radial-gradient(circle at top right, rgba(134, 246, 228, 0.22), transparent 0 28%),
          linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 248, 247, 0.96));
        box-shadow: 0 40px 80px rgba(0, 107, 95, 0.14);
      }

      .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        padding: 1.25rem 1.25rem 0.5rem;
      }

      .header-copy {
        display: grid;
        gap: 6px;
      }

      .eyebrow {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--rf-tertiary);
      }

      .title {
        margin: 0;
        color: var(--rf-ink);
        font-family: var(--font-display);
        font-size: 1.4rem;
        line-height: 1.05;
        letter-spacing: -0.03em;
        font-weight: 800;
      }

      .restaurant {
        margin: 0;
        color: var(--rf-ink-muted);
        font-size: 0.95rem;
        line-height: 1.5;
      }

      .close {
        appearance: none;
        border: 0;
        background: rgba(243, 243, 243, 0.92);
        color: var(--rf-muted);
        font-size: 1rem;
        line-height: 1;
        cursor: pointer;
        border-radius: 999px;
        width: 38px;
        height: 38px;
        box-shadow: inset 0 0 0 1px rgba(109, 122, 119, 0.1);
      }

      .close:hover {
        background: rgba(228, 226, 225, 0.92);
      }

      .content {
        padding: 0.75rem 1.25rem 1.25rem;
      }

      .reservation-shell,
      .confirmation-shell {
        display: grid;
        grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
        gap: 18px;
      }

      .hero-card,
      .form-card,
      .confirmation-card {
        border-radius: 26px;
        background: rgba(243, 243, 243, 0.9);
      }

      .hero-card {
        display: grid;
        overflow: hidden;
      }

      .hero-image-wrap {
        position: relative;
        min-height: 100%;
        background: linear-gradient(180deg, rgba(134, 246, 228, 0.18), rgba(0, 104, 93, 0.08));
      }

      .hero-image-wrap img {
        display: block;
        width: 100%;
        height: 100%;
        min-height: 280px;
        object-fit: cover;
      }

      .hero-fallback {
        display: grid;
        min-height: 280px;
        place-items: center;
        padding: 24px;
        color: var(--rf-muted);
        font-family: var(--font-display);
        font-size: 1.15rem;
        text-align: center;
      }

      .hero-overlay {
        position: absolute;
        inset: auto 0 0 0;
        padding: 20px;
        background: linear-gradient(180deg, transparent, rgba(26, 28, 28, 0.72));
        color: #ffffff;
        display: grid;
        gap: 8px;
      }

      .hero-label {
        font-family: var(--font-mono);
        font-size: 0.68rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        opacity: 0.8;
      }

      .hero-name {
        margin: 0;
        font-family: var(--font-display);
        font-size: 1.35rem;
        line-height: 1.08;
        letter-spacing: -0.03em;
        font-weight: 700;
      }

      .hero-address {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.86rem;
        line-height: 1.4;
        opacity: 0.92;
      }

      .form-card,
      .confirmation-card {
        padding: 22px;
      }

      .form-grid {
        display: grid;
        gap: 14px;
      }

      .input-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }

      label {
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
        color: var(--rf-ink-muted);
        font-size: 0.86rem;
        font-weight: 600;
      }

      .field-label {
        font-family: var(--font-mono);
        font-size: 0.68rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--rf-muted);
      }

      input,
      select {
        appearance: none;
        border: 1px solid rgba(109, 122, 119, 0.18);
        border-radius: 16px;
        padding: 0.85rem 0.9rem;
        font: inherit;
        font-size: 0.95rem;
        color: var(--rf-ink);
        background: rgba(255, 255, 255, 0.82);
      }

      input:focus,
      select:focus {
        outline: none;
        border-color: rgba(0, 104, 93, 0.34);
        box-shadow: 0 0 0 4px rgba(134, 246, 228, 0.34);
      }

      .error {
        color: var(--e-30);
        font-size: 0.78rem;
        font-weight: 500;
      }

      .actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.75rem;
        margin-top: 0.5rem;
        flex-wrap: wrap;
      }

      .secondary,
      .primary {
        appearance: none;
        border-radius: 18px;
        border: 1px solid transparent;
        padding: 0.85rem 1.1rem;
        font-size: 0.88rem;
        font-weight: 700;
        cursor: pointer;
      }

      .secondary {
        background: rgba(255, 255, 255, 0.82);
        color: var(--rf-ink);
        border-color: rgba(109, 122, 119, 0.14);
      }

      .secondary:hover {
        background: #ffffff;
      }

      .primary {
        background: linear-gradient(135deg, var(--rf-primary), var(--rf-primary-strong));
        color: var(--rf-primary-contrast);
        box-shadow: 0 18px 34px rgba(0, 107, 95, 0.16);
      }

      .primary:hover {
        opacity: 0.95;
      }

      .form-copy {
        display: grid;
        gap: 8px;
        margin-bottom: 4px;
      }

      .form-copy h4,
      .confirmation-card h4 {
        margin: 0;
        font-family: var(--font-display);
        font-size: 1.1rem;
        line-height: 1.08;
        letter-spacing: -0.02em;
        color: var(--rf-ink);
      }

      .form-copy p,
      .confirmation-card p {
        margin: 0;
        color: var(--rf-ink-muted);
        line-height: 1.55;
        font-size: 0.9rem;
      }

      .confirmation-shell {
        align-items: start;
      }

      .confirmation-card {
        display: grid;
        gap: 18px;
      }

      .detail-list {
        display: grid;
        gap: 10px;
        margin: 0;
      }

      .detail {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
        border-radius: 16px;
        padding: 12px 14px;
        background: rgba(255, 255, 255, 0.74);
        color: var(--rf-ink);
        font-size: 0.9rem;
      }

      .detail span:first-child {
        color: var(--rf-muted);
        font-family: var(--font-mono);
        font-size: 0.68rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }

      .detail span:last-child {
        text-align: right;
        line-height: 1.45;
      }

      .confirmation-badge {
        display: inline-flex;
        width: fit-content;
        align-items: center;
        justify-content: center;
        padding: 10px 14px;
        border-radius: 999px;
        background: rgba(134, 246, 228, 0.34);
        color: #005048;
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }

      .success {
        margin: 0;
        color: #005048;
        font-weight: 600;
        font-size: 0.9rem;
        line-height: 1.55;
      }

      @media (max-width: 640px) {
        .panel {
          border-radius: 22px;
        }

        .reservation-shell,
        .confirmation-shell,
        .input-grid {
          grid-template-columns: 1fr;
        }

        .hero-image-wrap img,
        .hero-fallback {
          min-height: 220px;
        }

        .content {
          padding: 0.65rem 0.9rem 0.9rem;
        }

        .header {
          padding: 0.9rem 0.9rem 0.35rem;
        }

        .form-card,
        .confirmation-card {
          padding: 18px;
        }

        .actions {
          flex-direction: column-reverse;
        }

        .primary,
        .secondary {
          width: 100%;
        }

        .detail {
          flex-direction: column;
          align-items: flex-start;
        }

        .detail span:last-child {
          text-align: left;
        }
      }
    `,
  ];

  render() {
    const hasSavedReservation = this.#hasSavedReservation();

    return html`
      <button class=${hasSavedReservation ? "trigger trigger-booked" : "trigger"} @click=${this.#openDialog}>
        ${this.#displayTriggerLabel()}
      </button>
      <dialog @cancel=${this.#onCancel}>
        <article class="panel">
          ${this.#step === "form" ? this.#renderForm() : this.#renderConfirmation()}
        </article>
      </dialog>
    `;
  }

  #renderForm() {
    const restaurantName = this.#displayRestaurantName();
    const restaurantImageUrl = this.#displayRestaurantImageUrl();
    const restaurantAddress = this.#displayRestaurantAddress();
    const availableTimeOptions = this.#timeOptionsForDate(this.#reservationDate);
    const minimumDate = this.#todayDateString();

    return html`
      <section class="header">
        <div class="header-copy">
          <span class="eyebrow">Reservation request</span>
          <h3 class="title">Reserve a table</h3>
          <p class="restaurant">${restaurantName}</p>
        </div>
        <button class="close" @click=${this.#closeDialog} aria-label="Close dialog">
          x
        </button>
      </section>
      <section class="content">
        <div class="reservation-shell">
          <section class="hero-card">
            <div class="hero-image-wrap">
              ${restaurantImageUrl
                ? html`<img src=${restaurantImageUrl} alt=${`Photo of ${restaurantName}`} />`
                : html`<div class="hero-fallback">${restaurantName}</div>`}
              <div class="hero-overlay">
                <span class="hero-label">Selected restaurant</span>
                <p class="hero-name">${restaurantName}</p>
                ${restaurantAddress
                  ? html`<span class="hero-address">${restaurantAddress}</span>`
                  : nothing}
              </div>
            </div>
          </section>

          <form class="form-card form-grid" @submit=${this.#onSubmit}>
            <div class="form-copy">
              <h4>Complete your reservation details</h4>
              <p>
                Confirm guest count, choose a future date and time, and we will hold this
                reservation locally for the current session.
              </p>
            </div>

            <label>
              <span class="field-label">Guest name</span>
              <input
                type="text"
                placeholder="Enter your name"
                .value=${this.#name}
                @input=${(evt: Event) => {
                  this.#onNameInput((evt.currentTarget as HTMLInputElement).value);
                }}
              />
              ${this.#errors.name
                ? html`<span class="error">${this.#errors.name}</span>`
                : nothing}
            </label>

            <div class="input-grid">
              <label>
                <span class="field-label">Guests</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  .value=${this.#guestCount}
                  @input=${(evt: Event) => {
                    this.#guestCount = (evt.currentTarget as HTMLInputElement).value;
                  }}
                />
                ${this.#errors.guestCount
                  ? html`<span class="error">${this.#errors.guestCount}</span>`
                  : nothing}
              </label>

              <label>
                <span class="field-label">Date</span>
                <input
                  type="date"
                  min=${minimumDate}
                  .value=${this.#reservationDate}
                  @input=${(evt: Event) => {
                    this.#onDateInput((evt.currentTarget as HTMLInputElement).value);
                  }}
                />
              </label>
            </div>

            <label>
              <span class="field-label">Time</span>
              <select
                .value=${this.#reservationTime}
                ?disabled=${!this.#reservationDate}
                @change=${(evt: Event) => {
                  this.#onTimeInput((evt.currentTarget as HTMLSelectElement).value);
                }}
              >
                <option value="">Select a time</option>
                ${availableTimeOptions.map(
                  (timeOption) => html`<option value=${timeOption.value}>${timeOption.label}</option>`
                )}
              </select>
              ${this.#errors.dateTime
                ? html`<span class="error">${this.#errors.dateTime}</span>`
                : nothing}
            </label>

            <div class="actions">
              <button type="button" class="secondary" @click=${this.#closeDialog}>
                Cancel
              </button>
              <button type="submit" class="primary">Confirm reservation</button>
            </div>
          </form>
        </div>
      </section>
    `;
  }

  #renderConfirmation() {
    const restaurantName = this.#displayRestaurantName();
    const restaurantImageUrl = this.#displayRestaurantImageUrl();
    const restaurantAddress = this.#displayRestaurantAddress();
    const confirmation = this.#confirmation ?? this.#getSavedReservation();
    const formattedDateTime = this.#formatDateTime(
      confirmation?.reservationDateTime ?? ""
    );

    return html`
      <section class="header">
        <div class="header-copy">
          <span class="eyebrow">Reservation confirmed</span>
          <h3 class="title">Reservation confirmed</h3>
          <p class="restaurant">${restaurantName}</p>
        </div>
        <button class="close" @click=${this.#closeDialog} aria-label="Close dialog">
          x
        </button>
      </section>

      <section class="content">
        <div class="confirmation-shell">
          <section class="hero-card">
            <div class="hero-image-wrap">
              ${restaurantImageUrl
                ? html`<img src=${restaurantImageUrl} alt=${`Photo of ${restaurantName}`} />`
                : html`<div class="hero-fallback">${restaurantName}</div>`}
              <div class="hero-overlay">
                <span class="hero-label">Booking locked in</span>
                <p class="hero-name">${restaurantName}</p>
                ${restaurantAddress
                  ? html`<span class="hero-address">${restaurantAddress}</span>`
                  : nothing}
              </div>
            </div>
          </section>

          <div class="confirmation-card">
            <span class="confirmation-badge">Session reservation saved</span>
            <div>
              <h4>Your table is confirmed</h4>
              <p>
                This reservation is available through the current session, and the trigger now opens
                the saved confirmation for this restaurant.
              </p>
            </div>
            <div class="detail-list">
              <p class="detail"><span>Guest name</span><span>${confirmation?.guestName}</span></p>
              <p class="detail"><span>Guests</span><span>${confirmation?.guestCount}</span></p>
              <p class="detail"><span>Date and time</span><span>${formattedDateTime}</span></p>
              ${restaurantAddress
                ? html`<p class="detail"><span>Address</span><span>${restaurantAddress}</span></p>`
                : nothing}
            </div>
            <p class="success">
              Your reservation at ${restaurantName} has been confirmed.
            </p>
            <div class="actions">
              <button type="button" class="primary" @click=${this.#closeDialog}>Done</button>
            </div>
          </div>
        </div>
      </section>
    `;
  }

  #openDialog = () => {
    this.#errors = {};
    const savedReservation = this.#getSavedReservation();
    if (savedReservation) {
      const parsedReservationDateTime = this.#parseReservationDateTime(
        savedReservation.reservationDateTime
      );
      this.#step = "confirmation";
      this.#confirmation = savedReservation;
      this.#name = savedReservation.guestName;
      this.#guestCount = String(savedReservation.guestCount);
      this.#reservationDate = parsedReservationDateTime?.date ?? "";
      this.#reservationTime = parsedReservationDateTime?.time ?? "";
    } else {
      this.#step = "form";
      this.#confirmation = null;
      this.#name = "";
      this.#guestCount = "2";
      this.#reservationDate = "";
      this.#reservationTime = "";
    }

    requestAnimationFrame(() => {
      if (this.#dialogRef && !this.#dialogRef.open) {
        this.#dialogRef.showModal();
      }
    });
  };

  #closeDialog = () => {
    if (this.#dialogRef?.open) {
      this.#dialogRef.close();
    }
  };

  #onCancel = (evt: Event) => {
    evt.preventDefault();
    this.#closeDialog();
  };

  #onSubmit = (evt: Event) => {
    evt.preventDefault();
    this.#errors = {};

    const errors: { name?: string; guestCount?: string; dateTime?: string } = {};
    const trimmedName = this.#name.trim();
    const numericGuestCount = Number.parseInt(this.#guestCount, 10);
    const reservationDateTime = this.#composeReservationDateTime();

    if (trimmedName.length < 3) {
      errors.name = "Name must be at least 3 characters.";
    }

    if (
      !Number.isInteger(numericGuestCount) ||
      Number.isNaN(numericGuestCount) ||
      numericGuestCount < 1
    ) {
      errors.guestCount = "Guests must be a whole number of at least 1.";
    }

    if (!reservationDateTime) {
      errors.dateTime = "Date and time is required.";
    } else {
      const parsedDateTime = new Date(reservationDateTime);
      if (Number.isNaN(parsedDateTime.getTime())) {
        errors.dateTime = "Date and time is invalid.";
      } else if (!this.#isSelectedTimeAllowed(this.#reservationDate, this.#reservationTime)) {
        errors.dateTime = "Please select a valid future 15-minute slot.";
      } else if (parsedDateTime.getTime() < this.#getMinimumDateTime().getTime()) {
        errors.dateTime = "Please select a future 15-minute slot.";
      }
    }

    const nameError = this.#nameValidationError(this.#name);
    if (nameError) {
      errors.name = nameError;
    }

    if (Object.keys(errors).length > 0) {
      this.#errors = errors;
      return;
    }

    const confirmation = {
      guestName: trimmedName,
      guestCount: numericGuestCount,
      reservationDateTime,
    };
    this.#confirmation = confirmation;
    SESSION_RESERVATIONS.set(this.#reservationKey(), confirmation);
    this.#step = "confirmation";
  };

  #displayTriggerLabel() {
    if (this.#hasSavedReservation()) {
      return VIEW_RESERVATION_LABEL;
    }
    return this.#resolveStringValue(this.triggerLabel) ?? "Book Now";
  }

  #displayRestaurantName() {
    return this.#resolveStringValue(this.restaurantName) ?? "Selected restaurant";
  }

  #displayRestaurantImageUrl() {
    return this.#resolveStringValue(this.restaurantImageUrl);
  }

  #displayRestaurantAddress() {
    return this.#resolveStringValue(this.restaurantAddress);
  }

  #resolveStringValue(value: StringBinding): string | null {
    if (value == null) {
      return null;
    }

    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
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
    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }
    const primitiveValue = value as PrimitiveDataValue;
    if (
      primitiveValue === null ||
      typeof primitiveValue === "string" ||
      typeof primitiveValue === "number" ||
      typeof primitiveValue === "boolean"
    ) {
      return primitiveValue === null ? null : String(primitiveValue);
    }
    return null;
  }

  #formatDateTime(rawValue: string) {
    if (!rawValue) {
      return "";
    }

    const parsed = new Date(rawValue);
    if (Number.isNaN(parsed.getTime())) {
      return rawValue;
    }

    return parsed.toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }

  #onNameInput(value: string) {
    this.#name = value;
    const nextErrors = { ...this.#errors };
    const nameError = this.#nameValidationError(value);
    if (nameError) {
      nextErrors.name = nameError;
    } else {
      delete nextErrors.name;
    }
    this.#errors = nextErrors;
  }

  #nameValidationError(value: string) {
    return value.trim().length < 3 ? "Name must be at least 3 characters." : undefined;
  }

  #onDateInput(value: string) {
    const today = this.#todayDateString();
    this.#reservationDate = value && value < today ? today : value;

    if (!this.#isSelectedTimeAllowed(this.#reservationDate, this.#reservationTime)) {
      this.#reservationTime = "";
    }
    this.#syncDateTimeError();
  }

  #onTimeInput(value: string) {
    this.#reservationTime = value;
    if (!this.#isSelectedTimeAllowed(this.#reservationDate, this.#reservationTime)) {
      const availableTimeOptions = this.#timeOptionsForDate(this.#reservationDate);
      this.#reservationTime = availableTimeOptions.length > 0 ? availableTimeOptions[0].value : "";
    }
    this.#syncDateTimeError();
  }

  #composeReservationDateTime() {
    if (!this.#reservationDate || !this.#reservationTime) {
      return "";
    }
    return `${this.#reservationDate}T${this.#reservationTime}`;
  }

  #parseReservationDateTime(rawValue: string): { date: string; time: string } | null {
    if (!rawValue) {
      return null;
    }

    const directMatch = rawValue.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/);
    if (directMatch) {
      return { date: directMatch[1], time: directMatch[2] };
    }

    const parsed = new Date(rawValue);
    if (Number.isNaN(parsed.getTime())) {
      return null;
    }

    return {
      date: this.#toLocalDateString(parsed),
      time: this.#toLocalTimeString(parsed),
    };
  }

  #getMinimumDateTime() {
    const current = new Date();
    current.setSeconds(0, 0);
    const minuteOffset = current.getMinutes() % 15;
    if (minuteOffset !== 0) {
      current.setMinutes(current.getMinutes() + (15 - minuteOffset));
    }
    return current;
  }

  #timeOptionsForDate(dateValue: string) {
    const minimumTimeValue = this.#minimumTimeValueForDate(dateValue);
    if (!minimumTimeValue) {
      return QUARTER_HOUR_OPTIONS;
    }
    return QUARTER_HOUR_OPTIONS.filter((timeOption) => timeOption.value >= minimumTimeValue);
  }

  #minimumTimeValueForDate(dateValue: string): string | null {
    if (!dateValue) {
      return null;
    }

    const today = this.#todayDateString();
    if (dateValue < today) {
      return "24:00";
    }
    if (dateValue > today) {
      return null;
    }

    return this.#toLocalTimeString(this.#getMinimumDateTime());
  }

  #isSelectedTimeAllowed(dateValue: string, timeValue: string) {
    if (!dateValue || !timeValue) {
      return false;
    }

    if (!QUARTER_HOUR_OPTIONS.some((timeOption) => timeOption.value === timeValue)) {
      return false;
    }

    const minimumTimeValue = this.#minimumTimeValueForDate(dateValue);
    if (!minimumTimeValue) {
      return true;
    }
    return timeValue >= minimumTimeValue;
  }

  #syncDateTimeError() {
    const nextErrors = { ...this.#errors };
    if (!this.#reservationDate || !this.#reservationTime) {
      nextErrors.dateTime = "Date and time is required.";
    } else if (!this.#isSelectedTimeAllowed(this.#reservationDate, this.#reservationTime)) {
      nextErrors.dateTime = "Please select a valid future 15-minute slot.";
    } else {
      delete nextErrors.dateTime;
    }
    this.#errors = nextErrors;
  }

  #hasSavedReservation() {
    return SESSION_RESERVATIONS.has(this.#reservationKey());
  }

  #getSavedReservation() {
    return SESSION_RESERVATIONS.get(this.#reservationKey()) ?? null;
  }

  #reservationKey() {
    const fallbackId = this.id?.trim().toLowerCase() || "unknown-restaurant";
    const restaurantName =
      this.#resolveStringValue(this.restaurantName)?.trim().toLowerCase() || fallbackId;
    const restaurantAddress =
      this.#resolveStringValue(this.restaurantAddress)?.trim().toLowerCase() || "no-address";
    const restaurantImage =
      this.#resolveStringValue(this.restaurantImageUrl)?.trim().toLowerCase() || "no-image";
    return `${restaurantName}::${restaurantAddress}::${restaurantImage}`;
  }

  #todayDateString() {
    return this.#toLocalDateString(new Date());
  }

  #toLocalDateString(value: Date) {
    const localMs = value.getTime() - value.getTimezoneOffset() * 60 * 1000;
    return new Date(localMs).toISOString().slice(0, 10);
  }

  #toLocalTimeString(value: Date) {
    const hour = String(value.getHours()).padStart(2, "0");
    const minute = String(value.getMinutes()).padStart(2, "0");
    return `${hour}:${minute}`;
  }
}

componentRegistry.register(
  "ReservationDialog",
  A2uiReservationDialog,
  "a2ui-reservation-dialog"
);

declare global {
  interface HTMLElementTagNameMap {
    "a2ui-reservation-dialog": A2uiReservationDialog;
  }
}
