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

import { AppConfig } from "./types.js";

export const config: AppConfig = {
  key: "restaurant",
  title: "Restaurant Finder",
  heroImage: "/hero.png",
  heroImageDark: "/hero-dark.png",
  background: `radial-gradient(circle at 12% 18%, rgba(134, 246, 228, 0.22), transparent 0 28%),
  radial-gradient(circle at 82% 14%, rgba(150, 241, 250, 0.2), transparent 0 22%),
  radial-gradient(circle at 78% 82%, rgba(0, 104, 93, 0.08), transparent 0 24%),
  linear-gradient(180deg, #fbfbfa 0%, #f4f3f0 100%)`,
  placeholder: "Top 5 Chinese restaurants in New York",
  loadingText: [
    "Mapping the dining scene...",
    "Reviewing ratings and atmosphere...",
    "Plotting restaurants on the map...",
    "Preparing reservation options...",
  ],
  serverUrl: "http://localhost:10002/agent",
};
