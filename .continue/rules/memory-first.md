# Memory First Architecture

## Core Principle
Institutional Memory is the most important asset of Drader.

## Before Creating New Features, Ask
- Should this event be stored?
- Should this decision become institutional memory?
- Should this failure become DNA?

## Memory Hierarchy
1. `strategy_dna` — Immutable strategy definitions, versioned lifecycle
2. `experiment_dna` — Every backtest, validation, and paper-trading run
3. `failure_dna` — Post-mortems of stopped/abandoned strategies
4. `council_decisions` — Structured Council votes, rationales, overrides
5. `system_memory` — Workspace state, preferences, pipeline status

## Preferred Stack
- Supabase
- PostgreSQL
- pgvector (for embedding similarity search)

## Rules
- Every major workflow should write to memory.
- Never bypass DNA storage when persistence is required.
- Writes are immutable and timestamped.
- Always record the actor (Founder or specific Council agent).
- A full reconstruction must be possible from DNA alone.