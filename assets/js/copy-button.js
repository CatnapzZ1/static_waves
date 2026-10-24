// Enhance PaperMod's existing buttons after its footer has created them.
// Keep the native clipboard handler and translated success/reset messages.
document.querySelectorAll(".copy-code").forEach((button) => {
  const initialLabel = button.textContent.trim();
  button.type = "button";
  button.classList.add("copy-icon-button");
  const syncLabel = () => {
    const label = button.textContent.trim();
    button.setAttribute("aria-label", label);
    button.title = label;
    button.classList.toggle("is-copied", label !== initialLabel);
  };
  syncLabel();
  new MutationObserver(syncLabel).observe(button, {
    childList: true,
    characterData: true,
    subtree: true
  });
});
