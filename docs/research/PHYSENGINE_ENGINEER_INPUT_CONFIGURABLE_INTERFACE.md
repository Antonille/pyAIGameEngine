# 1. Current Interface and Schema

The existing engine–AI boundary is **statically defined** in code and docs.  For example, `ai_api.py` and `model_api.py` define fixed dataclasses like `FeatureBlockContract` and action-packet structures that the engine uses for observations and controls.  Corresponding documentation (the “AI Interface Control Document” and “Model Interface Control Document”) spells out the expected feature blocks and action formats.  In short, the engine’s observation/action schema is hard-coded in Python and in markdown spec files, not loaded from external files. 

**Key artifacts:** The repo contains `poc1_engine/interfaces/ai_api.py` (feature-block and packet contracts) and `poc1_engine/interfaces/model_api.py` (for model feedback), plus control docs (`AI Interface Control Document.md`, etc.) that fully describe the interface. No runtime mechanism currently reads an interface description at startup – the engine and model simply use the shapes coded in these files.  

# 2. Dynamic Interface in Industry and Research

Several modern frameworks allow interface/schema configuration via external files.  For example:

- **Habitat-Lab (AI Simulators):**  Habitat uses Hydra/OmegaConf for environment config.  Agents, sensors, and actions are specified in YAML/JSON templates that the simulator reads at startup.  Hydra’s system enables *config reuse* and dynamic composition.  As documented, “it is possible to use the same agent config to configure two agents of the same type” by redeclaring config nodes【39†L574-L581】.  In practice, Habitat’s benchmark configs list enabled sensors, action sets, and parameters in YAML, and these are validated/merged at launch.  This shows that a simulation can dynamically assemble observation/action spaces from a config file.

- **AWS DeepRacer (RL Platform):**  The DeepRacer console now allows **fully customizable action spaces** defined via JSON.  Users edit a JSON in S3 to specify steering-angle and throttle actions, and the system dynamically visualizes and validates them【20†L59-L67】.  This decoupled “vehicle config” lets racers swap action sets without changing code.  In short, DeepRacer reads the action definitions at runtime (from JSON) and the UI/engine adjusts accordingly.  

- **Interface Schemas (General):**  In distributed systems, an *interface schema* (e.g. WSDL/XML Schema, JSON Schema) formally defines message formats【23†L70-L79】【23†L88-L96】.  Such schemas make the contract explicit and enable automated validation of message instances.  For example, standard practice in SOA/REST is to define data structures (via XML Schema or JSON Schema) so clients and servers can **validate** exchanged data against a shared contract【23†L70-L79】【23†L88-L96】.  We can draw an analogy: our engine–model boundary could be governed by a schema that both sides load and validate.

- **JSON/YAML + Schema:**  In web and ML settings, one often uses JSON/YAML config files plus a schema validator (e.g. JSON Schema or dataclass-based checking) to enforce correctness.  JSON/YAML are human-readable (CSV is similar), and libraries exist to parse/validate them.  As one survey notes, text-based configs (JSON/YAML) are easy to work with, and moving to a binary encoding (like Protobuf) later can improve startup speed【37†L111-L119】. 

These examples suggest that a *config-driven, runtime-defined interface* is feasible and can improve flexibility.  Engines like Habitat and tools like DeepRacer already load observation/action specifications from files. The trade-off is added parsing/validation overhead (negligible on startup) and implementation effort.  

# 3. Prototype: Config-Driven Loader & Validator

**Approach:**  Define the interface schema in a file (e.g. CSV initially, later JSON/Protobuf).  At startup, the engine reads this file to build the observation and action definitions. For instance, a simple CSV might list feature-block names, widths, dtypes, etc., and another CSV could list valid action names/parameters. A loader (in Python) would parse these into the existing contract classes (e.g. create `FeatureBlockContract` instances from CSV rows). The engine and agent would use these contracts for all data exchange. 

**Validation:**  Along with loading, we implement a routine to check consistency: for example, the engine could generate an “expected interface hash” and verify that the model sees the same schema. Or more simply, after loading the interface file, run a self-test: write and immediately read a dummy packet and ensure shapes match. We could also use a schema-validation library (e.g. JSON Schema or Pydantic) to enforce field types. The goal is to **fail fast** if the engine’s config and the model’s expectations diverge. 

**Optional binary format:**  As suggested, start with CSV or JSON (for ease of editing). Later we can migrate to a binary format (e.g. a serialized Protocol Buffer or custom binary record) for faster loading.  Binary-encoded schemas are typically *faster to parse* and more compact【37†L111-L119】. The dev write-up on this notes that binary formats strip extra characters and are “closer to the machine’s native language,” so parsing is quicker【37†L111-L119】. We can generate a binary blob from our CSV after the config is stabilized, if load-time becomes a bottleneck.

# 4. Performance and Safety

- **Startup overhead:** Parsing a small CSV/JSON at startup is negligible (milliseconds). Even Python’s JSON/XML parsers handle MB-sized configs quickly.  If needed, caching a binary version (once loaded) can make subsequent starts very fast【37†L111-L119】. 

- **Runtime overhead:** There should be **no extra per-tick cost**. After startup, the engine would operate as before, using fixed-size buffers/arrays. The loaded schema dictates these sizes once, then normal SIMD/batched updates proceed. The only potential overhead is in the initial memory allocation based on config-defined lengths. As long as we reuse array memory (zero-copy transfer of large blocks), this is minor.

- **Safety/Validation:** A schema file introduces risk of mismatch or malicious config. We mitigate by strict validation at load time (throw an error if invalid). Using a formal schema (or even simple assertions) ensures the data shapes and dtypes match code expectations. Also, we should treat the config file as trusted input (e.g. check a version field or signature). If an invalid configuration is loaded, we must fail immediately rather than running with unknown behavior. Overall, this increases safety by making the contract explicit.

- **Flexibility vs. performance:** The main “cost” of this change is complexity of implementation. It does **not** require slowing the physics loop or deep refactors; it only changes the setup phase. At runtime, the interface lookup is static. If we later add true run-time interface switching (e.g. mid-simulation), that could degrade performance, but our plan is only startup-time flexibility. 

# 5. Implementation Plan

**a. Define schema format.**  Draft a simple CSV/JSON schema file that lists the observation blocks and action blocks. For example, columns: `block_name,width,dtype,semantics,freshness_policy` and for actions: `action_name,actor_family,vector_length,range`. The project’s current docs and `FeatureBlockContract` definitions provide a template. We’ll document this schema so model developers know how to write compatible files.

**b. Write loader & validator.**  In the engine initialization (just before Gate-D evaluation), add a routine to load the interface file from disk. Parse it into the existing contract classes. Immediately run basic checks: correct total size, no name collisions, dtype valid, etc. Optionally, use a JSON schema or Python assertions for stricter checks. If validation fails, throw an error. 

**c. Adapt engine code to use loaded schema.**  Replace hard-coded lists of features/actions with loops over the loaded schema. For example, where the code used to generate the default observation array of fixed length, it now sums up widths from the config. Similarly, action application routines will index into `state.action` based on names from the file. Ideally, this is done modularly so that if no config file is found, the engine could fall back to a default (for backward compatibility).

**d. Update the Gym/adapter.**  The minimal Gym adapter should be revised so it does not bypass the new schema logic. For instance, instead of writing directly into `state.action`, the adapter should construct a packet or use the schema to place action values. This ensures the new interface pathway is exercised. Initially, we can mark the old direct path as **“temporary scaffolding”** (to be removed once the new method is validated).

**e. Timeline and rollout:**  We recommend prototyping this **now** (immediately after the POC current milestone). The effort is mainly in code around loading/parsing, which is orthogonal to core physics. It can be done in parallel with continued test/report implementation. We can start with CSV to get it working quickly, then convert to a binary format in a follow-up sprint. By doing it soon, we can benefit from dynamic testing (e.g. try out varying interfaces in regression tests). It also aligns with our validation goals: a schema-based interface makes automated tests check the right quantities.

**f. Scope and risks:**  The scope is moderate: touch in engine startup code, the AI adapter, and a few data-structure initializers. We will **not** alter physics or core loops. Main risks are implementation bugs in the loader or mismatches in coordinate/dtype. These are manageable with unit tests. Performance risk is negligible for startup loading; and safety is improved via validation. We do *not* see any fundamental limitation that would make this impossible. In fact, the evidence from systems like Habitat and AWS indicates this is a common pattern.

# Summary

Dynamic interface definition is feasible and could greatly improve flexibility.  Our research shows industry tools already do this via config files (Habitat, AWS DeepRacer). We can prototype a CSV/JSON-based schema loader and validate it at startup. The runtime cost is minimal and can be optimized with a binary format later【37†L111-L119】. The implementation work is mostly around parsing and adapting the current contracts to use the loaded schema. We recommend proceeding with this in the next iteration: define the schema, implement the loader/validator, and mark the old hard-coded paths as temporary. This will make future model swapping and extensive testing much smoother. 

**References:** Standard interface-schema design【23†L22-L30】【23†L88-L96】; examples of config-driven environments (Habitat’s Hydra/OmegaConf config【39†L574-L581】, AWS DeepRacer JSON actions【20†L59-L67】); and the performance benefits of binary vs. text config【37†L111-L119】. These support the viability of our plan.