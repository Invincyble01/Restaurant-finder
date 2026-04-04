# Lit Renderer README

For full repository setup from scratch, start with the root `README.md`.

This folder contains the Lit implementation of the A2UI renderer used by the client shell.

## Local Build

This package depends on the local `renderers/web_core` package.

Install dependencies:

```bash
npm install
```

Build the package:

```bash
npm run build
```

## Security Note

Important: The sample code provided is for demonstration purposes and illustrates the mechanics of A2UI and the Agent-to-Agent (A2A) protocol. When building production applications, it is critical to treat any agent operating outside of your direct control as a potentially untrusted entity.

All operational data received from an external agent - including its AgentCard, messages, artifacts, and task statuses - should be handled as untrusted input. For example, a malicious agent could provide crafted data in its fields (for example, `name` or `skills.description`) that, if used without sanitization to construct prompts for a large language model, could expose your application to prompt injection attacks.

Similarly, any UI definition or data stream received must be treated as untrusted. Malicious agents could attempt to spoof legitimate interfaces to deceive users, inject malicious scripts via property values, or generate excessive layout complexity to degrade client performance. If your application supports optional embedded content such as iframes or web views, additional care must be taken to prevent exposure to malicious external sites.

Developer responsibility: failure to properly validate data and strictly sandbox rendered content can introduce severe vulnerabilities. Developers are responsible for implementing appropriate security measures such as input sanitization, Content Security Policies (CSP), strict isolation for optional embedded content, and secure credential handling.
