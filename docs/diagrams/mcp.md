# Mcp

```mermaid
flowchart LR
    U[User] --> C[Local MCP client]
    C --> S[Stdio MCP server]
    S --> O[OpenRepro core]
    O --> F[Bounded local research files]
    U -.-> G[ChatGPT hosted integration unverified]
```
