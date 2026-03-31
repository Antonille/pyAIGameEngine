# Dynamic Interface Configuration Research

We analyzed how to let the engine and AI model read a shared interface definition at startup.  Modern systems often use a *schema* or IDL file to declare data contracts.  For example, the **Functional Mock-up Interface (FMI)** standard uses a `modelDescription.xml` that lists *all* exposed variables and their properties.  The importer (simulation engine) loads this XML so it knows exactly what inputs/outputs the model expects【10†L291-L299】.  Likewise, a JSON/YAML schema can serve as a contract: it explicitly names each field, its type, and constraints.  As one guide puts it, JSON Schema is “a language for describing and validating the structure of JSON data” – essentially *a contract between producers and consumers*【22†L153-L162】.  At startup, both engine and model could load and validate the same schema, ensuring they have matching expectations.

## Schema Definition Options

- **CSV (initial)**: A simple CSV could list field names and types.  This is human-editable, but CSV has no built-in schema validation.  We’d need custom parsing and checks (e.g. column order, name/type consistency).  As R&D suggests, a CSV can work for early prototyping, but it lacks the rigor of a formal schema.  

- **JSON/YAML with Schema**: A more robust approach is to use JSON or YAML for the interface spec, paired with a JSON Schema.  This format is self-describing and widely supported.  A JSON Schema allows automated validation of the config at startup【22†L153-L162】.  For example, the schema can require certain fields and types.  If the model’s schema doesn’t match the engine’s, we can detect and reject it immediately.  

- **IDL / FlatBuffers / Protobuf (binary)**: Eventually, we could compile the schema into a binary format (for performance or distribution).  Frameworks like **FlatBuffers** or **Protocol Buffers** use a binary format defined by a schema.  However, note that FlatBuffers in particular are *not self-describing* – the binary data must be parsed with the same schema used to create it【38†L468-L477】.  In other words, switching to a binary format usually means the schema becomes fixed (the “code” is generated) – so we lose some of the dynamic flexibility.  These are best used once the interface is stable.  Using a binary spec could improve load-time speed or memory, but it requires managing a separate compile step.

## Runtime Validation and Compatibility

In practice, we would implement a **validation routine at startup**: both engine and model read the interface file and confirm they agree.  This is analogous to FMI: the engine would read the interface description and compare it to what the model provides.  If there is a mismatch, the system should throw an error.  Using a schema-based approach (e.g. JSON Schema) makes this straightforward – the engine can simply run a JSON Schema validator against the loaded config.  Any discrepancies (missing fields, type conflicts) will be caught before simulation.  

For dynamic swapping of models, this ensures safety: whenever a new model or interface file is loaded, the validator enforces the same contract.  This avoids subtle bugs where one side expects “velocity” but the other calls it “speed” or uses a different unit.  In short, a validated schema *guarantees consistency* between engine and model at runtime【22†L153-L162】.

## Implementation Scope and Effort

- **Parsing and Validation Code**: We need to write code to read the interface file (CSV/JSON) at startup, parse it, and populate the engine’s data structures.  This involves adding a loader module (e.g. JSON parser or CSV reader) and a schema validator.  Depending on the chosen format, we might reuse existing libraries (e.g. RapidJSON with JSON Schema support, or Python’s `jsonschema` if using Python code).  

- **Engine Refactoring**: Currently the engine likely has hardcoded input/output variables.  To use a dynamic schema, we must make the data interfaces more generic – e.g. use lookup tables or reflection so that variables are accessed by name rather than fixed pointers.  This is non-trivial, but feasible.  It will require careful design to avoid run-time overhead in the inner loop (see Performance section). 

- **Model Adaptation**: The AI/RL model (or its wrapper) also needs to read the same interface definition.  For a trained model, this might mean packaging the interface file along with the model, so the model’s code can adapt (e.g. determine how many inputs to expect).  If the model is, say, a neural network, we’d need to map its output nodes to the names defined in the interface.  This is some extra work but can be done once per model version.

- **Validation Tests**: We should add tests that load a variety of interface definitions and ensure the engine and model either accept them or fail cleanly.  This is a new test area but will pay off by preventing mismatches later.

## Performance Considerations

Reading and validating the interface happens **once at startup**, so runtime performance impact is minimal.  Parsing a text-based config (even a few KB of CSV/JSON) is negligible compared to simulation costs.  The main performance concern is that dynamic lookup of variables (e.g. using a name map) could be slower than static code.  To mitigate that, we can map names to indices once at startup and then use array indexing in the inner loop.  In many existing systems (like FMI or dynamic dataflow engines), the overhead of a name lookup at startup is small, and the runtime only pays for efficient array reads【10†L291-L299】【22†L153-L162】.  

If we later switch to a binary format (e.g. FlatBuffers), parsing is still essentially one-time: the binary loader will quickly map memory to structures.  The key point is that dynamic interface adds almost **zero cost per simulation step** – the extra work is done before the loop begins.  We should profile this once implemented, but we expect any overhead to be negligible compared to the physics work.

## Testing Benefits

A dynamically defined interface greatly aids testing and flexibility.  Test harnesses can use different interface configurations to simulate alternative scenarios without recompiling the engine.  For instance, testers could add or remove output variables in the CSV and immediately rerun to see how the engine behaves.  This can speed up exploring variations (as suggested by R&D).  It also makes it easy to swap in different AI models: each model simply provides its interface file, and the engine automatically adapts.  This aligns with **contamination control** goals – the data contract is explicit and machine-validated【22†L153-L162】.  

Moreover, explicit schemas improve reliability of test reports: the harness can include interface names in logs and archives, ensuring traceability.  It fits well with our long-term reporting procedure (since interfaces become part of the “experiment configuration” archived and version-controlled).

## Risks and Mitigations

- **Implementation Complexity**: Introducing this system is a moderate coding effort (writing parsers, refactoring code, adding validators).  This could slow feature development if done too early.  To mitigate, we should scope it carefully and perhaps start after the core POC is stable.  

- **Schema Bugs**: Mis-specified schemas or validation logic could cause startup failures.  We must write good unit tests for the validator itself.  

- **Performance Bugs**: If naively implemented, a dynamic lookup inside tight loops could slow simulation.  Mitigate by caching lookups (as above).  

- **Binary Format Inflexibility**: If we compile the interface to a binary form later, we lose some of the “self-describing” ease.  As the FlatBuffers docs warn, a flatbuffer is **not self-describing** – you must know the schema to parse it【38†L468-L477】.  Thus we should only move to binary once the schema is final and lock in place (probably after major testing is done).

- **Version Synchronization**: Engine and model must use the *exact same* interface version.  We should include a version or checksum in the config and check it.  Failing fast on version mismatch is important.

## Recommendation & Plan

We recommend **designing the interface schema now, but delaying full implementation until after core POC completion**.  In practice, that means:

1. **Prototype in parallel**:  As a spike, define a simple interface JSON schema (or CSV) and write a loader in our dev environment.  Validate that the engine can parse it and that the model adapts.  This can be done concurrently with finishing POC logic, so it doesn’t block the main feature work.

2. **Gather requirements**:  Identify all data fields currently hardcoded (inputs, outputs) and put them in the spec.  Use this to refine the schema design (e.g. decide field names, units, etc.).

3. **Implement basic loader (post-POC)**:  Once the core engine is stable, integrate the loader into initialization.  Have the engine refuse to run if the schema is missing or mismatched.  This may involve refactoring the engine’s data structures as noted above.

4. **Testing and rollout**:  Create a version of the RL model that uses the schema (for example, by generating its input tensor shape from the config).  Run full validation/integration tests to ensure the new system works.  Update documentation and the test harness to use the dynamic interface files.

5. **Binary optimization (long term)**:  Only after the interface has matured and remained stable for a while should we consider a binary format (like a flatbuffer).  This could speed up load times or simplify distribution, but it should not be done until we are sure of the schema’s final form.

## Conclusion

A dynamically defined data interface is **feasible and beneficial**.  It will require some upfront engineering effort but pays off in flexibility and robustness.  By reading the interface from a config file (with a schema and validation), we ensure “engine and model have identical expectations” as requested.  The performance cost is negligible once implemented correctly.  We should proceed with prototyping now, and plan a full implementation in a controlled post-POC phase, following our testable development workflow.

**Sources:** For example, the FMI co-simulation standard uses an XML modelDescription to define all model variables and interfaces【10†L291-L299】.  More generally, JSON Schema provides a way to declare data contracts and validate them at runtime【22†L153-L162】.  (Note: binary formats like FlatBuffers require a fixed schema to parse【38†L468-L477】, so they are best used only when the interface is final.)