## 2026-07-05T18:20:14Z

Apply the frontend UI/UX & RTL polish defined in SCOPE.md:

1. Create a dynamic locale wrapper setup:
   - Create 'frontend/src/app/locale-context.tsx' containing the state and a LocaleProvider component to manage and share client-side 'locale' and 'isArabic' state. It should also dynamically update document.documentElement.lang and document.documentElement.dir attributes in a useEffect.
   - Create 'frontend/src/app/root-html.tsx' as a Client Component that reads 'locale' from LocaleContext and renders a dynamic <html lang={locale} dir={locale === 'ar' ? 'rtl' : 'ltr'} className={className}>{children}</html> element.
   - Modify 'frontend/src/app/layout.tsx' to use LocaleProvider and RootHtml. Move static 'h-full' to dynamic inline styling (e.g. style={{ blockSize: '100%' }}) on RootHtml, and 'min-h-full' on body to style={{ minBlockSize: '100%' }}.

2. Update 'frontend/src/app/page.tsx' and 'frontend/src/app/dashboard/page.tsx':
   - Remove the local 'isArabic' state and replace it with useLocale() from the shared context.
   - Audit and replace all physical sizing Tailwind classes (w-*, h-*, min-h-*, max-h-*, max-w-*) with logical inline styles (style={{ inlineSize: '...', blockSize: '...', minBlockSize: '...', maxBlockSize: '...', maxInlineSize: '...' }}).
   - In page.tsx, remove 'tracking-tight' from the <h1> element displaying the title.
   - In page.tsx, scale up all 'text-xs' classes rendering Arabic to at least 'text-sm' (14px) and set explicit logical line-heights of '1.8' to '2.0' (using leading-[1.8] or inline styles).
   - In dashboard/page.tsx, replace leading-relaxed classes on elements displaying Arabic text with leading-[1.8] or leading-[2.0].

3. Modify 'frontend/src/app/globals.css' to optimize paint performance for glassmorphism hover shadow transitions:
   - Remove box-shadow transition from .glass-panel.
   - Set up a .glass-panel::after pseudo-element with position: absolute, inset: 0, border-radius: inherit, pointer-events: none, z-index: 0, opacity: 0, and the hover box-shadow styles. Add transition: opacity var(--duration-base) var(--ease-out-quint).
   - On .glass-panel:hover::after, set opacity: 1.

4. Build the application:
   - Change directory into 'frontend/' and run the production build ('npm run build' or 'npx next build') to verify that there are no terminal or compilation errors.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_frontend_v5\worker_m3

When complete, write a handoff.md in your working directory and report back to your parent conversation (me) by calling send_message.
