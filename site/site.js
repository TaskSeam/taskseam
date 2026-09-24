const copyButton = document.querySelector("#copy");
copyButton.addEventListener("click", async () => {
  const command = document.querySelector(".install code").textContent;
  await navigator.clipboard.writeText(command);
  copyButton.textContent = "Copied";
  window.setTimeout(() => { copyButton.textContent = "Copy"; }, 1600);
});
