# Pin all Python dependencies to exact versions

**Labels:** technical-debt, infrastructure
**Priority:** Medium (Tier 2)
**Estimate:** 1-2 hours
**Blocked by:** Phase 2C finance work (complete this first)

## Problem

Currently 7 dependencies in `backend/requirements.txt` use `>=` instead of `==`:
- `asyncpg>=0.30.0`
- `shapely>=2.0.6`
- `pandas>=2.2.3`
- `numpy>=1.26.0`
- `statsmodels>=0.14.0`
- `scikit-learn>=1.3.0`
- `reportlab>=4.0.0`

This violates **CODING_RULES.md Rule 4** and creates:
- ❌ Security risk (unpinned versions can introduce vulnerabilities)
- ❌ Reproducibility issues (different environments get different versions)
- ❌ Non-deterministic CI builds

## Solution

Pin all dependencies to exact versions using `==` instead of `>=`.

## Steps to Fix

### 1. Get current installed versions
```bash
cd /Users/wakaekihara/GitHub/optimal_build
source .venv/bin/activate
pip freeze | grep -E "asyncpg|shapely|pandas|numpy|statsmodels|scikit-learn|reportlab"
```

### 2. Update backend/requirements.txt
Replace `>=` with exact versions from step 1:
```python
# Example (use actual versions from pip freeze):
asyncpg==0.30.0
shapely==2.0.6
pandas==2.2.3
numpy==1.26.0
statsmodels==0.14.0
scikit-learn==1.3.0
reportlab==4.0.0
```

### 3. Test everything still works
```bash
make verify
pytest backend/tests/ -v
```

### 4. Remove exception from .coding-rules-exceptions.yml
```yaml
# DELETE this section:
rule_4_dependency_pinning:
  - backend/requirements.txt
```

### 5. Commit and push
```bash
git add backend/requirements.txt .coding-rules-exceptions.yml
git commit -m "fix: pin all Python dependencies to exact versions

Pins 7 dependencies that were using >= to exact versions:
- asyncpg>=0.30.0 → asyncpg==0.30.0
- shapely>=2.0.6 → shapely==2.0.6
- pandas>=2.2.3 → pandas==2.2.3
- numpy>=1.26.0 → numpy==1.26.0
- statsmodels>=0.14.0 → statsmodels==0.14.0
- scikit-learn>=1.3.0 → scikit-learn==1.3.0
- reportlab>=4.0.0 → reportlab==4.0.0

This resolves CODING_RULES.md Rule 4 violations and improves:
- Security (known versions only)
- Reproducibility (same versions across environments)
- CI determinism (consistent builds)

Removes exception from .coding-rules-exceptions.yml now that
the issue is resolved.

Resolves #XXX
"

git push
```

## Acceptance Criteria

- [ ] All 7 dependencies pinned to exact versions
- [ ] `make verify` passes without Rule 4 violations
- [ ] All tests pass (`pytest backend/tests/`)
- [ ] Exception removed from `.coding-rules-exceptions.yml`
- [ ] Pre-push hook no longer shows dependency pinning violations
- [ ] Documentation updated if needed

## Related

- **CODING_RULES.md Section 4** - Dependency pinning rule
- **Tier 2 technical debt** from migration validation analysis
- **Root cause:** Phase 2 dependency audit was deferred
- **Follow-up:** Consider adding to pre-commit hook or CI

## Why This Matters

Unpinned dependencies can cause:
1. **Security vulnerabilities** - New versions may have CVEs
2. **Unexpected breakage** - API changes in minor versions
3. **Debugging nightmares** - "Works on my machine" issues
4. **Supply chain attacks** - Malicious packages pushed to PyPI

Pinning makes builds **reproducible** and **secure**.

## Notes

- Wait until Phase 2C finance work is merged
- Consider whether to also pin requirements-dev.txt
- May want to use `pip-compile` or similar tools in future
- Check if any dependencies have known vulnerabilities before pinning
