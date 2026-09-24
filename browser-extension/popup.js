const API = "http://127.0.0.1:8765";
const tokenInput = document.querySelector("#token");
const status = document.querySelector("#status");
const review = document.querySelector("#review");
const itemsNode = document.querySelector("#items");
let capture = null;

chrome.storage.local.get(["taskseamToken"], ({taskseamToken}) => {
  if (taskseamToken) tokenInput.value = taskseamToken;
});

function message(text, kind = "") {
  status.textContent = text;
  status.className = kind;
}

async function api(path, options = {}) {
  const token = tokenInput.value.trim();
  if (!token) throw new Error("Enter the pairing token shown by taskseam serve.");
  const response = await fetch(API + path, {
    ...options,
    headers: {"Authorization": `Bearer ${token}`, "Content-Type": "application/json",
              ...(options.headers || {})}
  });
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || `TaskSeam returned ${response.status}`);
  await chrome.storage.local.set({taskseamToken: token});
  return value;
}

document.querySelector("#connect").addEventListener("click", async () => {
  try {
    const context = await api("/v1/active");
    message(`Connected to: ${context.task.title}`, "success");
  } catch (error) { message(error.message, "error"); }
});

document.querySelector("#read").addEventListener("click", async () => {
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    const result = await chrome.tabs.sendMessage(tab.id, {type: "TASKSEAM_READ_LAST"});
    if (!result?.ok) throw new Error(result?.error || "Could not read this page.");
    capture = result;
    itemsNode.replaceChildren();
    result.packet.items.forEach((item) => {
      if (!["decision", "constraint", "question"].includes(item.kind) || !item.body) return;
      const row = document.createElement("article");
      row.className = "item";
      row.innerHTML = `<header><input type="checkbox" checked aria-label="Include item"><select aria-label="Item kind"><option>decision</option><option>constraint</option><option>question</option></select></header><textarea aria-label="Item body"></textarea>`;
      row.querySelector("select").value = item.kind;
      row.querySelector("textarea").value = item.body;
      itemsNode.append(row);
    });
    if (!itemsNode.children.length) throw new Error("The packet contains no supported items.");
    review.hidden = false;
    message("Review every item before saving.");
  } catch (error) { message(error.message, "error"); }
});

document.querySelector("#save").addEventListener("click", async () => {
  try {
    const items = [...itemsNode.querySelectorAll(".item")]
      .filter((row) => row.querySelector('input[type="checkbox"]').checked)
      .map((row) => ({kind: row.querySelector("select").value,
                      body: row.querySelector("textarea").value.trim()}))
      .filter((item) => item.body);
    if (!items.length) throw new Error("Select at least one non-empty item.");
    const result = await api("/v1/active/import", {method: "POST", body: JSON.stringify({
      items, source: capture.source, evidence: capture.evidence
    })});
    review.hidden = true;
    message(`Saved ${result.item_ids.length} item(s) to TaskSeam.`, "success");
  } catch (error) { message(error.message, "error"); }
});
