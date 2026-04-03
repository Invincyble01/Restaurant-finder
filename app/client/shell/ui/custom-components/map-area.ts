/*
 A2UI custom Map component using MapLibre (via CDN in index.html).
 Expects a data model at `dataPath` that resolves to a map/object or array
 of items with at least: { lat: number, lng: number, name?: string, infoLink?: string }.
 Optional properties:
  - zoom: number (default 12)
  - height: string CSS size (default '480px')
  - latField/lngField/titleField/linkField: override field names (defaults shown above)

 This component registers itself under the type name 'Map' in the A2UI
 component registry so the server can emit a custom node with { type: 'Map' }.
 */
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { componentRegistry, Root } from "@a2ui/lit/ui";
import { v0_8 } from "@a2ui/lit";

// Declare the global provided by the MapLibre CDN script.
declare global {
  interface Window {
    maplibregl?: any;
  }
}

@customElement("a2ui-custom-map")
export class A2uiCustomMap extends Root {
  @property({ type: String })
  accessor dataPath: string = "/items";

  @property({ type: Number })
  accessor zoom: number = 12;

  @property({ type: String })
  accessor height: string = "480px";

  // Field names in each item
  @property({ type: String }) accessor latField: string = "lat";
  @property({ type: String }) accessor lngField: string = "lng";
  @property({ type: String }) accessor titleField: string = "name";
  @property({ type: String }) accessor linkField: string = "infoLink";
  @property({ type: String }) accessor ratingField: string = "rating";
  @property({ type: String }) accessor markerImageUrl: string =
    "https://maplibre.org/maplibre-gl-js/docs/assets/custom_marker.png";
  #mapLibreCssUrl = "https://unpkg.com/maplibre-gl@5.19.0/dist/maplibre-gl.css";

  // Use the shared processor passed down by a2ui-root via .processor

  static styles = [
    css`
      :host {
        display: block;
        flex: var(--weight);
        height: 100%;
        min-height: 0;
      }

      .map-shell {
        display: grid;
        grid-template-rows: auto 1fr auto;
        gap: 14px;
        height: 100%;
        min-height: 0;
      }

      .map-header,
      .map-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
      }

      .map-kicker {
        display: block;
        margin-bottom: 6px;
        font-family: var(--font-mono);
        font-size: 0.7rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--rf-tertiary);
      }

      .map-title {
        margin: 0;
        font-family: var(--font-display);
        font-size: 1.2rem;
        line-height: 1.05;
        letter-spacing: -0.03em;
        color: var(--rf-ink);
      }

      .map-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.72);
        box-shadow: inset 0 0 0 1px rgba(109, 122, 119, 0.12);
        color: var(--rf-muted);
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }

      #map {
        width: 100%;
        height: 100%;
        min-height: 420px;
        border-radius: 28px;
        overflow: hidden;
        position: relative;
        pointer-events: auto;
        box-shadow: 0 20px 40px rgba(0, 107, 95, 0.1);
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(255, 255, 255, 0.42)),
          rgba(243, 243, 243, 0.9);
      }

      #map::before {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        background:
          radial-gradient(circle at 12% 16%, rgba(134, 246, 228, 0.26), transparent 0 20%),
          radial-gradient(circle at 80% 20%, rgba(150, 241, 250, 0.16), transparent 0 16%);
        z-index: 0;
      }

      /* Tooltip-style popup inside the map container */
      .maplibregl-popup {
        position: absolute;
        top: 0;
        left: 0;
        display: flex;
        will-change: transform;
        max-width: 280px;
        font: 13px/1.5 var(--font-copy);
        z-index: 10;
        pointer-events: none;
      }
      .maplibregl-popup-anchor-top,
      .maplibregl-popup-anchor-top-left,
      .maplibregl-popup-anchor-top-right {
        flex-direction: column;
      }
      .maplibregl-popup-anchor-bottom,
      .maplibregl-popup-anchor-bottom-left,
      .maplibregl-popup-anchor-bottom-right {
        flex-direction: column-reverse;
      }
      .maplibregl-popup-anchor-left {
        flex-direction: row;
      }
      .maplibregl-popup-anchor-right {
        flex-direction: row-reverse;
      }
      .maplibregl-popup-content {
        position: relative;
        border-radius: 18px;
        box-shadow: 0 20px 34px rgba(0, 107, 95, 0.12);
        padding: 0;
        background: rgba(255, 255, 255, 0.96);
        pointer-events: auto;
        overflow: hidden;
      }
      .maplibregl-popup-content * {
        pointer-events: auto;
      }
      .maplibregl-popup-tip {
        width: 0;
        height: 0;
        border: 10px solid transparent;
        border-top-color: rgba(255, 255, 255, 0.96) !important;
      }
      .maplibregl-popup-anchor-top .maplibregl-popup-tip,
      .maplibregl-popup-anchor-top-left .maplibregl-popup-tip,
      .maplibregl-popup-anchor-top-right .maplibregl-popup-tip {
        align-self: center;
        border-top: none;
        border-bottom-color: rgba(255, 255, 255, 0.96);
      }
      .maplibregl-popup-anchor-bottom .maplibregl-popup-tip,
      .maplibregl-popup-anchor-bottom-left .maplibregl-popup-tip,
      .maplibregl-popup-anchor-bottom-right .maplibregl-popup-tip {
        align-self: center;
        border-bottom: none;
        border-top-color: rgba(255, 255, 255, 0.96);
      }
      .maplibregl-popup-anchor-left .maplibregl-popup-tip {
        align-self: center;
        border-left: none;
        border-right-color: rgba(255, 255, 255, 0.96);
      }
      .maplibregl-popup-anchor-right .maplibregl-popup-tip {
        align-self: center;
        border-right: none;
        border-left-color: rgba(255, 255, 255, 0.96);
      }

      .popup-card {
        display: grid;
        gap: 8px;
        padding: 14px 16px;
        min-width: 220px;
      }

      .popup-title {
        color: var(--rf-ink);
        font-family: var(--font-display);
        font-size: 1rem;
        line-height: 1.1;
        letter-spacing: -0.02em;
        font-weight: 700;
      }

      .popup-rating {
        color: var(--rf-ink-muted);
        font-size: 0.84rem;
      }

      .popup-link {
        display: inline-flex;
        width: fit-content;
        align-items: center;
        justify-content: center;
        padding: 8px 12px;
        border-radius: 999px;
        background: linear-gradient(135deg, var(--rf-primary), var(--rf-primary-strong));
        color: var(--rf-primary-contrast);
        text-decoration: none;
        font-size: 0.76rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .notice {
        font-size: 0.84rem;
        color: var(--rf-ink-muted);
        line-height: 1.5;
      }
      .fallback-list {
        margin-top: 8px;
        font-size: 0.9rem;
      }
      .fallback-list a {
        color: var(--rf-primary);
        text-decoration: underline;
      }

      @media (max-width: 900px) {
        #map {
          height: min(520px, var(--a2ui-map-height, 520px));
          min-height: 320px;
          border-radius: 22px;
        }
      }
    `,
  ];

  #map?: any;
  #container?: HTMLDivElement;
  #mapLoaded = false;
  #hasFitOnce = false;
  #popup?: any;
  #layerId?: string;
  #activePopupKey?: string;
  #skipNextMapClickClose = false;
  #popupContentEl?: HTMLElement;
  #onPopupContentClick = (ev: Event) => {
    ev.stopPropagation();
  };

  connectedCallback(): void {
    super.connectedCallback();
    this.style.setProperty("--a2ui-map-height", this.height);
  }

  firstUpdated(): void {
    this.#ensureMapLibreCssInShadowRoot();
    // Load MapLibre dynamically if not present, then initialize.
    if ((window as any).maplibregl) {
      this.#initMapIfPossible();
    } else {
      this.#loadMapLibre();
    }
  }

  updated(): void {
    // Update GeoJSON source when data changes.
    this.#updateSource();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this.#detachPopupClickGuard();
    this.#popup?.remove();
    this.#activePopupKey = undefined;
  }

  resizeMap() {
    if (!this.#map) {
      return;
    }

    this.#map.resize();
  }

  render() {
    const itemsCount = this.#getItems().filter((item) => this.#isFiniteCoord(item)).length;

    return html`
      <section class="map-shell">
        <div class="map-header">
          <div>
            <span class="map-kicker">Spatial view</span>
            <h3 class="map-title">Restaurant map</h3>
          </div>
          <span class="map-badge">${itemsCount} pins</span>
        </div>

        <div id="map"></div>

        <div class="map-footer">
          <span class="notice">Pins reflect the restaurants shown in the current results list.</span>
        </div>
      </section>
    `;
  }

  #initMapIfPossible() {
    if (this.#map || !window.maplibregl) return;
    const container = (this.renderRoot.querySelector("#map") ||
      document.createElement("div")) as HTMLDivElement;
    this.#container = container;

    // Derive center from first marker if available.
    const items = this.#getItems();
    const first = items.find((x) => this.#isFiniteCoord(x));
    const coord = first ? this.#getCoords(first) : null;
    const fallback = { lat: 30.2672, lng: -97.7431 }; // Austin, TX
    const use = coord ?? fallback;
    const center = [use.lng, use.lat];

    this.#map = new window.maplibregl.Map({
      container,
      style: "https://tiles.openfreemap.org/styles/bright",
      center,
      zoom: this.zoom,
      attributionControl: true,
    });

    // Add navigation controls
    this.#map.addControl(new window.maplibregl.NavigationControl(), "top-right");

    // Add symbol or circle layer with popup handlers when ready
    this.#map.on("load", async () => {
      // 1) Source
      if (!this.#map.getSource("restaurants")) {
        this.#map.addSource("restaurants", {
          type: "geojson",
          data: this.#buildGeoJSON(this.#getItems()),
          generateId: true,
        });
      }

      // 2) Try symbol layer with custom image, else circle layer fallback
      let useSymbol = false;
      try {
        const img = await this.#map.loadImage(this.markerImageUrl);
        if (!this.#map.hasImage("a2ui-marker")) {
          this.#map.addImage("a2ui-marker", img.data);
        }
        useSymbol = true;
      } catch (e) {
        console.warn("Marker image load failed; using circle layer.", e);
      }

      if (useSymbol) {
        if (!this.#map.getLayer("restaurants")) {
          this.#map.addLayer({
            id: "restaurants",
            type: "symbol",
            source: "restaurants",
            layout: {
              "icon-image": "a2ui-marker",
              "icon-anchor": "bottom",
              "icon-allow-overlap": true,
            },
          });
        }
        this.#layerId = "restaurants";
      } else {
        if (!this.#map.getLayer("restaurants-circles")) {
          this.#map.addLayer({
            id: "restaurants-circles",
            type: "circle",
            source: "restaurants",
            paint: {
              "circle-radius": 6,
              "circle-color": "#e91e63",
              "circle-stroke-color": "#fff",
              "circle-stroke-width": 2,
            },
          });
        }
        this.#layerId = "restaurants-circles";
      }

      // 3) Click-only popup handlers using resolved layer id
      const lid = this.#layerId!;
      this.#popup = new window.maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
      });

      this.#map.on("click", lid, (ev: any) => {
        this.#skipNextMapClickClose = true;
        window.setTimeout(() => {
          this.#skipNextMapClickClose = false;
        }, 0);
        const f = this.#pickClosestFeature(ev, lid);
        if (!f) return;
        const targetCoords = this.#getWrappedCoords(ev, f);
        if (!targetCoords) return;

        const p = f.properties || {};
        this.#notifyRestaurantPinSelected({
          restaurantKey: this.#toString(p.restaurantKey),
          restaurantName: this.#toString(p.title),
        });
        const html = this.#popupHtml({
          [this.titleField]: p.title,
          [this.ratingField]: p.rating,
          [this.linkField]: p.link,
        });
        if (!html) return;

        const popupKey = `${f.id ?? "noid"}|${targetCoords[0].toFixed(6)},${targetCoords[1].toFixed(6)}`;
        if (popupKey === this.#activePopupKey && this.#popup?.isOpen?.()) {
          this.#closePopup();
          return;
        }

        this.#map.getCanvas().style.cursor = "pointer";
        this.#popup.setLngLat(targetCoords).setHTML(html).addTo(this.#map);
        this.#activePopupKey = popupKey;
        this.#attachPopupClickGuard();
      });

      this.#map.on("click", (ev: any) => {
        if (this.#skipNextMapClickClose) {
          this.#skipNextMapClickClose = false;
          return;
        }
        const target = ev?.originalEvent?.target;
        if (
          this.#popupContentEl &&
          target instanceof Node &&
          this.#popupContentEl.contains(target)
        ) {
          return;
        }
        if (this.#hasLayerFeatureAtPoint(ev, lid)) return;
        this.#closePopup();
      });

      // 4) Finalize
      this.#mapLoaded = true;
      this.#map.resize();
      this.#updateSource();
    });
  }

  #loadMapLibre() {
    const d = document;
    const existing = d.getElementById("maplibre-script") as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener("load", () => this.#initMapIfPossible(), { once: true });
      return;
    }

    // CSS
    if (!d.getElementById("maplibre-css")) {
      const link = d.createElement("link");
      link.id = "maplibre-css";
      link.rel = "stylesheet";
      link.href = this.#mapLibreCssUrl;
      d.head.appendChild(link);
    }

    // Script
    const script = d.createElement("script");
    script.id = "maplibre-script";
    script.src = "https://unpkg.com/maplibre-gl@5.19.0/dist/maplibre-gl.js";
    script.onload = () => this.#initMapIfPossible();
    d.head.appendChild(script);
  }

  #ensureMapLibreCssInShadowRoot() {
    if (!(this.renderRoot instanceof ShadowRoot)) return;
    if (this.renderRoot.getElementById("maplibre-shadow-css")) return;
    const link = document.createElement("link");
    link.id = "maplibre-shadow-css";
    link.rel = "stylesheet";
    link.href = this.#mapLibreCssUrl;
    this.renderRoot.appendChild(link);
  }

  #updateSource() {
    if (!this.#map || !this.#mapLoaded) return;
    const src: any = this.#map.getSource("restaurants");
    const data = this.#buildGeoJSON(this.#getItems());
    if (src && typeof src.setData === "function") {
      src.setData(data);
    }
    // Fit all markers on first data load so all are visible regardless of center
    if (!this.#hasFitOnce) {
      this.#fitToData(data);
      this.#hasFitOnce = true;
    }
  }

  #buildGeoJSON(items: any[]) {
    const features = [] as any[];
    for (const it of items) {
      const c = this.#getCoords(it);
      if (!c) continue;
      features.push({
        type: "Feature",
        properties: {
          title: this.#toString(it[this.titleField]) || "",
          rating: this.#toString(it[this.ratingField]) || "",
          link: this.#toString(it[this.linkField]) || "",
          restaurantKey: this.#restaurantKeyForItem(it) || "",
        },
        geometry: { type: "Point", coordinates: [c.lng, c.lat] },
      });
    }
    return { type: "FeatureCollection", features };
  }

  #fitToData(fc: any) {
    if (!this.#map || !fc || !Array.isArray(fc.features)) return;
    const feats = fc.features;
    if (feats.length === 0) return;
    if (feats.length === 1) {
      const [lng, lat] = feats[0].geometry.coordinates;
      this.#map.setCenter([lng, lat]);
      return;
    }
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const f of feats) {
      const [x, y] = f.geometry.coordinates;
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    }
    const bounds = [[minX, minY], [maxX, maxY]] as any;
    try {
      this.#map.fitBounds(bounds, { padding: 60, maxZoom: Math.max(this.zoom, 12) });
    } catch {
      // ignore
    }
  }

  #closePopup() {
    this.#popup?.remove();
    this.#activePopupKey = undefined;
    this.#detachPopupClickGuard();
    if (this.#map) {
      this.#map.getCanvas().style.cursor = "";
    }
  }

  #detachPopupClickGuard() {
    if (!this.#popupContentEl) return;
    this.#popupContentEl.removeEventListener("click", this.#onPopupContentClick);
    this.#popupContentEl = undefined;
  }

  #attachPopupClickGuard() {
    if (!this.#popup) return;
    const popupEl = this.#popup.getElement?.();
    if (!(popupEl instanceof HTMLElement)) return;
    const contentEl = popupEl.querySelector(".maplibregl-popup-content");
    if (!(contentEl instanceof HTMLElement)) return;
    if (this.#popupContentEl === contentEl) return;

    this.#detachPopupClickGuard();
    contentEl.addEventListener("click", this.#onPopupContentClick);
    this.#popupContentEl = contentEl;
  }

  #hasLayerFeatureAtPoint(ev: any, layerId: string): boolean {
    if (!this.#map || !ev?.point) return false;
    try {
      const features = this.#map.queryRenderedFeatures(ev.point, { layers: [layerId] }) ?? [];
      return Array.isArray(features) && features.length > 0;
    } catch {
      return false;
    }
  }

  #getFeatureCoords(feature: any): [number, number] | null {
    if (!feature) return null;
    const coords = feature?.geometry?.coordinates;
    if (!Array.isArray(coords) || coords.length < 2) return null;
    const lng = Number(coords[0]);
    const lat = Number(coords[1]);
    if (!Number.isFinite(lng) || !Number.isFinite(lat)) return null;
    return [lng, lat];
  }

  #getWrappedCoords(ev: any, feature: any): [number, number] | null {
    const coords = this.#getFeatureCoords(feature);
    if (!coords) return null;
    const wrapped: [number, number] = [coords[0], coords[1]];
    while (Math.abs(ev?.lngLat?.lng - wrapped[0]) > 180) {
      wrapped[0] += ev.lngLat.lng > wrapped[0] ? 360 : -360;
    }
    return wrapped;
  }

  #pickClosestFeature(ev: any, layerId: string): any | null {
    if (!this.#map) return ev?.features?.[0] ?? null;
    let features: any[] = [];
    try {
      features = this.#map.queryRenderedFeatures(ev.point, { layers: [layerId] }) ?? [];
    } catch {
      return ev?.features?.[0] ?? null;
    }

    if (!Array.isArray(features) || features.length === 0) {
      return ev?.features?.[0] ?? null;
    }
    if (features.length === 1) {
      return features[0];
    }

    let closest: any | null = null;
    let closestDist = Number.POSITIVE_INFINITY;
    for (const feature of features) {
      const wrapped = this.#getWrappedCoords(ev, feature);
      if (!wrapped) continue;
      const p = this.#map.project(wrapped);
      const dx = p.x - ev.point.x;
      const dy = p.y - ev.point.y;
      const dist = dx * dx + dy * dy;
      if (dist < closestDist) {
        closestDist = dist;
        closest = feature;
      }
    }

    return closest ?? features[0];
  }

  #popupHtml(item: any): string | null {
    const title = this.#toString(item[this.titleField]);
    const link = this.#toString(item[this.linkField]);
    const rating = this.#toString(item[this.ratingField]);
    const safeTitle = title ? this.#escapeHtml(title) : "Location";
    const safeRating = rating
      ? `<div class=\"popup-rating\">${this.#escapeHtml(rating)}</div>`
      : "";
    const safeLink = link
      ? `<a class=\"popup-link\" target=\"_blank\" href=\"${this.#escapeAttr(link)}\">Open Link</a>`
      : "";
    return `
      <div class=\"popup-card\">
        <div class=\"popup-title\">${safeTitle}</div>
        ${safeRating}
        ${safeLink}
      </div>`;
  }

  #renderFallbackLinks() {
    const items = this.#getItems();
    if (!items.length) return nothing;
    const links = items
      .map((it) => {
        const t = this.#toString(it[this.titleField]) ?? "Location";
        const l = this.#toString(it[this.linkField]);
        return l ? html`<div class="fallback-list"><a target="_blank" href=${l}>${t}</a></div>` : nothing;
      })
      .filter(Boolean);
    return html`${links}`;
  }

  #notifyRestaurantPinSelected(detail: { restaurantKey: string | null; restaurantName: string | null }) {
    if (!detail.restaurantKey) {
      return;
    }

    this.dispatchEvent(
      new CustomEvent("restaurant-pin-selected", {
        detail: {
          surfaceId: this.surfaceId,
          restaurantKey: detail.restaurantKey,
          restaurantName: detail.restaurantName,
        },
        bubbles: true,
        composed: true,
      })
    );
  }

  #getItems(): any[] {
    // Pull items from the A2UI data model.
    const proc = this.processor || null;
    if (!proc || !this.surfaceId || !this.component) return [];
    const raw = proc.getData(this.component, this.dataPath, this.surfaceId) as any;
    if (!raw) return [];
    return this.#toArray(raw);
  }

  #toArray(val: any): any[] {
    if (Array.isArray(val)) return val.map((x) => this.#mapToPlain(x));
    if (val instanceof Map) return Array.from(val.values()).map((x) => this.#mapToPlain(x));
    if (typeof val === "object") return Object.values(val).map((x) => this.#mapToPlain(x));
    return [];
  }

  #mapToPlain(v: any): any {
    if (v instanceof Map) {
      const obj: any = {};
      for (const [k, val] of v.entries()) obj[k] = this.#mapToPlain(val);
      return obj;
    }
    if (Array.isArray(v)) return v.map((x) => this.#mapToPlain(x));
    return v;
  }

  #isFiniteCoord(item: any): boolean {
    const c = this.#getCoords(item);
    return !!c && Number.isFinite(c.lat) && Number.isFinite(c.lng);
  }

  #getCoords(item: any): { lat: number; lng: number } | null {
    if (!item) return null;
    const directLat = Number((item as any)?.[this.latField]);
    const directLng = Number((item as any)?.[this.lngField]);
    if (Number.isFinite(directLat) && Number.isFinite(directLng)) {
      return { lat: directLat, lng: directLng };
    }
    const loc =
      (item as any)?.location ||
      (item as any)?.coords ||
      (item as any)?.geo ||
      (item as any)?.geometry?.location;
    const nLat = Number((loc as any)?.lat ?? (loc as any)?.latitude);
    const nLng = Number(
      (loc as any)?.lng ?? (loc as any)?.lon ?? (loc as any)?.longitude
    );
    if (Number.isFinite(nLat) && Number.isFinite(nLng)) {
      return { lat: nLat, lng: nLng };
    }
    return null;
  }

  #toString(v: any): string | null {
    if (v == null) return null;
    return String(v);
  }

  #restaurantKeyForItem(item: any): string | null {
    const normalize = (value: unknown, fallback: string) => {
      const stringValue = this.#toString(value)?.trim().toLowerCase();
      return stringValue || fallback;
    };

    const name = this.#toString(item?.[this.titleField]);
    const address = this.#toString(item?.address);
    const imageUrl = this.#toString(item?.imageUrl);

    if (!name && !address && !imageUrl) {
      return null;
    }

    return `${normalize(name, "unknown-restaurant")}::${normalize(address, "no-address")}::${normalize(imageUrl, "no-image")}`;
  }

  #escapeHtml(s: string): string {
    return s.replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[c] as string));
  }

  #escapeAttr(s: string): string {
    return this.#escapeHtml(s);
  }
}

// Register component type 'Map' so A2UI can instantiate it via registry.
componentRegistry.register("Map", A2uiCustomMap);

declare global {
  interface HTMLElementTagNameMap {
    "a2ui-custom-map": A2uiCustomMap;
  }
}
