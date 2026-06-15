# JobHunt Pro - Auto Apply Chrome Extension

## Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle top-right)
3. Click "Load unpacked"
4. Select this folder: `web/static/extension/`

## Usage

1. Click the extension icon → **Configure Profile**
2. Enter your name, email, phone, LinkedIn, and resume filename
3. Save your profile (stored locally in your browser)
4. Visit any supported job site (LinkedIn, Indeed, Bayt, NaukriGulf, etc.)
5. Click the floating **⚡ Auto Apply** button on the page
6. Review the filled form and submit!

## Supported Job Sites

- LinkedIn (Easy Apply)
- Indeed
- Bayt.com
- NaukriGulf
- Naukri.com
- Glassdoor
- Monster
- ZipRecruiter
- FoundItGulf
- GulfTalent

## Icon Generation

Replace the placeholder icons in `icons/` with real 16×16, 48×48, and 128×128 PNG icons.
You can generate them from the JobHunt Pro logo.

## Permissions

- **storage**: Store your profile locally
- **activeTab / scripting**: Detect and fill job forms
- **host_permissions**: Access supported job sites for form detection

## Privacy

All profile data is stored in `chrome.storage.local` — it never leaves your browser.
Application stats are tracked locally only.
