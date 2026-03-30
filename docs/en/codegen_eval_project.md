 # Code Generation Evaluation Project Document
 
 ## Content Generation Evaluation Specification
 
 ### Task Inputs and Outputs
 - Input, direct: prompts, provided code/text, and explicit instructions given to the model.
 - Input, indirect: repository context and external knowledge required to solve the task.
 - Output, expected: code, text, code changes, and required explanations for correct completion.
 - Output, actual: generated artifacts captured for evaluation and traceability.
 
 ### Evaluation Principles
 - Alignment with expected output: test pass, text match, location match, semantic match (hit@k, recall@k).
 - Necessity allowance: outputs that differ but are correct, necessary, and valuable.
 - Code quality: style, safety, performance, and maintainability considerations.
 - Process evidence: intermediate results and decision traces when available.
 
 ### Difficulty System
 - Input dimensions: tangling, scattering, scale, domain knowledge, modality.
 - Output dimensions: tangling, scattering, scale, modality.
 
 ### Metrics System
 - Process metrics: thinking time, response time, token usage, cost, and custom metrics.
 - Output metrics for code: syntax correctness, test pass rate, static analysis issues, security issues, performance issues, and similarity.
 - Output metrics for text: semantic accuracy, semantic coverage, relevance, factual errors, and custom metrics.
 - Output metrics for other modalities: format correctness, content correctness, coverage, relevance, and custom metrics.
 - Normalization and weights: per task type defaults, weight definitions, and normalization across percentage, count, and boolean metrics.
 
 ## Phase Goals
 
 ### March
 
 #### Goal
 Define and validate the minimal, high-quality evaluation workflow for March, covering representative tasks, preliminary framework design, and report outline.
 
 #### Work Items
 1. Representative samples process (inputs → outputs → difficulty → metrics).
    - Select source material per task type and record provenance.
    - Extract task context (codebase slice, docs, external knowledge) and fix scope.
    - Draft task input and expected output with clear acceptance criteria.
    - Assign difficulty across defined dimensions and justify the grade.
    - Define per-task metrics, scoring rules, and failure categories.
    - Review samples for realism and consistency, then freeze the sample set.
    - Independent function development: define isolated function scope, required interfaces, unit tests, and reference outputs.
    - New application development: define end-to-end app scope, module boundaries, deployment target, and acceptance tests.
    - Incremental feature development: define baseline repo state, feature delta, regression scope, and compatibility constraints.
 
 2. Baseline evaluation process (setup → run → trace → score).
    - Prepare a reproducible runtime, dependencies, and logging standard.
    - Execute tasks via manual or scripted runs with controlled prompts.
    - Capture raw outputs, tool logs, and intermediate artifacts.
    - Compute metrics, summarize results, and flag anomalies.
    - Archive run configurations and evidence for traceability.
    - Independent function development: run unit tests and local checks for correctness and edge cases.
    - New application development: run build, integration, and end-to-end checks with deployment validation.
    - Incremental feature development: run regression suites, dependency checks, and backward compatibility validation.
 
 3. Dataset + evaluation framework process (schema → process → aggregation).
    - Define dataset schema, required metadata, and difficulty label format.
    - Specify task packaging, versioning, and validation rules.
    - Design the evaluation workflow, including metric computation stages.
    - Define result aggregation logic and reporting-ready summaries.
    - Produce a minimal architecture diagram and interface contracts.
    - Define task templates for independent function, new application, and incremental feature categories.
 
 4. Report structure process (outline → evidence mapping → presentation).
    - Draft the report outline, section ownership, and required tables.
    - Map each conclusion to supporting metrics, samples, and artifacts.
    - Define chart and table standards for comparability.
    - Ensure the report aligns with dataset scope and framework outputs.
    - Separate result narratives for independent function, new application, and incremental feature tracks.
 
 #### Deliverables
 - A set of representative tasks with complete inputs, outputs, difficulty, and metrics.
 - Baseline evaluation results with reproducible artifacts.
 - A preliminary dataset + evaluation framework design document.
 - A report outline with conclusion-to-evidence mapping.
