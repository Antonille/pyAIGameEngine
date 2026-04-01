# Physics Engine Engineer Input — Configurable Interface

## Summary
- Startup-loaded interface definition is feasible and desirable.
- Validation must fail fast at startup.
- Per-plank-tic dynamic interpretation is not acceptable for engine performance.
- Binary serialization should come later, after the semantic contract stabilizes.
- The current Gym direct-write path should not become the long-term public boundary.

## Physics-engine recommendation
Implement configurable-interface groundwork now as a startup-loaded, startup-validated, startup-compiled plan for a narrow repeated-family hot control-plane subset, while preserving the existing hardcoded hot-path runtime mapping until the boundary proves stable and performance-neutral.
