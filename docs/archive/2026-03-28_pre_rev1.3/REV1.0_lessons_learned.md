# pyAIGameEngine Lessons Learned — REV 1.0 Addendum
**Date:** 2026-03-28

## Numba comparison lesson
A standalone kernel speedup does not guarantee an integrated runtime speedup. Fair comparison requires warmup awareness and structured benchmark output.

## Render-decoupling lesson
Even before a dedicated renderer exists, separating render-subset selection from full simulation state helps identify render-facing costs and keeps stage boundaries cleaner.

## AI scheduling lesson
AI scheduling should start as a minimal spec-driven planning layer before introducing real model execution complexity.
