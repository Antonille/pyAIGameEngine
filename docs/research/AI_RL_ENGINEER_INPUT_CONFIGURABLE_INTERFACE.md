# AI/RL Engineer Memo — Configurable Interface

## Summary
The first configurable-interface control document should define a general contract language for channels, views, timing, and composition rather than locking the project to one flat observation vector and one flat action vector.
The memo recommends multi-channel support, separation of semantic role from representation kind, explicit timing metadata, startup compilation/freeze, bounded variable-length support, multiple views over the same world state, model roles beyond direct controllers, hybrid pipelines, a hot control plane versus warm/cold semantic plane split, explicit memory/state channels, units/frame/normalization metadata, and a capability handshake.

## Implementation timing recommendation
Define the full conceptual envelope now, but implement only the minimal subset needed for the current POC and compile/freeze that subset into a startup runtime plan.
