# Independent Generation Evaluation Flow

```mermaid
graph TD
   A[Task intake and scope lock] --> B[Input assembly: independent task]
   B --> C[Run generation]
   C --> D[Compile/build]
   D --> E{Build succeeds}
   E -->|No| F[Mark as failed and record reason]
   E -->|Yes| G[Sample input validation]
   G --> H{Output correct}
   H -->|No| I[Mark as failed and record reason]
   H -->|Yes| J[Process metrics check]
   J --> K[Difficulty confirmation and record]
   K --> N[Final score and report archive]
```

## Detailed Steps

1. Task intake and scope lock: confirm independent-generation task, freeze scope and acceptance criteria.
2. Input assembly: collect task description, optional sample inputs/outputs, and code skeleton.
3. Run generation: execute the model with fixed prompt and produce code output.
4. Compile/build: directly compile or build the generated code; failure marks the case as failed.
5. Sample input validation: run provided sample inputs and compare with expected outputs; mismatch marks as failed.
6. Process metrics check: record and evaluate response time, token usage, and cost metrics.
7. Difficulty confirmation and record: confirm or adjust difficulty coefficient based on actual completion.
8. Final score and report archive: aggregate scores and archive evidence and results.
