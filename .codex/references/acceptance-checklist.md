# Acceptance Checklist

Use this file to decide whether the implementation is evaluator-ready.

## Global

- [ ] Repository runs locally with documented setup steps
- [ ] README explains setup, architecture, and design tradeoffs
- [ ] Tests run with `pytest`
- [ ] Domain models are typed and coherent
- [ ] LLM behavior is wrapped behind interfaces that are testable

## Part 1: Structured Extraction

- [ ] Template supports modules
- [ ] Template supports scalar fields
- [ ] Template supports table fields
- [ ] Template supports required flags
- [ ] Template supports locale
- [ ] Extraction output includes value plus metadata
- [ ] Metadata includes confidence, source location, and direct vs inferred flag
- [ ] Text-based and image-based inputs are both handled
- [ ] Malformed model output is handled safely
- [ ] Adversarial parser tests exist without calling a real LLM
- [ ] Table extraction does not hallucinate rows

## Part 2: Classification and Routing

- [ ] Classification returns type, confidence, language, authenticity, and normalized filename
- [ ] Routing distinguishes PDFs, images, scans, and spreadsheets
- [ ] Fallback strategy exists when primary extraction is weak
- [ ] Classification results are cached
- [ ] Edge-case tests cover weak text, screenshots, and multilingual files

## Part 3: Correction Chat Agent

- [ ] Scalar fields can be read and modified
- [ ] Table rows and cells can be added, edited, and removed
- [ ] Source documents can be searched or re-checked
- [ ] Current extraction state can be surfaced on demand
- [ ] Validation can run on demand
- [ ] Undo works for the latest mutations
- [ ] Large document sets use targeted retrieval instead of full-context stuffing
- [ ] UI shows chat, extraction state, validation issues, and undo

## Part 4: Validation Pipeline

- [ ] Validation is deterministic
- [ ] Required field rule exists
- [ ] Type-checking rule exists
- [ ] Confidence threshold rule exists
- [ ] Table minimum row rule exists
- [ ] Unknown field rule exists
- [ ] Issues include path, severity, rule name, and message
- [ ] Tests cover valid state plus failure modes

## Part 5: Real-Time Progress

- [ ] Progress events include phases, counts, snapshots, and errors
- [ ] Reconnection catches clients up without rerunning the job
- [ ] Keepalive events exist
- [ ] Streaming protocol is documented

## Design Notes Required In README

- [ ] Handling large documents beyond model context limits
- [ ] Rate limiting for concurrent users
- [ ] Strategies to reduce table hallucination
- [ ] Feedback loop for confidence calibration
