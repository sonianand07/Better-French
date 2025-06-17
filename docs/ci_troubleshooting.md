# CI / Netlify Troubleshooting Cheat-Sheet (2025-06-15)

A quick reference for the recurring build-pipeline issues we hit today and how we fixed them.  Keep this file updated whenever a new class of error appears.

---

## 1. Netlify preview/deploy fails in **Initializing** stage

**Symptoms**  
• All Netlify checks show red "Deploy failed" almost instantly.  
• Netlify UI banner: *"A failure prevented us from deploying your project."*

**Root cause**  
Netlify doesn't know what to build/publish (no `netlify.toml`) and aborts.

**Fix**  
Add `netlify.toml`:
```toml
[build]
  command = ""
  publish = "Project-Better-French-Website"
```

---

## 2. Netlify fails during **Install dependencies** with `blis` wheel error

**Symptoms**  
```
ERROR: Failed building wheel for blis
```

**Root cause**  
Netlify defaulted to Python 3.13; spaCy's `blis` wheel isn't available yet.

**Fix**  
Pin Python to 3.10 in `netlify.toml`:
```toml
[build.environment]
  PYTHON_VERSION = "3.10"
```

---

## 3. GitHub workflow "Quality Repair – contextual explanations" fails

**Symptoms**  
```
ModuleNotFoundError: No module named 'scripts'
```

**Root cause**  
`quality_repair.py` imported `scripts.note_logger` by package path; when executed directly, `scripts` isn't on `PYTHONPATH`.

**Fix**  
Patch at top of file:
```python
import pathlib, sys as _sys
_sys.path.append(str(pathlib.Path(__file__).parent))
try:
    from note_logger import log_task
except ImportError:
    from scripts.note_logger import log_task
```

Merged in commit **7a601e2**.

---

## 4. Playwright accessibility audit fails to load axe-core CDN

**Symptoms**  
```
Page.add_script_tag: Error: Failed to load script …/axe.min.js
```

**Root cause**  
CDN occasionally blocked in CI environments.

**Fix**  
Wrap injection in broad `except` and treat failure as a *skipped* audit (commit **e42563a**).

---

## 5. Cron schedule vs. branches

The scheduled job always runs on **main**.  Hot-fixes must be merged into `main` *before* the next cron tick, otherwise the run will still fail with the old code.

---

### Handy commands

```
# Run smoke test locally
python -m http.server 8010 --directory Project-Better-French-Website &
python qa/local/test_smoke.py http://localhost:8010

# Trigger workflow manually (CI)
# GitHub → Actions → Auto Update French News → Run workflow
```

---

Maintainer: **Better-French Max**  —  Last updated 2025-06-15. 