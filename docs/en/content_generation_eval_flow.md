 # Content Generation Evaluation Flow
 
```mermaid
graph TD
  A[Task intake and scope lock] --> B[Input assembly: direct + indirect]
  B --> C[Context validation: repo, version, files]
  C --> D[Generate output with fixed prompt]
  D --> E[Capture raw output, tool logs, artifacts]
  E --> F{Expected output available}
  F -->|Yes| G[Similarity check: exact + semantic]
  G --> Gs[Similarity score +/-]
  Gs --> H[Alternative correctness check if low similarity]
  H --> Hs[Necessity score +/-]
  F -->|No| X[No expected output: worst-case score applied]
  X --> I[Compile/build check]
  Hs --> I
  I --> Is[Build score +/-; fail skips tests]
  Is --> J[Static analysis check]
  J --> Js[Quality score +/-]
  Js --> L[Multi-step tests]
  L --> L1[Patch test: task-specific cases]
  L1 --> Ls1[Patch test score +/-]
  Ls1 --> L2[Fail-to-pass tests]
  L2 --> Ls2[Fail-to-pass score +/-]
  Ls2 --> L3[Pass-to-pass tests]
  L3 --> Ls3[Pass-to-pass score +/-]
  Ls3 --> T1[Independent-only: unit test focus]
  Ls3 --> T2[New app only: build + integration + e2e]
  Ls3 --> T3[Incremental only: regression + compatibility]
  T1 --> K[Process metrics check]
  T2 --> K
  T3 --> K
  K --> Ks[Process score +/-]
  Ks --> M[Difficulty confirmation and record]
  M --> N[Final score and report archive]
```

## Detailed Procedure
1. Task intake and scope lock: record task type, repo, version, and acceptance criteria.
2. Input assembly: consolidate direct inputs and required indirect context, then freeze the input set.
3. Context validation: verify file paths, dependencies, and reproducibility constraints.
4. Run generation: execute with a fixed prompt and controlled environment.
5. Evidence capture: store raw outputs, tool logs, and intermediate artifacts.
6. Expected output branch:
   - If expected output exists, run exact and semantic similarity checks and apply similarity score (+/-).
   - If similarity is low, validate whether the output is an acceptable alternative and apply necessity score (+/-).
   - If expected output does not exist, apply worst-case score and continue to the next tests.
7. Build/compile check: apply build score (+/-); failures skip tests.
8. Static analysis check: apply quality score (+/-) by issue thresholds.
9. Multi-step tests:
   - Patch tests: task-specific test cases, apply score (+/-).
   - Fail-to-pass tests: previously failing tests must pass, apply score (+/-).
   - Pass-to-pass tests: regression-free expectation, apply score (+/-).
   - Independent only: unit test focus.
   - New app only: build + integration + end-to-end.
   - Incremental only: regression + compatibility.
10. Process metrics check: token usage, response time, and cost thresholds apply score (+/-).
11. Difficulty confirmation: confirm or adjust difficulty label and log the rationale.
12. Final score and archive: consolidate recorded scores, output decision, and evidence.
