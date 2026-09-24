# TaskSeam Capture browser extension

This unpacked Manifest V3 extension captures a TaskSeam JSON packet from the latest ChatGPT or Claude response. It always shows an editable review before writing to the active local workspace.

## Local development

1. In the target project, run `taskseam serve` and copy the displayed pairing token.
2. Open `chrome://extensions`, enable Developer mode, and select **Load unpacked**.
3. Choose this `browser-extension` directory.
4. Ask ChatGPT or Claude for a packet using the output of `taskseam prompt`.
5. Open TaskSeam Capture, enter the token, read the latest response, review it, and save.

No conversation is captured until the user opens the extension and selects **Read latest AI response**. Only approved items are written, while the full selected assistant response is retained locally as source evidence.
