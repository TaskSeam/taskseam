# TaskSeam agent plugin

This plugin connects supported agents to the local TaskSeam MCP server and teaches them to:

- retrieve only task changes they have not received;
- use accepted decisions, constraints, and unresolved questions;
- record durable state after explicit user acceptance;
- preserve supersession, resolution, and source evidence.

Install the TaskSeam Python package first so the `taskseam` command is available. The plugin does not upload the local database.
