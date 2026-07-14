# Scope: Milestone 1: Backend Code Quality, Refactoring & Security

## Architecture
- Refactoring and security hardening of backend core python files.
- Implementation of the Auto-Fill Browser Agent.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| M1.1 | IMP-154: Dead Code Removal | Dead code removal via vulture (vulture . --min-confidence 80) | None | PLANNED |
| M1.2 | IMP-158: Large Function Decomposition | Decompose functions >100 lines in core/ | M1.1 | PLANNED |
| M1.3 | IMP-160: Import Sorting | Import sorting with isort (isort . --profile black) | M1.2 | PLANNED |
| M1.4 | IMP-162: Dependency Pinning | pip freeze to exact versions in requirements.txt | M1.3 | PLANNED |
| M1.5 | IMP-190: LinkedIn OAuth | LinkedIn OAuth2 via authlib; auto-import profile to CV | M1.4 | PLANNED |
| M1.6 | R2: Auto-fill Browser Agent | Auto-fill browser agent `core/form_autofill.py` using Playwright | M1.5 | PLANNED |

## Interface Contracts
- `autofill_job_form` signature must be exactly as specified in `core/form_autofill.py`:
  `autofill_job_form(url: str, user_profile: dict) -> dict` returning `{success: bool, screenshot_path: str}` or error structure.
- LinkedIn OAuth endpoint must be `/api/v1/auth/linkedin` utilizing `authlib` to retrieve user profile and import to CV.
