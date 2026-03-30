# pyAIGameEngine Prompt Templates — REV 1.0 Addendum
**Date:** 2026-03-28

## Suggested next prompt
Use the current pyAIGameEngine project state as truth.

POC1_SoaFirst now has:
- fallback validation
- numpy/numba comparison tooling
- first AI scheduling prototype structures
- render subset selection decoupled from full simulation state

Task:
Proceed with the next implementation pass.

Requirements:
1. Add runtime schema and feature-block/feature-pack structures for one repeated object family.
2. Add a transfer-planning prototype that maps scheduled AI families to feature blocks and staged copy groups.
3. Keep benchmark comparison tooling current.
4. Preserve fallback-first architecture and keep PyBullet optional/deferred.
5. Update all affected docs, progress notes, lessons learned, workflow notes, and next-step prompts.
6. Deliver:
   - sparse snapshot ZIP
   - updated code
   - updated docs
   - exact local validation commands
   - next recommended prompt
