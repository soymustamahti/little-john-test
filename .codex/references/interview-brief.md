# Interview Brief

## Objective

Build a prototype platform that extracts structured data from uploaded documents such as invoices,
contracts, purchase orders, receipts, identity documents, bank statements, and similar files.

The user workflow is:

1. Define a template that describes what data to extract
2. Upload one or more documents
3. Classify each document and route it through the right processing path
4. Extract structured data with quality metadata
5. Let the user review and correct the results through chat
6. Export the final structured data

## Core Constraints

- Time budget: about 8 hours
- Stack: Python 3.12+
- Deliverable: GitHub repository with working code and README
- No database required
- In-memory structures or JSON persistence are acceptable

## Part 1: Structured Extraction

Implement:

- Template model with logical modules
- Scalar fields: string, number, date, boolean
- Table fields with typed columns
- Required field markers
- Locale support: `en` and `fr`

Extraction output must include:

- Structured data matching the template
- Per-field confidence score from `0` to `1`
- Source location in the document
- Whether the value was directly extracted or inferred

Robustness requirements:

- Handle text documents and image-based input
- Handle malformed LLM output gracefully
- Test resilience against adversarial LLM output without calling a real LLM
- Table extraction must not hallucinate rows

## Part 2: Document Classification and Routing

Classification must determine:

- Document type
- Confidence
- Detected language
- Authenticity assessment
- Suggested normalized filename

Routing must support:

- Text-extractable PDFs
- Images that require vision
- Scanned documents with little extractable text
- Spreadsheets with already structured data
- Fallback strategies when primary extraction is weak
- Classification caching so the same document is not classified twice

## Part 3: Correction Chat Agent

The agent must:

- Read and modify scalar fields
- Add, remove, and edit table rows and cells
- Search documents and verify source passages
- Show current extraction state
- Run validation on demand
- Undo previous changes

Additional constraints:

- Support small document sets by sending the full context
- Support large document sets by searching or retrieving passages on demand
- Every mutation must be undoable
- Surface validation issues after each change

UI expectations:

- Chat interface
- Visible extraction state
- Visible validation issues
- Undo action
- Streaming responses are a bonus

## Part 4: Validation Pipeline

Validation must be deterministic and not rely on an LLM.

Rules to support:

- Required fields present
- Declared type correctness
- Low-confidence warnings with severity levels
- Minimum table row counts
- Detection of unknown fields not present in the template

Each issue must include:

- Field path
- Severity
- Rule name
- Human-readable message
- Optional suggested action

## Part 5: Real-Time Progress

Long-running extraction requires progress streaming.

Events should include:

- Phase changes
- Progress counts
- State snapshots
- Errors

The protocol must support:

- Client reconnection
- Replay of missed events
- Keepalive events during long-running LLM calls

## Deliverables

- Working repository
- README with setup and design decisions
- Dependencies in `pyproject.toml` or `requirements.txt`
- Tests runnable with `pytest`
- Design notes answering:
  - Handling 200-page documents
  - Rate limiting with many concurrent users
  - Reducing table hallucination
  - Improving confidence calibration over time
