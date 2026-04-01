from __future__ import annotations

import argparse
import json
from pathlib import Path

from poc1_engine.ai.action_bridge import build_default_action_bridge
from poc1_engine.ai.feature_blocks import build_default_feature_block_registry
from poc1_engine.interfaces.configurable_interface import (
    default_generated_doc_path,
    default_manifest_path,
    load_and_compile_default_manifest,
    write_human_readable_interface_doc,
)
from poc1_engine.runtime.runtime_schema import build_default_runtime_schema_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and compile the bounded configurable-interface manifest.")
    parser.add_argument("--emit-doc", action="store_true", help="Write/refresh the human-readable interface control doc.")
    parser.add_argument("--output-json", action="store_true", help="Print the compiled interface summary as JSON.")
    parser.add_argument("--manifest-path", type=Path, default=default_manifest_path())
    parser.add_argument("--doc-path", type=Path, default=default_generated_doc_path())
    args = parser.parse_args()

    runtime_schemas = build_default_runtime_schema_registry()
    feature_blocks = build_default_feature_block_registry(runtime_schemas)
    action_bridge = build_default_action_bridge()
    plan = load_and_compile_default_manifest(runtime_schemas, feature_blocks, action_bridge)

    if args.emit_doc:
        write_human_readable_interface_doc(plan, args.doc_path)

    if args.output_json:
        print(json.dumps(plan.summary(), indent=2, sort_keys=True))
    else:
        print(f"manifest_id={plan.manifest.manifest_id}")
        print(f"manifest_version={plan.manifest.manifest_version}")
        print(f"manifest_hash={plan.manifest_hash}")
        print(f"validator_version={plan.validator_version}")
        print(f"validator_hash={plan.validator_hash}")
        print(f"runtime_binding={plan.manifest.runtime_binding}")
        print(f"compatibility_status={plan.compatibility_handshake.status}")
        print(f"compiled_channels={[channel.channel_id for channel in plan.compiled_channels]}")
        if args.emit_doc:
            print(f"human_doc_path={args.doc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
