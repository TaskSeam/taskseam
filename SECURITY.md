# Security Policy

## Supported versions

TaskSeam is currently alpha software. Security fixes are applied to the latest release.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for this repository. Do not open a public issue for a vulnerability or include private conversation data, credentials, or source code in a report.

## Current security boundary

TaskSeam stores data in a local SQLite database. The HTTP service accepts only localhost bind addresses. Workspace API access uses a random bearer token stored in the private `.taskseam/config.json` file; health information remains unauthenticated. Browser CORS access is limited to extension origins. Do not expose the service or token through a proxy, tunnel, container port, public network, screenshot, or bug report. The MCP server exposes context tools over standard input and output. Its continuation tool updates only the local per-target delivery checkpoint after returning a delta.

TaskSeam does not currently encrypt its database. Protect it with your operating system account and disk encryption, and do not record secrets in the alpha release.
