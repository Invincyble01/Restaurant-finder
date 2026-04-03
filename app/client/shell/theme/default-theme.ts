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

import { v0_8 } from "@a2ui/lit";

const link = {
  "typography-f-sf": true,
  "typography-fs-n": true,
  "typography-w-500": true,
  "layout-as-n": true,
  "layout-dis-iflx": true,
  "layout-al-c": true,
  "typography-td-none": true,
  "color-c-p40": true,
};

const body = {
  "typography-f-s": true,
  "typography-fs-n": true,
  "typography-w-400": true,
  "layout-m-0": true,
  "typography-sz-bm": true,
  "color-c-n10": true,
};

const heading = {
  "typography-f-sf": true,
  "typography-fs-n": true,
  "typography-w-500": true,
  "layout-m-0": true,
};

const input = {
  "typography-f-s": true,
  "typography-fs-n": true,
  "typography-w-400": true,
  "layout-pl-4": true,
  "layout-pr-4": true,
  "layout-pt-2": true,
  "layout-pb-2": true,
  "border-br-6": true,
  "border-bw-1": true,
  "border-bs-s": true,
  "color-c-n10": true,
};

const button = {
  "typography-f-s": true,
  "typography-fs-n": true,
  "typography-w-500": true,
  "layout-pt-2": true,
  "layout-pb-2": true,
  "layout-pl-4": true,
  "layout-pr-4": true,
  "border-br-12": true,
  "border-bw-0": true,
  "border-bs-s": true,
};

const aLight = v0_8.Styles.merge(link, {});
const bodyLight = v0_8.Styles.merge(body, {});
const buttonLight = v0_8.Styles.merge(button, {});
const headingLight = v0_8.Styles.merge(heading, {});
const inputLight = v0_8.Styles.merge(input, {});

export const theme: v0_8.Types.Theme = {
  additionalStyles: {
    Button: {
      background:
        "linear-gradient(135deg, var(--rf-primary) 0%, var(--rf-primary-strong) 100%)",
      color: "var(--rf-primary-contrast)",
      border: "none",
      minHeight: "46px",
      boxShadow: "0 18px 36px rgba(0, 104, 93, 0.16)",
      letterSpacing: "0.01em",
      cursor: "pointer",
    },
    Card: {
      background: "var(--rf-surface-elevated)",
      borderRadius: "28px",
      boxShadow: "0 22px 40px rgba(0, 107, 95, 0.08)",
      border: "1px solid rgba(109, 122, 119, 0.12)",
      overflow: "hidden",
      padding: "22px",
    },
    Column: {
      gap: "16px",
    },
    Row: {
      gap: "14px",
    },
    List: {
      gap: "24px",
      padding: "0",
    },
    Image: {
      background: "linear-gradient(180deg, rgba(0, 104, 93, 0.08), rgba(0, 104, 93, 0.02))",
      borderRadius: "24px",
      overflow: "hidden",
      aspectRatio: "16 / 10",
      minHeight: "220px",
    },
    Text: {
      h1: {
        color: "var(--rf-ink)",
        fontFamily: "var(--font-display)",
        fontSize: "clamp(2rem, 3vw, 3rem)",
        lineHeight: "1.02",
        letterSpacing: "-0.04em",
        fontWeight: "800",
      },
      h2: {
        color: "var(--rf-ink)",
        fontFamily: "var(--font-display)",
        fontSize: "1.55rem",
        lineHeight: "1.08",
        letterSpacing: "-0.03em",
        fontWeight: "750",
      },
      h3: {
        color: "var(--rf-ink)",
        fontFamily: "var(--font-display)",
        fontSize: "1.18rem",
        lineHeight: "1.15",
        letterSpacing: "-0.02em",
        fontWeight: "700",
      },
      h4: {
        color: "var(--rf-ink)",
        fontFamily: "var(--font-display)",
        fontSize: "1rem",
        lineHeight: "1.2",
        letterSpacing: "-0.01em",
        fontWeight: "700",
      },
      h5: {
        color: "var(--rf-ink-muted)",
        fontFamily: "var(--font-copy)",
        fontSize: "0.85rem",
        lineHeight: "1.45",
        fontWeight: "600",
        textTransform: "uppercase",
        letterSpacing: "0.12em",
      },
      body: {
        color: "var(--rf-ink-muted)",
        fontFamily: "var(--font-copy)",
        fontSize: "0.95rem",
        lineHeight: "1.55",
      },
      caption: {
        color: "var(--rf-muted)",
        fontFamily: "var(--font-mono)",
        fontSize: "0.75rem",
        lineHeight: "1.45",
        letterSpacing: "0.08em",
        textTransform: "uppercase",
      },
    },
    TextField: {
      background: "var(--rf-surface-subtle)",
      borderRadius: "16px",
      border: "1px solid rgba(109, 122, 119, 0.18)",
    },
    Modal: {
      boxShadow: "0 28px 60px rgba(0, 107, 95, 0.12)",
      borderRadius: "26px",
      border: "1px solid rgba(109, 122, 119, 0.14)",
      background: "var(--rf-surface-elevated)",
    },
  },
  components: {
    AudioPlayer: {},
    Button: {
      "layout-pt-2": true,
      "layout-pb-2": true,
      "layout-pl-4": true,
      "layout-pr-4": true,
      "border-br-12": true,
      "border-bw-0": true,
      "border-bs-s": true,
      "typography-w-500": true,
    },
    Card: {
      "border-br-9": true,
      "layout-p-4": true,
    },
    CheckBox: {
      element: {
        "layout-m-0": true,
        "layout-mr-2": true,
        "layout-p-2": true,
        "border-br-12": true,
        "border-bw-1": true,
        "border-bs-s": true,
      },
      label: {
        "typography-f-s": true,
        "typography-w-400": true,
        "layout-flx-1": true,
      },
      container: {
        "layout-dsp-iflex": true,
        "layout-al-c": true,
      },
    },
    Column: {
      "layout-g-3": true,
    },
    DateTimeInput: {
      container: {
        "typography-sz-bm": true,
        "layout-w-100": true,
        "layout-g-2": true,
        "layout-dsp-flexhor": true,
        "layout-al-c": true,
      },
      label: {
        "color-c-n40": true,
        "typography-sz-bm": true,
      },
      element: {
        "layout-pt-2": true,
        "layout-pb-2": true,
        "layout-pl-3": true,
        "layout-pr-3": true,
        "border-br-6": true,
        "border-bw-1": true,
        "border-bs-s": true,
      },
    },
    Divider: {},
    Image: {
      all: {
        "border-br-5": true,
        "layout-el-cv": true,
        "layout-w-100": true,
        "layout-h-100": true,
      },
      avatar: { "is-avatar": true },
      header: {},
      icon: {},
      largeFeature: {},
      mediumFeature: {},
      smallFeature: {},
    },
    Icon: {},
    List: {
      "layout-g-4": true,
      "layout-p-0": true,
    },
    Modal: {
      backdrop: { "color-bbgc-p60_20": true },
      element: {
        "border-br-5": true,
        "layout-p-4": true,
        "border-bw-1": true,
        "border-bs-s": true,
      },
    },
    MultipleChoice: {
      container: {},
      label: {},
      element: {},
    },
    Row: {
      "layout-g-4": true,
    },
    Slider: {
      container: {},
      label: {},
      element: {},
    },
    Tabs: {
      container: {},
      controls: { all: {}, selected: {} },
      element: {},
    },
    Text: {
      all: {
        "layout-w-100": true,
      },
      h1: {
        "typography-f-sf": true,
        "typography-w-500": true,
        "layout-m-0": true,
        "layout-p-0": true,
      },
      h2: {
        "typography-f-sf": true,
        "typography-w-500": true,
        "layout-m-0": true,
        "layout-p-0": true,
      },
      h3: {
        "typography-f-sf": true,
        "typography-w-500": true,
        "layout-m-0": true,
        "layout-p-0": true,
      },
      h4: {
        "typography-f-sf": true,
        "typography-w-500": true,
        "layout-m-0": true,
        "layout-p-0": true,
      },
      h5: {
        "typography-f-s": true,
        "typography-w-500": true,
        "layout-m-0": true,
        "layout-p-0": true,
      },
      body: {
        "layout-m-0": true,
        "layout-p-0": true,
      },
      caption: {
        "layout-m-0": true,
        "layout-p-0": true,
      },
    },
    TextField: {
      container: {
        "typography-sz-bm": true,
        "layout-w-100": true,
        "layout-g-2": true,
        "layout-dsp-flexhor": true,
        "layout-al-c": true,
      },
      label: {
        "layout-flx-0": true,
      },
      element: {
        "typography-sz-bm": true,
        "layout-pt-2": true,
        "layout-pb-2": true,
        "layout-pl-3": true,
        "layout-pr-3": true,
        "border-br-6": true,
        "border-bw-1": true,
        "border-bs-s": true,
      },
    },
    Video: {
      "border-br-5": true,
      "layout-el-cv": true,
    },
  },
  elements: {
    a: aLight,
    audio: {},
    body: bodyLight,
    button: buttonLight,
    h1: headingLight,
    h2: headingLight,
    h3: headingLight,
    h4: headingLight,
    h5: headingLight,
    iframe: {},
    input: inputLight,
    p: bodyLight,
    pre: bodyLight,
    textarea: inputLight,
    video: {},
  },
  markdown: {
    p: [...Object.keys(bodyLight)],
    h1: [...Object.keys(headingLight)],
    h2: [...Object.keys(headingLight)],
    h3: [...Object.keys(headingLight)],
    h4: [...Object.keys(headingLight)],
    h5: [...Object.keys(headingLight)],
    ul: [...Object.keys(bodyLight)],
    ol: [...Object.keys(bodyLight)],
    li: [...Object.keys(bodyLight)],
    a: [...Object.keys(aLight)],
    strong: [],
    em: [],
  },
};
