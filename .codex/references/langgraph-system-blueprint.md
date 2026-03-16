# LangGraph System Blueprint

This file records the current intended backend strategy for ingestion, retrieval, and correction.

## Core Decision

Use LangGraph as the orchestration backbone.

Instead of a single monolithic agent, structure the backend around multiple graphs or graph-backed
subsystems:

- ingestion graph
- retrieval graph
- correction graph
- validation and progress orchestration around them

## Ingestion Graph

The ingestion workflow begins when a user uploads a document.

Recommended high-level flow:

1. accept upload and create a document job
2. persist original file metadata
3. store the original file in R2
4. detect file type and route preprocessing
5. run OCR when needed
6. normalize extracted content into a canonical document representation
7. create retrieval chunks
8. generate embeddings
9. persist chunks, embeddings, and retrieval metadata
10. mark the document ready for downstream extraction and correction workflows

## OCR Strategy

Default OCR provider direction:

- use Mistral OCR for PDFs and images when OCR is required

What to persist from OCR:

- raw OCR provider response
- normalized page-level text
- page-level markdown or structured text if available
- page metadata such as page number, bounding boxes, and confidence signals when available

Reasoning:

- OCR is expensive and should be cached
- downstream extraction and retrieval should not need to rerun OCR
- retaining raw and normalized forms helps debugging and reprocessing

## Canonical Document Representation

After OCR or direct parsing, normalize every document into a canonical internal representation.

Suggested layers:

- document
- page or sheet
- block or section
- chunk

Keep provenance on each unit:

- source file id
- page or sheet identifier
- block or chunk identifier
- text content
- structural hints
- location metadata

## Chunking Strategy

Do not use one chunking strategy for every file type.

Preferred approach:

- PDFs and OCR-heavy documents: layout-aware chunking with page and section provenance
- Text-rich documents: semantic and heading-aware chunking
- Tables in documents: preserve table rows and columns where possible
- Spreadsheets: treat sheets, tables, and cell ranges as structured retrieval units instead of
  plain text chunks

Chunk requirements:

- enough text for retrieval quality
- enough locality to preserve provenance
- overlap only when it materially improves recall
- store chunk content and metadata separately from embeddings

## Embeddings and Search Storage

Recommended primary persistence:

- PostgreSQL
- pgvector for embeddings
- PostgreSQL full-text search or keyword indexes for lexical retrieval

This gives a coherent production-ready base for:

- semantic retrieval
- keyword retrieval
- metadata filtering
- durable storage

Persist at least:

- document metadata
- canonical content units
- chunks
- embeddings
- OCR outputs
- ingestion job records

## Hybrid Retrieval Strategy

The retrieval system should not rely on only one search mode.

Preferred retrieval path:

1. interpret user request
2. run keyword search
3. run semantic search
4. merge and deduplicate candidate results
5. rerank candidates
6. return evidence set to the agent

Keyword search is important for:

- exact names
- invoice numbers
- IDs
- dates
- short field labels

Semantic search is important for:

- paraphrased user requests
- loosely phrased fields
- descriptive document passages

## Reranking Strategy

Rerank after hybrid retrieval, not before.

Requirements:

- preserve provenance
- keep a compact evidence set
- allow multiple evidence fragments when a single chunk is insufficient
- prefer precision for correction workflows

A strong default is:

- hybrid recall first
- rerank second
- final evidence assembly third

## Deep Agent Direction

The retrieval and correction layer should use a deeper planning-capable agent architecture, not a
single short reasoning call.

Conceptually, the deep agent should:

- understand the user request
- decide which retrieval tools to call
- compare keyword and semantic evidence
- request more evidence when confidence is low
- inspect document passages, pages, or spreadsheet regions
- decide whether to answer, mutate state, re-check, or ask for clarification

Important note:

- The user referenced a LangGraph helper similar to `create_deep_agent`
- Until the exact documentation is provided, treat this as an architectural intention, not a fixed
  API dependency
- If the official helper fits later, use it
- If not, implement the same behavior with a plan-execute-review LangGraph design

## Correction Graph

The correction experience should be graph-backed as well.

Expected tool families:

- search by keyword
- search by semantic similarity
- rerank and inspect evidence
- inspect page or sheet region
- read current extraction state
- update field value
- add, edit, or remove table rows
- rerun validation
- undo mutation

The correction graph should keep:

- mutation history
- validation after each change
- explanation of what changed
- source evidence when applicable

## File-Type Routing Expectations

Support these branches:

- PDFs with extractable text
- scanned PDFs and images requiring OCR
- spreadsheets such as Excel files
- Google Sheets through a future adapter or import flow

Routing guidance:

- spreadsheets should use structured parsers before any chunking-for-text workflow
- image-heavy documents should OCR first
- near-empty extracted text should trigger OCR fallback

## External Services

Current expected external integrations:

- Mistral OCR for OCR
- R2 for original file storage
- PostgreSQL with pgvector for persistence and vector search

Keep all provider interactions behind adapters so credentials and provider choices can be swapped
without rewriting the core logic.

## Opinionated Recommendation

For this project, the strongest production-ready path is:

- PostgreSQL plus pgvector for metadata, chunks, and embeddings
- PostgreSQL full-text search for keyword retrieval
- R2 for originals and possibly derived artifacts
- Mistral OCR as the ingestion OCR layer
- LangGraph orchestration for ingestion, retrieval, and correction

This is stronger than introducing many separate systems too early, because it keeps the architecture
cohesive while still feeling production-grade.
