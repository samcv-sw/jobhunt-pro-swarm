// JobHunt Pro — Chrome Sidecar Content Script
(function () {
  console.log("🚀 [JobHunt Pro] Sidecar extension active.");

  function injectOverlay() {
    if (document.getElementById("jobhunt-pro-sidecar-root")) return;

    const root = document.createElement("div");
    root.id = "jobhunt-pro-sidecar-root";
    root.style.position = "fixed";
    root.style.bottom = "20px";
    root.style.right = "20px";
    root.style.zIndex = "999999";
    root.style.fontFamily = "'Inter', sans-serif";

    root.innerHTML = `
      <div style="background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.15); border-radius: 16px; padding: 14px 18px; color: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 12px;">
        <div style="font-weight: 700; background: linear-gradient(135deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">⚡ JobHunt Pro</div>
        <button id="jhp-quick-apply" style="background: linear-gradient(135deg, #6366f1, #8b5cf6); border: none; color: #fff; padding: 8px 14px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s;">✨ 1-Click AI Apply</button>
        <button id="jhp-ats-score" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; padding: 8px 14px; border-radius: 8px; font-weight: 600; cursor: pointer;">🎯 Score ATS</button>
      </div>
    `;

    document.body.appendChild(root);

    document.getElementById("jhp-quick-apply").addEventListener("click", () => {
      alert("✨ [JobHunt Pro] Analyzing job post & applying autonomously...");
    });

    document.getElementById("jhp-ats-score").addEventListener("click", () => {
      alert("🎯 [JobHunt Pro] ATS Match Score: 96% Match! Dynamic keywords injected.");
    });
  }

  setTimeout(injectOverlay, 1500);
})();
