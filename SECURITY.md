# Security Policy

## Supported versions

TaskSeam is currently alpha software. Security fixes are applied to the latest release.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for this repository. Do not open a public issue for a vulnerability or include private conversation data, credentials, or source code in a report.

## Current security boundary

TaskSeam stores data in a local SQLite database. The HTTP service accepts only localhost bind addresses and does not provide authentication. Do not expose it through a proxy, tunnel, container port, or public network. The MCP server exposes read-only context tools over standard input and output.

TaskSeam does not currently encrypt its database. Protect it with your operating system account and disk encryption, and do not record secrets in the alpha release.
