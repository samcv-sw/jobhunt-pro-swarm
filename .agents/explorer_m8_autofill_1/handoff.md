# Milestone 8 Handoff Report — Auto-Fill Browser Agent

## 1. Observation
The following details were directly observed in the codebase:
- **File Location**: The applying browser agent is located in `core/ghost_applicant.py` (lines 8-23):
  ```python
  class GhostApplicant:
      """
      The Ghost Applicant Engine.
      Uses Playwright to automatically fill and submit job applications
      on Greenhouse, Lever, and Workable portals, bypassing email entirely.
      """
  ```
- **Current Implementations**:
  - `_fill_greenhouse` (lines 73-126) relies on specific, rigid CSS selectors such as:
    ```python
    await page.fill("input[name='job_application[first_name]']", profile.get("name", "").split(" ")[0])
    ```
  - `_fill_lever` (lines 127-153) matches inputs using strict CSS selectors:
    ```python
    await page.fill("input[name='name']", profile.get("name", ""))
    await page.fill("input[name='email']", profile.get("email", ""))
    await page.fill("input[name='phone']", profile.get("phone", ""))
    ```
  - `_fill_generic` (lines 154-195) iterates over profile fields and attempts fuzzy CSS selectors matching using:
    ```python
    locators = [
        f"input[name*='{key}' i]",
        f"input[id*='{key}' i]",
        f"input[placeholder*='{key}' i]",
    ]
    ```
- **Codebase References**: Run PowerShell search commands for `GhostApplicant` and `apply_to_url` in the codebase.
  - **Command**:
    ```powershell
    Get-ChildItem -Path "C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi" -Filter *.py -Recurse -ErrorAction SilentlyContinue | Select-String -Pattern "GhostApplicant" -List | Select-Object Path
    ```
  - **Result**: Only `core/ghost_applicant.py` contains these references. It is completely isolated and is not imported, instantiated, or used in `core/multi_platform_apply.py`, `core/campaign_runner.py`, or any of the webapp routes in `web/`.
- **Existing Evasion/Stealth Assets**:
  - `core/stealth.py` provides Canvas and WebGL spoofing JavaScript injection (lines 356-395), rotating user-agents, and proxy support.
  - `core/human_mouse.py` (lines 16-103) implements a cubic Bezier curve trajectory and EaseInOutCubic easing mechanism to generate natural mouse paths, compatible with Playwright's `page.mouse.move()` command:
    ```python
    async def simulate_mouse_movement(page: Any, start_x: int, start_y: int, dest_x: int, dest_y: int) -> None:
        # Dispatch native mouse move event (Playwright/Nodriver compatible format)
        await page.mouse.move(x, y)
    ```

---

## 2. Logic Chain
The reasoning leading to the recommended browser autofill implementation is as follows:
1. **Greenhouse, Lever, and Workable forms** are frequently embedded or customized, causing rigid CSS attribute matching (like `input[name='job_application[first_name]']`) to fail if class names, form versions, or custom wrappers are updated.
2. **Dynamic IDs and Name attributes** are typical of modern frontend frameworks (React, Angular, Vue, Tailwind UI, etc.). This makes standard attribute queries brittle.
3. **Accessibility Attributes and Parent Text crawling** offer a significantly more robust approach. Browsers and accessibility tools construct an accessibility tree which maps labels directly to their corresponding input fields, regardless of dynamic naming.
4. **Iframe Traversal** is required because many portals load application forms within sub-frames. The agent must recursively query `page.frames` to target fields within nested iframes.
5. **Human Emulation** is required to bypass behavioral detection systems (Cloudflare, Datadome, Turnstile). Direct `locator.fill()` values are populated instantly, which triggers event listeners checking for copy-paste or programmatic speeds. Implementing a character-by-character typing loop (`press` key event simulation) and Bezier mouse movement ensures the application appears organic.
6. **Execution Sandbox Testing**: To verify this logic, a proposed file `proposed_ghost_applicant.py` was created containing:
   - Dynamic fuzzy label matching (crawling attribute markers `name`, `id`, `placeholder`, `aria-label`, and text inside associated `<label>` and parent elements).
   - Dropdown handling for `select` elements (including automated "No" to sponsorship and "Yes" to work authorization questions).
   - Iframe crawling using `page.frames`.
   - Human emulation (`_type_humanlike` keystroke jitter, hover movements, and delays).
7. A local mock form (`mock_job_form.html`) and test script (`test_autofill.py`) were developed, executing Playwright headlessly.
8. The test successfully located, matched, and populated:
   - First name, Last name, Email, Phone, LinkedIn URL, and CV file upload.
   - Sponsorship select (set to "no") and Work Auth select (set to "yes").
   - Passed all strict assertions.

---

## 3. Caveats
1. **Network Sandbox**: The verification was completed inside a local filesystem sandbox using `file://` URLs because the agent is operating in CODE_ONLY mode (no external web access).
2. **Third-Party CAPTCHAs**: The proposed autofiller does not bypass dynamic, image-based third-party CAPTCHAs (like reCAPTCHA v3 or Turnstile) on forms without using solver services (like `core/captcha_solver.py`), though it is configured with maximum browser-level stealth to prevent them from triggering.
3. **PythonAnywhere Environment Restrictions**: Since the target environment is PythonAnywhere (which enforces virtual memory limits and does not support headed graphical rendering), running headless Chromium using Playwright must be strictly serialized (e.g., using a background task queue) to prevent Out-Of-Memory (OOM) crashes.

---

## 4. Conclusion
We recommend rewriting `core/ghost_applicant.py` using the dynamic fuzzy matching, iframe crawling, and human emulation script verified in `proposed_ghost_applicant.py`.

### Actionable Next Steps:
1. **Replace Core Engine**: Overwrite `core/ghost_applicant.py` with the contents of `proposed_ghost_applicant.py`.
2. **Integrate into Orchestrator**: Update the `apply` method in `core/multi_platform_apply.py` (or a dedicated job dispatcher) to import `GhostApplicant` and call it for detected external links pointing to applicant forms (Greenhouse, Lever, etc.).
3. **Queue Applications**: Implement a serialized job queue (similar to `core/blast_queue.py`) under `data/apply_queue/` to run Playwright applications sequentially (1 concurrency limit) to remain compliant with PythonAnywhere's memory constraints.
4. **Stealth Enhancements**: Hook `core/human_mouse.py`'s `simulate_mouse_movement` into the click operations to ensure realistic pointer movements before executing clicks.

---

## 5. Verification Method
To verify the implementation of the autofill agent, execute the following commands in the workspace:

```powershell
# 1. Navigate to the agent's folder
cd "C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m8_autofill_1"

# 2. Run the automated Playwright test script
python test_autofill.py
```

### Expected Output:
```text
Initializing enhanced autofiller test...
Navigating to: file:///C:/Users/samde/Desktop/.../mock_job_form.html
Running universal autofill engine...
[GHOST] Scanned page and found 1 sub-frames.
[GHOST] Uploaded CV to frame element: ...
[GHOST] Fuzzy match found! Field: 'first_name', Markers: 'field_first_name first_name_input john  first name'
[GHOST] Fuzzy match found! Field: 'last_name', Markers: 'field_last_name last_name_input doe  last name'
[GHOST] Fuzzy match found! Field: 'email', Markers: 'field_email email_address example@domain.com  emai'
[GHOST] Fuzzy match found! Field: 'phone', Markers: 'field_phone mobile_phone +12345678  mobile phone'
[GHOST] Fuzzy match found! Field: 'linkedin', Markers: 'linkedin linkedin_url   linkedin url'
[MOCK] Bypassing submit button click to run assertions on form state.
--- Test Results ---
First Name: Sam (Expected: Sam)
Last Name: Salameh (Expected: Salameh)
Email: samsalameh.cv@gmail.com (Expected: samsalameh.cv@gmail.com)
Phone: +96170123456 (Expected: +96170123456)
LinkedIn: https://linkedin.com/in/samsalameh (Expected: https://linkedin.com/in/samsalameh)
Sponsorship Selection: no (Expected: no)
Work Auth Selection: yes (Expected: yes)
🎉 All assertions passed! Universal Autofill works perfectly.
```

### Invalidation Conditions:
- If Playwright throws an import error (insufficient PythonAnywhere libraries).
- If the browser fails to locate hidden input elements or is unable to upload files due to frame path differences.
- If form submission triggers an immediate Cloudflare challenge that requires CAPTCHA resolution.
