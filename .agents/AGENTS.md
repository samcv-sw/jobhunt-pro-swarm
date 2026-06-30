# Multi-Persona Council & AI Context Rules

## Global Constraints
1. **Never use placeholder code** (e.g., `// TODO: implement`). Always provide complete, copy-paste-ready file outputs.
2. **Lazy Loading of Tools**: Use context efficiently. Only load metadata and tools when strictly necessary for the active domain.
3. **No Sycophancy**: Do not blindly agree with the user if their technical request contradicts structural integrity or best practices.

## Multi-Persona Evaluation Council
For all complex code generation, especially regarding architecture and UI/UX:
1. **Skeptic**: Assume the generated code has hidden bugs or fails to account for edge cases. Identify what is wrong, missing, or overly complex.
2. **Domain Expert**: Review the code from the perspective of a Senior Architect. Are CSS Logical Properties strictly used? Are the typography and cultural colors accurate for the Gulf region?
3. **Adversary**: Construct the strongest argument against the chosen approach. E.g., "This flex layout will break on older browsers" or "This font size is too small for Arabic legibility."
4. **Synthesis Pass**: Combine the initial output with these critiques to produce the final, hardened codebase.

## UI/UX & Layout Directives (Arabic & RTL Focus)
1. **CSS Logical Properties MUST BE USED**:
   - `margin-left` -> `margin-inline-start`
   - `padding-right` -> `padding-inline-end`
   - `left`/`right` -> `inset-inline-start`/`inset-inline-end`
   - `width`/`height` -> `inline-size`/`block-size`
2. **Arabic Typography**:
   - Fonts: `'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif`
   - Min font-size: `14px` (recommended `16px` for readability)
   - Line-height: `1.6` to `2.0`
   - No `letter-spacing` on Arabic text.
3. **Cultural Ergonomics**:
   - Primary action buttons (CTAs) should remain centrally located or naturally positioned for right-handed users on mobile devices, avoiding blind mechanical mirroring.
   - **Colors**: Green for success. Black/Gold for luxury. Blue for trust. Red for strict errors only.
4. **Forms**: All inputs must use `dir="auto"`.
5. **Directional Icons**: Use `transform: scaleX(var(--text-x-direction))` with a `--text-x-direction` variable (`1` for LTR, `-1` for RTL).
