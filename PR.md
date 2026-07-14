# Spring Cleaning PR

## Summary

Four independent improvements to package quality, CI reliability, and security — targeting customers who begin integrations through this package.

---

## 1. SDK documentation link

- **README.rst**: replace legacy `https://geotab.github.io/sdk/` with `https://developers.geotab.com/`
- **README.rst**: fix docs URL to HTTPS canonical form (`readthedocs.io/en/latest`)

---

## 2. Python version reconciliation (3.10–3.14)

Drops Python 3.9 (EOL October 2025) and adds 3.14. Every version contract now agrees:

| Location | Before | After |
|---|---|---|
| `setup.py` runtime guard | `< (3, 7, 0)` | `< (3, 10, 0)` |
| `setup.py` `python_requires` | missing | `>=3.10` |
| `setup.py` classifiers | 3.9–3.13 | 3.10–3.14 |
| `setup.py` packages list | `mygeotab`, `mygeotab.ext` | + `mygeotab.altitude` (was silently absent from all installs) |
| `mypy.ini` `python_version` | `9` (invalid) | `3.10` |
| `pyproject.toml` ruff `target-version` | `py39` | `py310` |
| `setup.cfg` | `[bdist_wheel] universal = 1` (Python 2 artifact) | removed |
| `README.rst` | "Python 3.9+" | "Python 3.10+" |

---

## 3. Test separation — offline vs credentialed, and full version matrix

**pytest.ini** — two new marks with descriptions; `addopts` excludes both by default so `pytest` never needs network access or credentials:
```ini
markers =
    live: real network calls to public Geotab servers (no credentials)
    integration: requires MYGEOTAB_DATABASE / USERNAME / PASSWORD
addopts = -m "not live and not integration"
```

**tests/test_api_live.py** — `pytestmark = pytest.mark.live` applied.

**.github/workflows/pythonpackage.yml** — single job replaced with three:

| Job | Python | Secrets | Runs |
|---|---|---|---|
| `test-offline` | 3.10 / 3.11 / 3.12 / 3.13 / 3.14 (matrix) | none | all unit tests |
| `test-live` | 3.12 | none | unauthenticated `GetVersion` calls |
| `test-integration` | 3.12 | DB credentials | credentialed tests; exits 0 when no tests collected (exit code 5) or secrets absent |

---

## 4. Session token file protection

`mygeotab/cli.py` — enforces strict filesystem permissions on every write:

- Config **directory**: `os.chmod(..., stat.S_IRWXU)` → **0700** (owner only)
- Config **file**: `os.chmod(..., stat.S_IRUSR | stat.S_IWUSR)` → **0600** (owner read/write only)
- Applied in both `Session.save()` and `Session.logout()`
- `myg --help` now includes guidance: *"To remove a saved session run: `myg sessions remove <database>`"*

---

## 5. Coverage: 59% → 81% (+22 pp)

835 lines of new tests across 5 files; 163 tests pass, 0 failures.

| File | Before | After |
|---|---|---|
| `altitude/daas_definition.py` | **0%** | **100%** |
| `exceptions.py` | ~90% | **100%** |
| `parameters.py` | ~95% | **100%** |
| `altitude/wrapper.py` | ~15% | **83%** |
| `api.py` | ~65% | **83%** |
| `ext/entitylist.py` | ~60% | **73%** |

**New file — `tests/test_daas_definition.py`**: full branch coverage of `DaasError`, `DaasResult` (None/empty/missing-`apiResult` guards, gateway errors, `apiResult` errors, `"error"` singular field, `errorMessage` as string/dict/empty), `DaasGetJobStatusResult` (all four `has_finished()` outcomes, `errorResult` override, missing `status` key), `DaasGetQueryResult`.

**Extended — `tests/test_altitude.py`**: `_extract_errors` (both branches), `call_api` (success, invalid name, non-retry exception), `create_job` (success, errors in response, re-raise), `check_job_status`, `wait_for_job_to_complete` (immediate done, polling, error path), `fetch_data` (single page, not-finished guard, multi-page), `get_data`, `do` (full orchestration).

**Extended — `tests/test_api_call.py`**: `authenticate()` `ExtendSession` path, `"ThisServer"` redirect, no-`path`-in-result, `DbUnavailableException` (`Initializing` + `UnknownDatabase`), other-exception re-raise; `call()` re-auth on `InvalidUserException` when password present, `__reauthorize_count` guard prevents infinite loop; `multi_call` with no params element.

**Extended — `tests/test_api.py`**: `_process()` unknown-structure passthrough; `_server` fallback to `my.geotab.com`; `MyGeotabException.data` field.

**Extended — `tests/test_api_entitylist.py`**: `first`/`last` on empty list, `entity` with 0 items, `__add__` plain list, `__radd__`, `__mul__`/`__rmul__`, `__copy__`, `to_dataframe` `ImportError`, `EntityListAPI.get` return type.

---

## Commits

| SHA | Message |
|---|---|
| `6e24073` | `chore: fix SDK link, Python version contracts, test separation, token file permissions` |
| `9854eab` | `fix(ci): treat pytest exit 5 (no integration tests) as success` |
| `3c955ce` | `test: raise offline coverage from 59% to 81%` |
| `c7ee84f` | `chore: expand supported Python range to 3.10–3.14` |
