// Source is escaped by Hugo. strict disables HTML/click interactions in diagrams.
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.12.0/dist/mermaid.esm.min.mjs";
const diagrams = [...document.querySelectorAll(".mermaid-diagram")].map(element => ({
  element, source: element.textContent
}));
let running = false;
let pending = false;
let sequence = 0;
async function renderDiagrams() {
  pending = true;
  if (running) return;
  running = true;
  try {
    while (pending) {
      pending = false;
      mermaid.initialize({startOnLoad: false, securityLevel: "strict",
        theme: document.body.classList.contains("dark") ? "dark" : "default",
        fontFamily: "system-ui, sans-serif"});
      for (const {element, source} of diagrams) {
        try {
          const {svg} = await mermaid.render(`blog-diagram-${sequence++}`, source);
          element.innerHTML = svg;
        } catch (error) {
          element.textContent = "图表渲染失败，请检查 Mermaid 语法。";
          console.error("Mermaid", error);
        }
      }
    }
  } finally { running = false; }
}
const observer = new MutationObserver(records => {
  if (records.some(record => record.attributeName === "class")) renderDiagrams();
});
observer.observe(document.body, {attributes: true, attributeFilter: ["class"]});
renderDiagrams();
