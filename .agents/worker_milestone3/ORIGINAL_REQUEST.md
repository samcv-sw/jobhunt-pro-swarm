## 2026-07-05T16:57:30Z
Your role is teamwork_preview_worker for Milestone 3 (Frontend Overhaul). Your working directory is c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_milestone3\.
Your task is to overhaul the frontend (R1) to be premium, dynamic, and responsive while maintaining Arabic RTL support. Do not break existing routes.

Please follow these guidelines:
1. Glassmorphism Design System:
   - Upgrade '.glass-panel' and premium components in frontend/src/app/globals.css by implementing:
     - SVG grain texture overlays (via a ::before pseudo-element with a URL data SVG texture) to improve readability and style.
     - Dual-layered refractive borders (an inner border glow and soft outer border).
     - Hover-state tinted shadow-casting (using rgba(212, 175, 55, 0.12) gold tint for a premium look).
     - Modern glass panels and blur transitions.
2. RTL and Layout Compliance:
   - Strict CSS Logical Properties: Ensure zero physical layout properties remain. Convert all margins, paddings, positions, and sizes to logical properties:
     - margin-left/right -> margin-inline-start/end (or margin-inline)
     - padding-left/right -> padding-inline-start/end (or padding-inline)
     - left/right -> inset-inline-start/end
     - width/height -> inline-size/block-size
   - Typography: Font hierarchy must use Cairo and Tajawal fonts, minimum 16px font-size for Arabic readability, line-height between 1.8 and 2.0, and no letter-spacing on Arabic texts.
   - Forms: Ensure all text/email/password inputs use dir="auto" for proper contextual text alignment.
   - Directional Icons: Use transform: scaleX(var(--text-x-direction)) with a --text-x-direction variable (1 for LTR, -1 for RTL) to flip icons dynamically.
   - Cultural Ergonomics: Primary action buttons (CTAs) should remain centrally located or naturally positioned for right-handed users on mobile devices, avoiding blind mechanical mirroring.
3. Verification:
   - Run a search for physical directional CSS keywords (e.g. margin-left, margin-right, padding-left, padding-right, left:, right:) in frontend/src/ to ensure zero matches remain.
   - Run the production build command in the frontend/ folder to verify success:
     node node_modules/next/dist/bin/next build
   - Run pytest tests/e2e/test_frontend.py to verify that all frontend tests pass with zero failures.
4. Output:
   - Write your implementation details, build outputs, and test results to handoff.md in your working directory. Notify the parent orchestrator via send_message when complete.

MANDATORY INTEGRITY WARNING:
> DO NOT CHEAT. All implementations must be genuine. DO NOT
> hardcode test results, create dummy/facade implementations, or
> circumvent the intended task. A Forensic Auditor will independently
> verify your work. Integrity violations WILL be detected and your
> work WILL be rejected.
