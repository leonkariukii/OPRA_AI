# OPRA.AI — Environment Recovery Report

**Task ID:** `OPRA-ENV-001`  
**Date:** 2026-11-27  
**Environment:** Existing repository `.venv`; no recreation performed

## Recovery actions

The existing `.venv\Scripts\python.exe` was verified as Python 3.11.18. Its `pyvenv.cfg` points to the uv-managed CPython 3.11 installation and records uv 0.13.10. The `uv` executable itself was not found on `PATH` or in the checked conventional locations. The venv interpreter reported `ensurepip` version 26.3, while `python -m pip --version` initially failed because pip was not installed in the venv.

Recovery performed in place using the standard library bootstrap:

```text
.venv\Scripts\python.exe -m ensurepip --upgrade --default-pip
Looking in links: ...
Processing ... setuptools-79.0.1-py3-none-any.whl
Processing ... pip-26.3-py3-none-any.whl
Installing collected packages: setuptools, pip
```

Afterward, `python -m pip --version` reported pip 26.3 from the project `.venv` on Python 3.11. No project dependencies or lockfiles were changed, and the virtual environment was not deleted or recreated.

## Tool and dependency verification

| Component | Installed version | Lockfile version | Result |
|---|---:|---:|---|
| Python | 3.11.18 | n/a | Available |
| pip | 26.3 | n/a | Bootstrapped into existing venv |
| Ruff | 0.17.6 | 0.17.6 | Available |
| mypy | 2.4.1 | 2.4.1 | Available |
| pytest | 9.2.0 | 9.2.0 | Available |
| pytest-cov | 7.1.0 | 7.1.0 | Available |
| Streamlit | 1.67.0 | 1.67.0 | Available |
| uv CLI | Not found | uv 0.13.10 recorded in venv config | Not available; `uv sync --locked` could not be run |

The listed development and runtime packages match versions recorded in `uv.lock`. `python -m pip check` returned `No broken requirements found.` This checks installed package consistency; it does not replace `uv sync --locked` verification, which remains unavailable.

## Baseline quality gates

Commands were run from the repository root with the project venv interpreter and `PYTHONPATH=src`, which exercises the same project tools without `uv`:

| Command | Result |
|---|---|
| `.venv\Scripts\python.exe -m ruff check .` | **Failed:** 5 findings: SIM905 in `records.py`, import ordering in two ingestion test files, and two FURB157 findings in `test_records_ingestion.py`. |
| `.venv\Scripts\python.exe -m ruff format --check .` | **Failed:** 4 files would be reformatted; 46 were already formatted. |
| `.venv\Scripts\python.exe -m mypy src/opra` | **Passed:** `Success: no issues found in 22 source files`. |
| `.venv\Scripts\python.exe -m pytest --cov=opra --cov-report=term-missing` | **Passed:** 332 passed; 92.97% total coverage (coverage threshold was not requested in this baseline command). One pytest cache permission warning occurred. |

The four requested gates are executable through Python module invocations, but the exact `uv run ...` forms are blocked by the missing uv CLI. Ruff findings and formatting are existing baseline failures and have not been fixed in this recovery task.

## Repository preservation note

At inspection, `src/opra/ingestion/csv_loader.py` had a pre-existing working-tree modification. It removed the broken `exact_duplicate_count` property, simplified UTC parsing, removed an unused local, and changed sorting to `min`. This file was not edited by the environment recovery action and was preserved. No other source or test files were changed by this recovery report task.

## Status

Python 3.11 and test/static-analysis tools are operational in the existing `.venv`. The venv package set is internally consistent and the inspected tool versions match the lockfile. Lockfile synchronization through uv is unverified because the uv executable is missing. Baseline Ruff lint and formatting checks fail as recorded above; mypy and pytest pass.
