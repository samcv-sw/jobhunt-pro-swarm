# RTL and Localization Compliance Audit Report

## Executive Summary
An audit was conducted on the Vue frontend application located in `frontend-vue/` to evaluate compliance with RTL (Right-to-Left) and Gulf region localization standards. The application consists of three Vue components (`App.vue`, `HelloWorld.vue`, and `views/Dashboard.vue`) and one global stylesheet (`style.css`). 

Key findings indicate that while the global stylesheet (`style.css`) adopts CSS Logical Properties comprehensively, there are critical violations inside component-scoped styles (specifically `App.vue` and `Dashboard.vue`), global typography parameters that conflict with optimal Arabic legibility, and missing mechanisms for directional icons.

---

## 1. Physical Layout and Spacing Audit Findings

### Global Styles (`frontend-vue/src/style.css`)
- **Compliance**: **Highly Compliant**. The file relies on CSS Logical Properties (e.g. `margin-inline`, `padding-block`, `inset-inline-start`, `border-inline-end`).
- No physical spacing properties like `margin-left/right`, `padding-left/right`, or `left/right` were found in this file.

### Component-Scoped Styles
Physical layout properties were found in `App.vue` and `views/Dashboard.vue` that will fail to adapt in RTL contexts:

#### `frontend-vue/src/App.vue`
- **Line 9**: `margin: 0;` (under `body` selector) is a shorthand physical property. While harmless on its own, it should ideally use logical blocks (`margin-block: 0; margin-inline: 0;`).

#### `frontend-vue/src/views/Dashboard.vue`
The `<style scoped>` block contains multiple physical layout and spacing rules:
- **Line 130**: `padding: 2rem;` (under `.dashboard-container`) uses physical shorthand.
- **Line 131**: `max-width: 1200px;` (under `.dashboard-container`) uses physical inline limit.
- **Line 132**: `margin: 0 auto;` (under `.dashboard-container`) uses physical horizontal margins.
- **Lines 136, 152**: `margin-bottom: 2rem;` (under `.dashboard-header` and `.stats-cards`) uses physical direction.
- **Line 142**: `margin-bottom: 0.5rem;` (under `.dashboard-header h1`) uses physical direction.
- **Lines 159, 190**: `padding: 1.5rem;` (under `.card` and `.charts-container`) uses physical shorthand.
- **Line 171**: `margin: 0 0 1rem 0;` (under `.card h3`) uses physical shorthand specifying bottom margin.
- **Line 191**: `height: 500px;` (under `.charts-container`) uses physical block size.
- **Line 195**: `width: 100%;` (under `.chart`) uses physical inline size.
- **Line 196**: `height: 100%;` (under `.chart`) uses physical block size.

#### ECharts Configuration (`frontend-vue/src/views/Dashboard.vue`)
- **Lines 79-82**: Inside the chart initialization script, physical rendering options are hardcoded:
  ```javascript
  left: '10%',
  top: 60,
  bottom: 60,
  width: '80%',
  ```
  In RTL mode, ECharts layout will remain left-aligned unless dynamically adjusted based on the document direction.

---

## 2. Arabic Typography Audit Findings

The current font and text configurations violate regional legibility rules in the following areas:

### Font Families
- **Global Styles (`style.css`, Lines 14-15)**: 
  ```css
  --sans: 'Cairo', 'Tajawal', 'Inter', system-ui, 'Segoe UI', Roboto, sans-serif;
  --heading: 'Cairo', 'Tajawal', 'Inter', system-ui, 'Segoe UI', Roboto, sans-serif;
  ```
  The fallback order includes 'Cairo' and 'Tajawal' which are correct.
- **App component (`App.vue`, Line 10)**:
  ```css
  font-family: 'Inter', 'Roboto', sans-serif;
  ```
  This overrides the global settings and completely omits Arabic-friendly typography.

### Line Height and Letter-Spacing
- **Global Styles (`style.css`, Lines 18-19)**:
  ```css
  font: 18px/145% var(--sans);
  letter-spacing: 0.18px;
  ```
  - **Line Height**: `145%` (1.45) is too low for Arabic scripts (specifically Cairo/Tajawal), which requires a range of `1.7` to `2.0` (or `170%` to `200%`) for readability due to taller glyph structures.
  - **Letter-Spacing**: `0.18px` is applied globally. Letter-spacing must be `0` or `normal` on Arabic text as Arabic script is cursive and separating letters breaks typographical rules.

---

## 3. Inputs and Directional Icons Audit Findings

### Form Inputs
- Currently, **no form input fields** (`<input>`, `<select>`, or `<textarea>`) exist in `App.vue`, `HelloWorld.vue`, or `Dashboard.vue`.
- However, as a compliance measure, any future input components must be enforced to use the `dir="auto"` attribute.

### Directional Icons
- In `HelloWorld.vue` (Lines 30-32), the chevron icon (`documentation-icon` in `public/icons.svg`) points to the right. 
- In RTL contexts, directional icons (such as chevrons, arrows, and progress indicators) must be mirrored.
- The project **lacks any scaling/flipping variables** (e.g. `--text-x-direction`) or CSS transformations (`transform: scaleX(...)`) to automate this mirroring.

---

## 4. Concrete Fix Strategy

To address these audit findings, we propose the following multi-tiered fix strategy:

### Task A: Refactor Scoped Component Styling to CSS Logical Properties
1. **Refactor `App.vue` (`style` block)**:
   - Convert `margin: 0;` to `margin-block: 0; margin-inline: 0;`.
   - Remove `font-family` from `App.vue` to allow the global font fallback chain (`--sans` / `--heading`) to govern the typography.
2. **Refactor `Dashboard.vue` (`style scoped` block)**:
   - `padding: 2rem;` -> `padding-block: 2rem; padding-inline: 2rem;`
   - `max-width: 1200px;` -> `max-inline-size: 1200px;`
   - `margin: 0 auto;` -> `margin-block: 0; margin-inline: auto;`
   - `margin-bottom: 2rem;` -> `margin-block-end: 2rem;`
   - `margin-bottom: 0.5rem;` -> `margin-block-end: 0.5rem;`
   - `padding: 1.5rem;` -> `padding-block: 1.5rem; padding-inline: 1.5rem;`
   - `margin: 0 0 1rem 0;` -> `margin-block: 0 1rem; margin-inline: 0;`
   - `height: 500px;` -> `block-size: 500px;`
   - `width: 100%;` -> `inline-size: 100%;`
   - `height: 100%;` -> `block-size: 100%;`

### Task B: Define Arabic Typography Scopes in `style.css`
Override font metrics when the document direction is RTL or the language is set to Arabic (`:lang(ar)` or `[dir="rtl"]`):
```css
/* Arabic script adjustments */
:root:lang(ar),
[dir="rtl"] {
  --sans: 'Cairo', 'Tajawal', 'IBM Plex Arabic', sans-serif;
  --heading: 'Cairo', 'Tajawal', 'IBM Plex Arabic', sans-serif;
  font: 18px/1.8 var(--sans); /* Increase line-height to 1.8 */
  letter-spacing: 0; /* Remove letter-spacing for Arabic cursive connections */
}
```

### Task C: Implement Dynamic RTL Support for ECharts
Adjust ECharts coordinates dynamically in `Dashboard.vue` by detecting the document direction:
```javascript
const isRTL = document.documentElement.dir === 'rtl';

const option = {
  // Use logical alignments
  title: {
    text: isRTL ? 'قمع الطلبات' : 'Application Funnel',
    left: isRTL ? 'right' : 'left',
    textStyle: { color: '#c9d1d9' }
  },
  // Ensure the funnel matches the visual focus direction
  series: [
    {
      name: 'Funnel',
      type: 'funnel',
      left: isRTL ? '10%' : '10%', // Adjust dynamically if mirroring is needed
      // ...
    }
  ]
};
```

### Task D: Implement Directional Icon Scaling
1. Define a global text direction indicator in `style.css` under `:root`:
   ```css
   :root {
     --text-x-direction: 1;
   }
   
   [dir="rtl"] {
     --text-x-direction: -1;
   }
   ```
2. Apply the scaling transform to directional helper icons (`.icon`):
   ```css
   .icon.directional {
     transform: scaleX(var(--text-x-direction));
   }
   ```
3. Update `HelloWorld.vue` to add the `.directional` class to the documentation chevron:
   ```html
   <svg class="icon directional" role="presentation" aria-hidden="true">
     <use href="/icons.svg#documentation-icon"></use>
   </svg>
   ```
