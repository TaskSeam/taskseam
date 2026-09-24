function assistantMessages() {
  if (location.hostname === "chatgpt.com") {
    return [...document.querySelectorAll('[data-message-author-role="assistant"]')];
  }
  if (location.hostname === "claude.ai") {
    const turns = [...document.querySelectorAll('[data-testid="conversation-turn"]')];
    const assistantTurns = turns.filter((turn) =>
      !turn.querySelector('textarea, [contenteditable="true"]'));
    if (assistantTurns.length) return assistantTurns;
    return [...document.querySelectorAll('.font-claude-response')];
  }
  return [];
}

function packetFromText(text) {
  const candidates = [text];
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fenced) candidates.unshift(fenced[1]);
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start >= 0 && end > start) candidates.push(text.slice(start, end + 1));

  for (const candidate of candidates) {
    try {
      const packet = JSON.parse(candidate.trim());
      if (packet.version === 1 && Array.isArray(packet.items)) return packet;
    } catch (_) {
      // Continue to the next possible JSON region.
    }
  }
  throw new Error("The latest assistant response does not contain a TaskSeam packet.");
}

chrome.runtime.onMessage.addListener((message, _sender, respond) => {
  if (message.type !== "TASKSEAM_READ_LAST") return;
  try {
    const messages = assistantMessages();
    if (!messages.length) throw new Error("No assistant response was found on this page.");
    const evidence = messages[messages.length - 1].innerText.trim();
    respond({ok: true, packet: packetFromText(evidence), evidence,
             source: location.hostname === "claude.ai" ? "claude-web" : "chatgpt-web"});
  } catch (error) {
    respond({ok: false, error: error.message});
  }
});
