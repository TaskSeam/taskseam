# TaskSeam Privacy

Last updated: September 24, 2026

TaskSeam is local-first open-source software. This policy describes the TaskSeam command-line application, agent plugin, and developer-preview browser extension distributed from the TaskSeam repository.

## Data TaskSeam handles

TaskSeam can store task titles, accepted decisions, active constraints, unresolved questions, continuity state, source labels, and supporting evidence that a user chooses to save.

The browser extension can read the latest visible assistant response on a supported ChatGPT or Claude page after the user selects **Read latest AI response**. It presents detected project changes for review. Nothing is saved until the user selects **Save approved items**.

## Storage and transmission

- Task state and evidence are stored in the local project's `.taskseam/` directory.
- The browser pairing token is stored in the browser extension's local storage and the project's ignored `.taskseam/config.json` file.
- The browser extension sends approved data only to the TaskSeam service on `127.0.0.1`.
- TaskSeam does not operate an analytics, advertising, synchronization, or hosted storage service.
- TaskSeam does not sell personal data.

AI services still process conversations according to their own terms and privacy policies. TaskSeam does not control those services.

## Permissions

The developer-preview browser extension requests access to active ChatGPT and Claude tabs so it can read the latest assistant response after a user action. It requests access to the local TaskSeam bridge so it can check the active task and save reviewed items. It does not capture browsing history or run background conversation collection.

## User controls

Users can edit or exclude every browser-captured item before saving it. Users can stop the local bridge, disable or remove the extension, and delete the local `.taskseam/` directory to remove a project's TaskSeam data.

## Security reports and questions

Report vulnerabilities using GitHub private vulnerability reporting as described in [SECURITY.md](SECURITY.md). For privacy questions, open a GitHub discussion or issue without including private conversation content, credentials, pairing tokens, or source code that should remain confidential.
