document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-apply").addEventListener("click", () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { action: "quick_apply" });
    });
  });

  document.getElementById("btn-tailor").addEventListener("click", () => {
    alert("📄 [JobHunt Pro] Generating ATS-optimized PDF resume...");
  });

  document.getElementById("btn-negotiate").addEventListener("click", () => {
    alert("💼 [JobHunt Pro] Opening AI Negotiator assistant...");
  });
});
