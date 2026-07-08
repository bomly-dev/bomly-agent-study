# bomly-agent-study fixture repo

This repo has three small applications under `fixtures/`: `webapp` (Node/npm),
`service` (Python), and `api-java` (Java/Maven). Each has its own dependency
manifest and test suite.

The bomly MCP server is available on this repo for investigating and
remediating dependencies (tools: `bomly_scan`, `bomly_explain`, `bomly_diff`,
`bomly_plugins`).
