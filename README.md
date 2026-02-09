## A2UI Learning repo

This core contains a lightweight version of the [official release of A2UI](https://github.com/google/A2UI) to demonstrate the minimal requirements.

Main objective is to make easier the understanding of A2UI protocol, conection using A2A and project overall structure. There are upcoming changes to demonstrate LIT framework capabilities of building UI with components. For now, restaurant demo remains almost the same as tutorial.

- Uses LIT for main client side UI render. Requires the `renderers` folder to work since the a2ui package renderer is not released yet.
    - [Renderers source original](https://github.com/google/A2UI/tree/main/renderers)
- Uses python + UV + a2a_agents folder since this final module is also not publised.
    - [a2a_agents folder original](https://github.com/google/A2UI/tree/main/a2a_agents)
    - For now server uses generic gemini API key, upcoming versions will use [langchain-oci from Oracle](https://github.com/oracle-samples/oci-openai).

Instructions on how to run client and server are in `app/client` and `app/server`. Optimized for Windows env, npm scripts may require Linux/MacOS adjustments.