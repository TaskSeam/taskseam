# Contributing to TaskSeam

TaskSeam is in early development. Bug reports, concrete handoff examples, documentation improvements, and focused pull requests are welcome.

## Development

Requires Python 3.9 or newer and has no runtime dependencies.

```bash
git clone https://github.com/TaskSeam/taskseam.git
cd taskseam
python3 -m unittest discover -s tests -v
```

Please keep changes small, add tests for behavior that can fail, and run the full test suite before opening a pull request. Do not include real conversations, secrets, or proprietary source code in fixtures.

## Scope

The current milestone covers local project state, explicit state changes, provenance, per-agent continuation, an authenticated localhost API, and MCP read/write tools. Discuss broad architecture changes in an issue before implementing them.
