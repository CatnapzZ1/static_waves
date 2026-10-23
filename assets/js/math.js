document.addEventListener("DOMContentLoaded", () => {
  const article = document.querySelector(".post-content");
  if (!article) return;
  if (typeof renderMathInElement !== "function") {
    console.error("KaTeX 未加载；检查网络连接。");
    return;
  }
  renderMathInElement(article, {
    delimiters: [
      {left: "\\[", right: "\\]", display: true},
      {left: "$$", right: "$$", display: true},
      {left: "\\(", right: "\\)", display: false}
    ],
    throwOnError: false,
    trust: false
  });
});
