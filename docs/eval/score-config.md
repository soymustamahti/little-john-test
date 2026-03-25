# Score Config

These are the MVP scores we will use to evaluate the agents in this application.

## Scores

### 1. classification_label_correctness

- Type: `BOOLEAN`
- Values: `true | false`
- Description: checks whether the category selected by the classification agent is correct.

### 2. classification_novelty_decision

- Type: `CATEGORICAL`
- Categories:
  - `correct_reuse`
  - `correct_novelty`
  - `false_novelty`
  - `missed_novelty`
- Description: checks whether the agent was right to reuse an existing category or propose a new
  one.

### 3. extraction_required_field_accuracy

- Type: `NUMERIC`
- Min: `0`
- Max: `1`
- Description: measures the share of required fields extracted correctly.

### 4. extraction_evidence_coverage

- Type: `NUMERIC`
- Min: `0`
- Max: `1`
- Description: measures the share of filled fields that include usable evidence.

### 5. extraction_table_non_hallucination

- Type: `NUMERIC`
- Min: `0`
- Max: `1`
- Description: measures whether extracted table rows are actually supported by the document.

### 6. correction_request_success

- Type: `BOOLEAN`
- Values: `true | false`
- Description: checks whether the user's correction request was successfully satisfied.

### 7. correction_unintended_change_rate

- Type: `NUMERIC`
- Min: `0`
- Max: `1`
- Description: measures the proportion of changes that were not requested by the user.
