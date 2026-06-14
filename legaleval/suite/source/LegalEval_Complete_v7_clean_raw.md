
LegalEval
Complete Framework, Prompt Suite & Scoring Rubrics
End-to-End Evaluation Framework for LLM Legal Tasks
Rubrics revised per v2 fixes · Weights redesigned to prioritize factuality
2026

>

>HOW TO USE THIS DOCUMENT
Part I (Sections 0–6) — the benchmark design framework, philosophy, dataset mapping, and scoring system.
Part II (Sections 7–11) — the real-source prompt test suite: 14 prompts with contract text and corrected rubrics.
Rubric fixes from v2 are incorporated inline; changed elements are flagged with RUBRIC FIX (v2) boxes.
Scoring weights have been redesigned throughout: Faithfulness and Directionality are now the load-bearing gates. v7 makes instruction specificity a controlled variable: detection/diagnosis prompts (A1, A2, C2) now carry OPEN (headline) and DIRECTED variants, B3 carries an honesty-instruction A/B, open-variant grading and clean-instance controls are defined in §6.2a, and every gold judgment unit carries a stable ID.
	||CELL||
>

>

>PART I — BENCHMARK FRAMEWORK
	||CELL||
>
0. How This Eval Differs from LegalBench & BigLaw Bench
LegalBench is the leading academic benchmark for legal reasoning in LLMs — 162 tasks across six reasoning categories (issue-spotting, rule-recall, rule-conclusion, rule-application, interpretation, and rhetorical understanding), contributed by 40 researchers from 36 corpora. It is the right tool for measuring whether a model understands law.

This eval measures something different: whether a model can do a lawyer's job. The distinction matters.

>

>Dimension
	||CELL||LegalBench
	||CELL||LegalEval (This Eval)
	||CELL||
>Task type
	||CELL||Mostly binary / multi-class classification; some extraction & generation
	||CELL||Open-ended generation across full workflow stages (redline, draft, negotiate)
	||CELL||
>Legal domain
	||CELL||Broad: statutes, case law, contracts, civil procedure, evidence
	||CELL||Narrow & deep: commercial contracts only (NDA, SaaS, MSA, M&A, Employment, Vendor)
	||CELL||
>Workflow orientation
	||CELL||Discrete, atomic tasks — no chaining
	||CELL||Pipeline-first: tasks chain A→B→C→D→E to simulate a full deal
	||CELL||
>Primary skill tested
	||CELL||Legal reasoning & knowledge recall
	||CELL||Practical lawyering: issue-spotting, drafting, redlining, negotiation triage
	||CELL||
>Ground truth format
	||CELL||Classification labels (Yes/No, extracted span)
	||CELL||Multi-dimensional rubric: Faithfulness & Directionality (gates) + Coverage, Soundness, Actionability (graded)
	||CELL||
>Hallucination testing
	||CELL||Implicit (wrong classification = hallucination)
	||CELL||Explicit: planted-issue tasks and fabricated-citation detection baked into rubric
	||CELL||
>Adversarial component
	||CELL||None
	||CELL||Stage E: multi-round negotiation simulation with opposing-counsel counter-redlines
	||CELL||
>Scale
	||CELL||162 tasks, 36 corpora
	||CELL||200 tasks, 6 contract types, 4 source datasets + EDGAR synthesis
	||CELL||
>Practitioner alignment
	||CELL||Research — IRAC framework
	||CELL||Real workflows — maps to billable-hour task types (per BigLaw Bench)
	||CELL||
>

>

>CORE PRINCIPLE
LegalBench tells you if a model knows the law. LegalEval tells you if a model can work as a first-year associate on a commercial deal. These are correlated but not equivalent — and the gap is where legal AI products live.
	||CELL||
>

Why the Gap Exists
LegalBench tasks are largely classification problems: given a clause, does it contain X? Given a fact pattern, does it trigger rule Y? Real legal work involves open-ended generation under constraints: redline this to favor our client, draft a replacement clause, tell me whether this deal can close. The output format difference — Yes/No vs. a marked-up clause — creates a fundamentally different evaluation problem requiring rubric-based grading rather than label matching.

>

>DESIGN NOTE
Recommendation: Run LegalBench as a calibration layer (fast, automatable). Use LegalEval for product-readiness decisions where real workflow performance is the standard.
	||CELL||
>

The Other Reference Point: BigLaw Bench
LegalBench is the academic anchor; BigLaw Bench (Harvey AI) is the industry one, and it is the closer cousin. Both LegalEval and BigLaw Bench start from the same premise — tasks should mirror real billable work, not academic exercises — and both grade against expert-annotated ground truth with positive points for meeting requirements and negative points for errors such as hallucination. The headline BigLaw Bench metric, the share of a lawyer-quality work product a model completes, is exactly the spirit LegalEval's Coverage and Soundness dimensions aim at.

Where they diverge is scope and instrumentation. BigLaw Bench's public surface centers on extraction and answer-quality at scale — its flagship workflow set extracts deal points from Share Purchase Agreements, scored field-by-field against a fixed schema, with non-text fields graded by exact match and text fields by a model grader validated against attorneys. That field-level schema is powerful precisely because it is granular and reusable: each deal point is an independently checkable unit with its own ground truth. LegalEval borrows that granularity but pushes it across the full lifecycle — issue-spotting, redlining, drafting, negotiation — rather than concentrating on extraction, and it makes the adversarial step (opposing-counsel counter-redlines, deal-viability synthesis) a first-class stage that BigLaw Bench's public sets do not cover.

>

>Dimension
	||CELL||BigLaw Bench (public)
	||CELL||LegalEval
	||CELL||
>Center of gravity
	||CELL||Extraction & answer-quality at scale (e.g. SPA deal-point schema)
	||CELL||Full workflow A–E, weighted toward redlining & negotiation
	||CELL||
>Ground-truth unit
	||CELL||Field-level schema entries, attorney-verified
	||CELL||Per-criterion gold sets per prompt (planted issues, expected edits, triage calls)
	||CELL||
>Headline metric
	||CELL||% of lawyer-quality work product completed; points minus error deductions
	||CELL||Gate-adjusted dimension scores; fabrication / wrong-party failures capped, not just deducted
	||CELL||
>Adversarial / multi-party
	||CELL||Not in the public sets
	||CELL||Stage E: counter-redline triage and deal-viability synthesis
	||CELL||
>Grader
	||CELL||Exact match for typed fields; model grader (attorney-validated) for text
	||CELL||Same philosophy — deterministic where possible, validated LLM grader elsewhere
	||CELL||
>Source material
	||CELL||Real SPAs from SEC + Harvey collections
	||CELL||Real SEC filings + CUAD / ContractNLI / ACORD / MAUD annotations
	||CELL||
>

The deliberate design choice LegalEval shares with BigLaw Bench's schema approach is granularity: every prompt resolves into discrete, independently-checkable units of judgment — a specific planted issue, a specific expected edit, a specific accept/reject/counter call — each with its own gold answer. That granularity is what lets the grader be decomposed and validated (see §6.5), and it is also what makes each task far more than a single pass/fail score: a task is really a bundle of labeled, reusable judgment units. BigLaw Bench demonstrated the value of that structure for extraction; LegalEval extends it to generation and advocacy.

>

>DESIGN NOTE
Net positioning: LegalBench measures legal knowledge. BigLaw Bench measures, at scale, how much of a defined work product a model completes — strongest on extraction. LegalEval measures whether a model can be trusted across the full contract lifecycle including adversarial steps, with a scoring model that treats fabrication and wrong-party advocacy as disqualifying rather than merely costly.
	||CELL||
>

1. Overview & Philosophy
This benchmark evaluates LLM performance on tasks a legal clerk or junior associate performs day-to-day — not raw legal knowledge, but the practical, automatable work that currently consumes a lawyer's billable hours.

The Focus: Real Workflow
Reading and ingesting contracts to identify issues
Summarizing documents into structured, actionable briefs
Redlining — suggesting edits to language, flagging risks, making contracts favorable or legally sound
Drafting new clauses or full agreements from instructions
Simulating back-and-forth negotiation between opposing counsel

>

>CORE PRINCIPLE
Each stage maps to a real step in a lawyer's day. Tasks run standalone OR chain end-to-end, so the eval captures both atomic capability and multi-step reasoning across a full contract lifecycle.
	||CELL||
>

A Second Design Principle: Decomposable, Reusable Tasks
Beyond fidelity to real work, every task is built to decompose into small, independently-labeled units of judgment — a single planted issue, a single expected edit, a single accept/reject/counter call — each carrying its own gold answer and its own pass/fail. A prompt is therefore not one opaque score but a structured bundle of labeled criteria over a known source document.

This is deliberate. Granular per-criterion labels are what let the grader be decomposed and validated rather than asked for a holistic verdict (see §6.5); they make partial credit meaningful instead of arbitrary; and they turn each task into a reusable, recombinable unit rather than a one-off. The same structure that makes a task gradeable also makes it a clean, well-specified specimen of legal reasoning — source, criteria, gold answers, and known failure modes all attached — which pays off well beyond a single scoring run. Design tasks so that the unit of measurement is the individual judgment, not the whole response.

A Third Design Principle: The Eval as a Generalizable Environment
The first two principles — fidelity to real work, and decomposition into reusable judgment units — combine into a third that governs how the suite scales: LegalEval is built as an environment, not a fixed dataset. What stays fixed is the task structure, the judgment units, and the grading contract; what varies is the instance — the individual contract under the lens. Each task is bound to contract structure (“whether a survival clause is present,” “the liability cap,” “which party each absence favors”), never to a specific named document, so the same task can be re-run on a new contract, a perturbed one, a synthetic one, or a confidential one a client supplies — with no change to the scoring logic.
The rule that makes this work is that the contract text presented in a prompt is the sole authoritative source of fact for that instance. Gold answers are derived from the instance as presented, never from an external or “real” version of the document. A claim is true if it is true of the prompt instance and false if it contradicts the prompt instance; it is neither rewarded nor penalized for matching some document that lives outside the prompt. Grading therefore never depends on whether a model has memorized a public corpus — a model that has the contract in its training data gains nothing it could not get by reading the prompt, and loses nothing for knowing too much.
This is what lets one rubric serve both public and private data with no per-source branching. Public filings carry a contamination channel — a model may recall the real document — which the suite neutralizes by perturbing the gold-bearing identifiers (see §6.2) so the instance has no real-world twin for the facts that matter. Private or synthetic contracts have no public ground truth to recall, so the same instance-as-truth rule applies unchanged. Provenance affects how an instance is prepared (whether perturbation is applied), not how it is scored.
Two capabilities follow directly. Because the correct answer for an instance is a function of that instance’s structure, new synthetic contracts can be generated into any existing task with only instance-level labeling, and instance–gold pairs can be produced and checked programmatically — letting grader strictness, gate thresholds, and difficulty be calibrated automatically, with humans reserved for spot-checks and the hard tail rather than relabeling every contract. An eval whose gold answers point at external real documents can do neither; prompt-as-ground-truth is what keeps the environment generative rather than static.

Pipeline Overview

>

>Stage
	||CELL||Workflow Step
	||CELL||What It Tests
	||CELL||
>A
	||CELL||READ → Identify Issues
	||CELL||Coverage, precision, hallucination resistance
	||CELL||
>B
	||CELL||EXTRACT → Summarize
	||CELL||Structured output, compression, completeness
	||CELL||
>C
	||CELL||REDLINE → Suggest Edits
	||CELL||Directional editing, legal reasoning, consistency
	||CELL||
>D
	||CELL||DRAFT → Write from Scratch
	||CELL||Zero-to-draft quality, scoped writing
	||CELL||
>E
	||CELL||NEGOTIATE → Back-and-Forth
	||CELL||Multi-doc reasoning, triage, compromise
	||CELL||
>

2. Eval Stages & Task Inventory
Stage A — Document Ingestion & Issue Spotting

>

>Task
	||CELL||Description
	||CELL||What's Tested
	||CELL||
>A1
	||CELL||Given an NDA, list every clause that is missing or incomplete
	||CELL||Coverage, issue recall
	||CELL||
>A2
	||CELL||Given an MSA with planted problematic clauses, surface the most significant concerns (the open variant asserts neither existence nor count)
	||CELL||Precision; hallucination resistance
	||CELL||
>A3
	||CELL||Given two contract versions, diff and summarize what changed and why it matters
	||CELL||Comparison; materiality judgment
	||CELL||
>A4
	||CELL||Flag any clause that is ambiguous or could be interpreted two ways
	||CELL||Linguistic precision
	||CELL||
>A5
	||CELL||Read a contract and identify which party each clause favors
	||CELL||Bias detection; legal reasoning
	||CELL||
>

Stage B — Summarization & Extraction

>

>Task
	||CELL||Description
	||CELL||What's Tested
	||CELL||
>B1
	||CELL||Extract all defined terms and produce a verbatim glossary
	||CELL||Extraction accuracy; verbatim fidelity
	||CELL||
>B2
	||CELL||Summarize obligations for Party A vs B in a table
	||CELL||Structured output; completeness
	||CELL||
>B3
	||CELL||Given a 40-page SaaS agreement, produce a 1-page executive summary
	||CELL||Compression; no hallucination
	||CELL||
>B4
	||CELL||Extract all deadlines, notice periods, and time-sensitive clauses
	||CELL||Recall of specific clause types
	||CELL||
>B5
	||CELL||Given an amendment, summarize what it changes vs. the base agreement
	||CELL||Delta summarization
	||CELL||
>

Stage C — Redlining & Suggested Edits

>

>Task
	||CELL||Description
	||CELL||What's Tested
	||CELL||
>C1
	||CELL||Given an indemnification clause, rewrite it to favor the vendor
	||CELL||Directional redlining
	||CELL||
>C2
	||CELL||Given an uncapped liability clause, identify the gap and fix it
	||CELL||Issue-to-fix pipeline
	||CELL||
>C3
	||CELL||Given a non-compete, identify enforceability issues and fix
	||CELL||Factual legal reasoning
	||CELL||
>C4
	||CELL||Redline a termination clause to add mutual termination for convenience
	||CELL||Clause-level rewriting
	||CELL||
>C5
	||CELL||Given a clause with incorrect defined-term usage, catch and correct
	||CELL||Internal consistency
	||CELL||
>

Stage D — Drafting from Instructions

>

>Task
	||CELL||Description
	||CELL||What's Tested
	||CELL||
>D1
	||CELL||Draft an NDA from a one-paragraph business description
	||CELL||Zero-to-draft quality
	||CELL||
>D2
	||CELL||Given a term sheet, draft the contract clause by clause
	||CELL||Term sheet to contract
	||CELL||
>D3
	||CELL||Draft a notice of breach letter from contract + described violation
	||CELL||Applied drafting; factual precision
	||CELL||
>D4
	||CELL||Write a governing law and dispute resolution clause for a US-UK deal
	||CELL||Jurisdiction awareness
	||CELL||
>D5
	||CELL||Draft an amendment that changes payment terms only
	||CELL||Scoped drafting; no scope creep
	||CELL||
>

Stage E — Negotiation Simulation

>

>Task
	||CELL||Description
	||CELL||What's Tested
	||CELL||
>E1
	||CELL||Given your redline and opposing counter, identify open issues
	||CELL||Multi-doc reasoning
	||CELL||
>E2
	||CELL||Given 3-round negotiation history, summarize trajectory and open issues
	||CELL||Longitudinal tracking
	||CELL||
>E3
	||CELL||Opposing counsel rejected your liability cap — draft a compromise
	||CELL||Negotiation reasoning
	||CELL||
>E4
	||CELL||Given a counter-redline with 10 changes, classify each: accept/reject/counter
	||CELL||Triage judgment
	||CELL||
>E5
	||CELL||Given both parties' must-haves, determine whether a deal is possible
	||CELL||Logical synthesis
	||CELL||
>

3. Dataset Distribution (200 Tasks)
By Eval Stage

>

>Stage
	||CELL||Focus
	||CELL||Task Count
	||CELL||% of Dataset
	||CELL||
>A — Issue Spotting
	||CELL||Read, find problems
	||CELL||40
	||CELL||20%
	||CELL||
>B — Summarization
	||CELL||Extract, compress, structure
	||CELL||40
	||CELL||20%
	||CELL||
>C — Redlining
	||CELL||Suggest edits, rewrite clauses
	||CELL||50
	||CELL||25%
	||CELL||
>D — Drafting
	||CELL||Write from scratch or from brief
	||CELL||40
	||CELL||20%
	||CELL||
>E — Negotiation
	||CELL||Multi-round, opposing counsel
	||CELL||30
	||CELL||15%
	||CELL||
>

Redlining receives the largest allocation (25%) because it is the most common billable task in commercial contract work and the hardest for models to get directionally correct.

By Contract Type

>

>Contract Type
	||CELL||Examples
	||CELL||Task Count
	||CELL||%
	||CELL||
>NDA / Confidentiality
	||CELL||Mutual NDA, one-way NDA
	||CELL||40
	||CELL||20%
	||CELL||
>SaaS / Software Licensing
	||CELL||Enterprise SaaS, API license
	||CELL||50
	||CELL||25%
	||CELL||
>MSA / SOW
	||CELL||Professional services, consulting
	||CELL||40
	||CELL||20%
	||CELL||
>Employment / Non-Compete
	||CELL||Offer letters, IP assignment
	||CELL||30
	||CELL||15%
	||CELL||
>M&A / LOI
	||CELL||Merger agreements, letters of intent
	||CELL||20
	||CELL||10%
	||CELL||
>Vendor / Procurement
	||CELL||Supply agreements, POs
	||CELL||20
	||CELL||10%
	||CELL||
>

4. Source Datasets
Tier 1: Core Contract Datasets
CUAD — Contract Understanding Atticus Dataset

>

>Attribute
	||CELL||Details
	||CELL||
>Size
	||CELL||510 commercial legal contracts; 13,000+ expert-annotated labels
	||CELL||
>Clause Types
	||CELL||41 types: indemnification, limitation of liability, termination, non-compete, IP ownership, and more
	||CELL||
>Use Cases
	||CELL||Stage A (issue spotting), Stage C (redlining) — ground-truth clause locations included
	||CELL||
>Source
	||CELL||huggingface.co/datasets/dvgodoy/CUAD_v1_Contract_Understanding_PDF
	||CELL||
>

MAUD — Merger Agreement Understanding Dataset

>

>Attribute
	||CELL||Details
	||CELL||
>Size
	||CELL||47,457 annotations from 152 public merger agreements
	||CELL||
>Source
	||CELL||SEC EDGAR — real, executed public contracts
	||CELL||
>Coverage
	||CELL||92 reading comprehension questions across deal points (ABA 2021 Study)
	||CELL||
>Use Cases
	||CELL||Stage B (extraction), Stage E (negotiation), Stage D (M&A clause drafting)
	||CELL||
>Link
	||CELL||atticusprojectai.org/maud
	||CELL||
>

ContractNLI

>

>Attribute
	||CELL||Details
	||CELL||
>Size
	||CELL||607 annotated NDAs with span-level evidence labels
	||CELL||
>Task Type
	||CELL||Given a hypothesis (e.g., 'obligations survive termination'), classify: entailed / contradicted / neutral
	||CELL||
>Use Cases
	||CELL||A2 (finding planted issues), A4 (ambiguity detection), B5 (amendment deltas)
	||CELL||
>Link
	||CELL||arxiv.org/abs/2110.01799
	||CELL||
>

ACORD — Atticus Clause Retrieval Dataset

>

>Attribute
	||CELL||Details
	||CELL||
>Size
	||CELL||114 queries; 126,000+ query-clause pairs rated 1–5 stars
	||CELL||
>Focus Clauses
	||CELL||Limitation of Liability, Indemnification, Change of Control, Most Favored Nation
	||CELL||
>Use Cases
	||CELL||Stage D (precedent-based drafting), Stage C (finding the right redline baseline)
	||CELL||
>Link
	||CELL||arxiv.org/abs/2501.06582
	||CELL||
>

Tier 2: Benchmarks to Study

>

>Benchmark
	||CELL||What It Offers
	||CELL||How to Use It
	||CELL||
>LegalBench (HuggingFace)
	||CELL||162 tasks across 6 reasoning categories; binary/multi-class classification, extraction, generation
	||CELL||Use as calibration layer before running LegalEval
	||CELL||
>BigLaw Bench (Harvey AI)
	||CELL||Tasks derived from actual billable time entries — closest to real legal work
	||CELL||Calibrate difficulty and realism; study their rubric methodology
	||CELL||
>Harvey Legal Agent Benchmark
	||CELL||Multi-step, long-horizon tasks (full deal-team memo with risk mapping)
	||CELL||Aspirational target for end-to-end chain evals
	||CELL||
>

5. Dataset-to-Stage Mapping

>

>Stage
	||CELL||Primary Dataset
	||CELL||Secondary / Supplement
	||CELL||
>A — Issue Spotting
	||CELL||CUAD (41 clause type labels)
	||CELL||ContractNLI (entailment / contradiction)
	||CELL||
>B — Summarization
	||CELL||MAUD (deal point Q&A), CUAD
	||CELL||EDGAR raw docs for long-form compression
	||CELL||
>C — Redlining
	||CELL||CUAD (clause locations) + ACORD (precedent retrieval)
	||CELL||EDGAR for real redline examples
	||CELL||
>D — Drafting
	||CELL||ACORD (precedent-based), MAUD (term sheet to clause)
	||CELL||EDGAR executed contracts as quality target
	||CELL||
>E — Negotiation
	||CELL||MAUD deal points, EDGAR M&A rounds
	||CELL||Synthesized: Claude generates opposing-counsel redlines
	||CELL||
>

Recommended Build Path (200 Tasks)
CUAD — Pull 50+ contracts; use 41 clause labels as issue-spotting ground truth for Stages A and C.
MAUD — Use deal point Q&A pairs as Stage B extraction tasks; M&A provisions for Stage E.
EDGAR — Pull 10–15 real executed contracts per type for Stages C and E.
Synthesize — Use Claude to generate planted errors and counter-redlines on top of real clauses. Have a lawyer validate all synthetic tasks before inclusion.

6. Scoring System
This section was substantially revised in v3. Three changes: (1) the dimension set is reorganized to fit the task better — Consistency is dissolved into the others and a Soundness dimension is added; (2) a gate-then-grade mechanic replaces flat weighting so that catastrophic failures cannot be offset by volume; (3) grading is moved off humans and onto a validated LLM grader, with humans repurposed to calibration and audit.

6.1 The Refined Dimension Set
The earlier rubric used five dimensions (Coverage, Precision, Directionality, Consistency, Actionability). Two problems: Consistency only applied to a handful of prompts and overlapped heavily with Precision and Coverage; and nothing directly measured whether the legal reasoning was actually correct — a model could catch the right issue, invent nothing, favor the right party, and still propose a fix that does not work. The revised set fixes both.

>

>Dimension
	||CELL||Max
	||CELL||Role
	||CELL||What It Measures
	||CELL||Replaces / Change
	||CELL||
>Faithfulness
	||CELL||0–3
	||CELL||GATE
	||CELL||No false or misattributed claims: no invented clauses, citations, or numbers, and nothing attributed to the document that it does not contain; accurate quotation of source; calibrated uncertainty on terms the document does not determine (do not state a guess as fact). A true statement is never a Faithfulness failure, even if it draws on knowledge outside the excerpt — what fails is falsity, or claiming the document says something it does not.
	||CELL||Broadened from 'Precision'
	||CELL||
>Directionality
	||CELL||0–4
	||CELL||GATE
	||CELL||Serves the named client's interest; does not go neutral when advocacy is required; does not advocate against the client
	||CELL||Unchanged in spirit
	||CELL||
>Coverage
	||CELL||0–4
	||CELL||Graded
	||CELL||Caught the material issues; no significant omissions against the gold set
	||CELL||Unchanged
	||CELL||
>Soundness
	||CELL||0–3
	||CELL||Graded
	||CELL||The legal reasoning and proposed fixes are correct and would actually work — enforceable, addresses the stated risk, internally consistent, correct use of defined terms
	||CELL||NEW (absorbs Consistency)
	||CELL||
>Actionability
	||CELL||0–2
	||CELL||Graded
	||CELL||Usable as-is: correct artifact format, specific proposed language not description, prioritized
	||CELL||Unchanged
	||CELL||
>

Maximum where all five apply: /16. Consistency no longer appears as its own line — verbatim-quotation fidelity now lives under Faithfulness, and correct defined-term usage lives under Soundness. This removes the awkward dimension that only sometimes applied and adds the one quality the task most needs but the old rubric never scored: is the law actually right.

6.2 Gate-Then-Grade
Legal work product has asymmetric risk. A missed issue is recoverable in review. A fabricated clause or wrong-party advice that gets relied on is a liability event — actively worse than no work product at all. Flat weighting cannot express this: under pure point-summing, a comprehensive, well-formatted answer that argues for the wrong party can still out-score a modest but correct one. That is the wrong ranking for this task.

>

>CORE PRINCIPLE
Faithfulness and Directionality are gates, not just weights. If a response fails either gate, its normalized prompt score is capped at 0.40 regardless of how well it scores elsewhere. A beautiful, comprehensive answer that hallucinates a clause or advocates against the client is a failing answer.
	||CELL||
>

Gate vs. graded quality — what the distinction means and why it's here
Every dimension answers a question about the response, but the two kinds answer fundamentally different questions, and the scoring has to treat them differently.

>

>
	||CELL||Gate quality
	||CELL||Graded quality
	||CELL||
>The question it asks
	||CELL||Is this response safe to rely on at all?
	||CELL||How good is this response, given that it's safe?
	||CELL||
>Failure type
	||CELL||Disqualifying — the kind of error that makes a lawyer stop trusting the output entirely
	||CELL||Degrading — the kind of error that makes the output less useful but still a usable starting point
	||CELL||
>Examples
	||CELL||Invented a clause; cited a section that doesn't exist; redlined for the opposing party
	||CELL||Missed a secondary issue; clunky formatting; a fix that's correct but verbose
	||CELL||
>How it scores
	||CELL||Binary check that caps the whole prompt score if failed
	||CELL||Continuous 0–max contribution, summed and normalized
	||CELL||
>Why
	||CELL||More volume cannot offset it — a confident wrong answer is worse than a thin right one
	||CELL||More of it is straightforwardly better; partial credit is meaningful
	||CELL||
>

The reason gates exist as a separate mechanism — rather than just giving Faithfulness and Directionality heavy weights — is that weighting is additive and gating is not. Under heavy weighting, a model that fabricates one clause but nails everything else can still post a high score; the fabrication is merely expensive. That produces a ranking that rewards fluent, comprehensive, confidently-wrong output, which is the single most dangerous failure mode for legal AI and the hardest for a downstream user to catch. A gate makes the failure disqualifying instead of expensive: it says this response does not count as competent work, full stop, no matter how much else it got right. Graded qualities, by contrast, behave well under addition — more coverage, more soundness, more usability are each monotonically good, so summing them is the right model.
FAITHFULNESS — WHAT COUNTS AS A HALLUCINATION (v5.1)
Faithfulness tests fidelity, not omniscience. A claim is a hallucination only if it is asserted as fact and is either false or unverifiable, OR if it misattributes to the document something the document does not contain. A true statement never fails Faithfulness, even when it draws on knowledge outside the provided excerpt. This reframes “grounding” from confinement (never leave the text) to attribution (do not claim the text says what it does not): a model may use correct outside knowledge — and doing so can help Coverage and Actionability — as long as it does not dress an outside fact up as a quote from the document, or state a guess as fact.
Three cases, one rule: (1) inventing a clause, citation, or number that is false — FAILS; (2) recalling a true fact about the real document that is not in the excerpt — PASSES, it is correct; (3) saying “the contract provides X” when it does not, whether or not X is true — FAILS, that is misattribution. Only (1) and (3) are hallucinations.
Why this stays cheap to grade (the construction half): instead of verifying every outside claim against the world, remove the divergence at the source. Perturb ONLY the gold-bearing identifiers — the party names, jurisdiction, and figures the gold makes a claim about — and keep the real clause language everywhere else. Once those facts are fictional, the document has no real-world twin for the facts that matter, so “supported by the source” and “true” coincide: the grader needs no external lookup, and a strict gate still never punishes recall because there is nothing real to recall. Genuinely verbatim prompts (B1, B2, D3) keep their real text; the modified-from-real prompts (A1, A2, B3, C3, E1) get the perturbation.
Net: true recall is safe (the property you want), grading stays lookup-free, and real clause language is preserved — without having to choose between “loosen Faithfulness” and “go fully synthetic.” The one remaining build step is the surgical perturbation of the five modified-from-real prompts.Net: true recall is safe (the property you want), grading stays lookup-free, and real clause language is preserved — without having to choose between “loosen Faithfulness” and “go fully synthetic.” (v6) The surgical perturbation has now been applied to all five modified-from-real prompts (A1: Calidon/Sferex; A2, B3, C3, E1: Kelmont/Spireline); B1/B2 retain verbatim text with header party names relabeled; D3's party names were fictionalized to match.

>

>NOTE
A useful way to read the two types: gate qualities define the floor (is this trustworthy?), graded qualities define the ceiling (how much value did it add?). A response has to clear the floor before its ceiling matters. This separation also keeps each judgment clean and independently checkable — the floor checks and the value checks don't blur into one fuzzy quality score, which matters both for grader reliability and for getting a precise, per-criterion record of exactly where and how a given response succeeded or failed.
	||CELL||
>

>

>Gate
	||CELL||Trips when…
	||CELL||Effect
	||CELL||
>Faithfulness gate
	||CELL||The response asserts as fact something that is false or unverifiable, or claims the document says something it does not — an invented clause, a fabricated citation, a made-up figure (e.g., inventing a specific §12.02 cap amount), or misattributing a term to the document. A true statement does NOT trip the gate, even if it draws on knowledge outside the excerpt; only falsity or misattribution does.
	||CELL||Normalized prompt score capped at 0.40
	||CELL||
>Directionality gate
	||CELL||On an advocacy task, the response advocates for the wrong party — a wrong-direction edit on C1, recommending Calidon add a standstill on A1, or ACCEPT on E1 Change 7. The gate fires only on UNAMBIGUOUS wrong-party advocacy — an edit or recommendation that demonstrably helps the counterparty. Defensible positions (e.g. recommending a return/destruction or injunctive-relief clause, which sophisticated real parties routinely include) are at most a minor Directionality deduction, never a gate trip.
	||CELL||Normalized prompt score capped at 0.40
	||CELL||
>

Procedure per prompt: (1) score all applicable dimensions to get a raw total; (2) normalize to the prompt's stated max; (3) if either gate tripped, cap the normalized score at 0.40 and flag the trip in the report. The 0.40 cap is a parameter — tighten toward 0.25 if you want gates to dominate ranking, loosen toward 0.50 if you want them to be a strong penalty rather than a near-zero.

Source-Agnostic Grading: Grade the Instance, Not the World
The dimension definitions above are deliberately source-agnostic: every gate and every graded point is scored against the contract as presented in the prompt instance, never against any document, corpus, or fact that lives outside the prompt. This is the grading-side expression of the environment principle in §1 — grade the instance, not the world — and it is what lets the identical rubric and grader contract apply to public filings, perturbed prompts, synthetic contracts, and confidential client documents without per-source branching.
Perturbation is what makes this safe for public-sourced prompts, and it comes with a guarantee. Let a perturbation relabel surface identifiers (party names, dates, jurisdiction, figures) and be structure-preserving — it adds or removes no clause. Applied jointly to the prompt and the gold key, in the same namespace, the achievable score is invariant to it: a model reading the perturbed prompt and reasoning from it scores exactly as it would on the original. Changing the details changes nothing a model can be graded on. The guarantee holds on three conditions, which double as authoring requirements: (1) the gold key is expressed entirely in the perturbed namespace, with no pre-perturbation identifier surviving in it; (2) no judgment unit references the real-world identity of the document or its parties — units key on roles and structure only; and (3) the perturbation only relabels, never adding, removing, or reordering clauses.
The corollary is the property the suite is built around: a model is never penalized for the perturbation, and never gated for correctly recalling a true fact about an underlying real document (Faithfulness keys on falsity and misattribution, not ungroundedness). As of v6, all five modified-from-real prompts are perturbed (A1: Calidon/Sferex; A2, B3, C3, E1: Kelmont/Spireline), so planted gaps are genuinely true of their instances and recall cannot collide with the gold.

6.2a Instruction Specificity, Open-Variant Grading & Clean-Instance Controls (v7)
Task framing vs. finding leakage. Every prompt must tell the model what artifact to produce — client seat (“from the perspective of Spireline Digital”), output format (“quote the exact language”), and artifact spec are the grading contract: a real associate would know them, and Directionality and Actionability grading depend on them. They stay, everywhere. What a detection or diagnosis prompt must NOT do is assert that findings exist or how many. An existence assertion (“several provisions are absent”) converts issue-spotting into checklist diffing; a count assertion (“identify the three most significant”) makes it impossible for a model to over-flag or under-flag on a prompt whose stated purpose is precision; a singular assertion (“the specific problem”) points straight at the planted defect. The eval’s positioning is “can a model work as a first-year associate” — and the partner says “review this NDA before the call,” not “this NDA has missing clauses, find them.” Spontaneous detection is the billable skill; hinted detection is guided enumeration, which is easier and compresses model spread. The one-line rule: hints about what to produce are the grading contract — keep them; hints about what the model will find change what is being measured — strip them from detection and diagnosis prompts.
Instruction specificity is a controlled variable, not a phrasing accident. As of v7, the detection/diagnosis prompts (A1, A2, C2) carry two instruction variants over the same instance, the same gold key, and the same grader contract: an OPEN variant (existence-neutral; printed in the paste block) and a DIRECTED variant (the v6 phrasing; preserved in the variants note below each paste block). The open score is the headline; the open-minus-directed delta is itself diagnostic — it measures, per model, how much of performance is prompted vs. spontaneous. B3’s “If a term is absent, say so” is an honesty instruction rather than a finding leak; it gets a one-time instructed/uninstructed A/B rather than a permanent variant pair. Framing stays where the framing IS the job: C3 (a proofread-the-defined-terms QC assignment), A3 (a version diff), all of Stage B’s extraction tasks, Stage D’s drafting briefs (there the instructions are the gold set), and Stage E’s triage.
Clean-instance controls. The strongest test of the hallucination resistance Stage A explicitly claims to measure is the same open prompt run on an instance where nothing is wrong, with gold = “no material concerns.” Existence hints foreclose this control entirely — told there are three problems, every model will manufacture three. Existence-neutral prompts unlock it, and under the environment principle (§1) clean instances are nearly free to add: same task structure, new instance, trivial gold. On a clean instance, any asserted material defect is a precision failure, and a defect stated as fact about the document is a Faithfulness trip. Each detection task should ship with at least one clean-instance sibling once the open variants are the headline.
Grading consequences of open prompts — two adjustments. Open prompts produce broader responses, so the grading absorbs two deliberate changes. (a) Defensible-but-ungraded: Coverage stays recall-vs-gold, but a legitimate, defensible flag outside the gold set is neither Coverage credit nor a Faithfulness failure — it is simply ungraded. This is the same spirit as the v5.1 “a true statement never fails Faithfulness” rule, extended one step: reasonable judgment never fails either. A finding fails Faithfulness only if it is false of the instance or misattributes something to the document; it fails Directionality only on unambiguous wrong-party advocacy. The grader classifies each finding as GOLD-MATCHED, DEFENSIBLE-UNGRADED, or FALSE/MISATTRIBUTED. (b) Precision/length norm: so models cannot farm Coverage by listing thirty concerns, open-variant responses are scored on precision — material findings as a fraction of total findings, banded — or held to an explicit length norm; an undifferentiated laundry list also docks Actionability (prioritization is part of the artifact). On A2’s open variant the “up to three” bound makes over-listing an instruction-following failure as well.
Stable gold-unit IDs (authoring rule, v7). Every gold key already decomposes into discrete judgment units — a specific absence, a specific expected edit, a specific accept/reject call. From v7 each unit carries a stable, enumerable ID in the form task.unit-type.slug (e.g. A1.absence.governing_law, C3.term.losses, E1.call.change7_force_majeure), printed in the unit’s gold-table row. The IDs must survive finalization as individually named rows — never prose paragraphs — so concept tags, synthetic-instance generators, and the planned RL adaptation can target units directly without re-excavating the rubrics. This is formatting discipline, not a design change, and it is mandatory for all new prompts. The full authoring rules and process live in the companion document “LegalEval — Prompt Authoring & Grading Guidelines (v7).”
6.3 Per-Prompt Dimension Map

>

>Prompt
	||CELL||Applicable Dimensions
	||CELL||Max
	||CELL||Gates Active
	||CELL||
>A1
	||CELL||Faithfulness /3 · Directionality /4 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||16
	||CELL||Both
	||CELL||
>A2
	||CELL||Faithfulness /3 · Directionality /4 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||16
	||CELL||Both
	||CELL||
>A3
	||CELL||Faithfulness /3 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||12
	||CELL||Faithfulness
	||CELL||
>B1
	||CELL||Faithfulness /3 · Coverage /4 · Actionability /2
	||CELL||9
	||CELL||Faithfulness
	||CELL||
>B2
	||CELL||Faithfulness /3 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||12
	||CELL||Faithfulness
	||CELL||
>B3
	||CELL||Faithfulness /3 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||12
	||CELL||Faithfulness
	||CELL||
>C1
	||CELL||Faithfulness /3 · Directionality /4 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||16
	||CELL||Both
	||CELL||
>C2
	||CELL||Faithfulness /3 · Directionality /4 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||16
	||CELL||Both
	||CELL||
>C3
	||CELL||Faithfulness /3 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||12
	||CELL||Faithfulness
	||CELL||
>D1
	||CELL||Faithfulness /3 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||12
	||CELL||Faithfulness
	||CELL||
>D2
	||CELL||Faithfulness /3 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||12
	||CELL||Faithfulness
	||CELL||
>D3
	||CELL||Faithfulness /3 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||12
	||CELL||Faithfulness
	||CELL||
>E1
	||CELL||Faithfulness /3 · Directionality /4 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||16
	||CELL||Both
	||CELL||
>E2
	||CELL||Faithfulness /3 · Directionality /4 · Coverage /4 · Soundness /3 · Actionability /2
	||CELL||16
	||CELL||Both*
	||CELL||
>
* E2 is a neutral-mediator task, so the 'correct direction' is balanced neutrality. The Directionality gate trips if the model systematically favors one party.

6.4 Gold-Standard Provenance
A rubric is only as trustworthy as the gold answer behind it. The gold standards in this suite come from three different places, and they are not equally reliable — so the scoring should not treat them as if they were. This subsection states, per prompt, where the gold answer comes from and whether it has been attorney-attested.

>

>Provenance type
	||CELL||What backs the gold answer
	||CELL||Reliability
	||CELL||
>Document-grounded
	||CELL||Verifiable directly against the source text or arithmetic — the answer is in the contract (defined terms, obligations, a redacted figure) or is a calculation. No legal judgment required.
	||CELL||Self-attesting — no human needed
	||CELL||
>Constructed key
	||CELL||An authored answer key built when the task was designed — the planted issues, the expected vendor-favorable edits, the required drafting provisions. Informed by the source datasets' standards but not lifted from them.
	||CELL||Needs lawyer review
	||CELL||
>Legal judgment
	||CELL||Rests on contestable legal or commercial reasoning — which absences favor which party, whether a deal is bridgeable, whether a clause is well-drafted. Currently authored, not attorney-attested.
	||CELL||Needs lawyer review — high priority
	||CELL||
>

Important caveat on the source datasets: although every prompt draws its contract text from real expert-annotated corpora (CUAD, ContractNLI, ACORD, MAUD) and SEC filings, the per-prompt gold answers are mostly not lifted from those datasets' labels. The datasets supply the source material and the standard of what realistic clauses look like; the specific answer keys here were constructed for these tasks. The exception is the document-grounded prompts, where the source text itself is the answer key. This means the dataset citations attest the realism of the inputs, not the correctness of the gold outputs — those still need their own validation.

>

>Prompt
	||CELL||Primary provenance
	||CELL||Verifiable layer / Judgment layer
	||CELL||Validation status
	||CELL||
>A1
	||CELL||Mixed
	||CELL||Which clauses are absent = verifiable; which absences favor Calidon = judgment
	||CELL||Judgment layer unattested
	||CELL||
>A2
	||CELL||Constructed + judgment
	||CELL||Clauses are real = verifiable; the 'three worst' ranking = constructed/judgment
	||CELL||Ranking needs review
	||CELL||
>A3
	||CELL||Mixed
	||CELL||The diffs between versions = verifiable; favorable/unfavorable direction = judgment
	||CELL||Direction layer unattested
	||CELL||
>B1
	||CELL||Document-grounded
	||CELL||All 20/21 terms are in the text = fully verifiable
	||CELL||Self-attesting
	||CELL||
>B2
	||CELL||Document-grounded
	||CELL||Obligations enumerated verbatim in Articles III/IV = verifiable
	||CELL||Self-attesting
	||CELL||
>B3
	||CELL||Perturbed (fictionalized)
	||CELL||Modified-from-real: the “redacted” cap (§12.02) and “absent” governing law (NY, §16.12) are present in the real filing — not verifiable-as-stated
	||CELL||NOT self-attesting — modified-from-real; re-found trap on a withheld/synthetic figure
	||CELL||
>C1
	||CELL||Constructed + judgment
	||CELL||Source clause real; the 6 expected vendor-favorable edits = authored key
	||CELL||Edit key needs review
	||CELL||
>C2
	||CELL||Legal judgment
	||CELL||The 'uncapped indemnification via §8 carve-out' diagnosis = legal analysis
	||CELL||Needs review
	||CELL||
>C3
	||CELL||Perturbed (fictionalized)
	||CELL||The inconsistencies were planted by editing the excerpt — the real filing uses the defined terms correctly (real §11.03 uses “Losses”)
	||CELL||NOT self-attesting — constructed (planted) inconsistencies
	||CELL||
>D1
	||CELL||Constructed (from brief)
	||CELL||The 11 required provisions come from the brief = verifiable; drafting soundness = judgment
	||CELL||Soundness layer needs review
	||CELL||
>D2
	||CELL||Mixed
	||CELL||97.5% uptime = arithmetic-verifiable; 'don't overreach to termination' = judgment
	||CELL||Math self-attesting; judgment needs review
	||CELL||
>D3
	||CELL||Constructed (from brief)
	||CELL||The 6 required changes come from the instructions = verifiable; no-scope-creep = verifiable
	||CELL||Self-attesting
	||CELL||
>E1
	||CELL||Constructed + judgment
	||CELL||The accept/reject/counter answer key = authored legal judgment
	||CELL||Calls need review
	||CELL||
>E2
	||CELL||Legal judgment
	||CELL||'All 6 bridgeable; 2-day claim is a position not a constraint' = commercial judgment
	||CELL||Needs review — highest priority
	||CELL||
>

>

>FAILURE MODES
What this means for the eval’s honesty: only the genuinely verbatim document-grounded prompts (B1, B2, D3) can be trusted today — the source text is the answer key. B3 and C3 were thought to be in that set but are NOT: both are modified-from-real (B3’s “redacted” cap and “absent” governing law are in fact present in the real filing; C3’s defined-term inconsistencies were planted by editing the excerpt). Treat B3 and C3 as constructed tasks pending the gold-verification sweep, not as self-attesting. The constructed and judgment prompts (A1–A2, C1–C2, D1–D2, E1–E2) carry gold answers that are currently authored, not attorney-attested. They are plausible and defensible, but until the calibration set (§6.5) is graded by lawyers, treat their gold standards as provisional and weight conclusions on those stages accordingly.
Priority order for attorney validation: the 'Legal judgment' rows first (C2, E2, and the judgment layers of A1, C1, E1), then the constructed keys, then a spot-check of the document-grounded rows to confirm nothing was mis-transcribed from the source filings.
	||CELL||
>

>

>NOTE
This is also why the grader's calibration step (next subsection) matters twice over: it validates that the LLM grader agrees with humans, and — because the humans are lawyers scoring against these gold answers — it simultaneously surfaces any gold answer the lawyers disagree with. A dimension that can't clear the agreement threshold may indicate a weak grader OR a contestable gold standard; both are worth catching.
	||CELL||
>

6.5 LLM Grader Architecture
The earlier draft sent redlining, drafting, and negotiation to human reviewers because Directionality and Actionability were thought to need human judgment. They do not — provided the grader works against a reference rubric rather than holistically, and the judgment is decomposed into checkable sub-claims. Humans do not disappear; their role shifts from grading every output to calibrating the grader and auditing the hard tail.

>

>DESIGN NOTE
Why Directionality and Actionability are tractable for an LLM grader: neither requires open-ended judgment once decomposed. Directionality becomes per-edit classification — extract each edit the model made, ask 'does this favor Vendor, Customer, or neither?' against the gold answer. Actionability becomes a checklist — proposed language present (not just description)? correct artifact format? specific vs. vague? self-contained? Each is a yes/no. Constrained classification and checklists are exactly where LLM judges are reliable; holistic 1–5 quality ratings are where they are not.
	||CELL||
>

Three-Tier Grader

>

>Tier
	||CELL||Method
	||CELL||Handles
	||CELL||LLM needed?
	||CELL||
>Tier 0 — Deterministic
	||CELL||String/set matching against gold labels; arithmetic check; format/structure detection
	||CELL||Coverage recall vs. gold issue-set; B1 term count; D2 uptime math (97.5%); required-phrase presence (D3 'in full force and effect'); table/signature-block present
	||CELL||No
	||CELL||
>Tier 1 — LLM grader
	||CELL||Reference-anchored, decomposed, evidence-quoting. Grader receives source contract + prompt + gold rubric + response. Emits structured JSON per sub-criterion
	||CELL||Faithfulness (is each assertion either supported by the source or independently true, and is nothing false or misattributed to the document? — true outside knowledge does not fail); Directionality (per-edit classification); Soundness (does the fix address the gold risk?); Actionability checklist
	||CELL||Yes
	||CELL||
>Tier 2 — Controls & escalation
	||CELL||Cross-family judge, self-consistency, confidence-gated escalation
	||CELL||Bias mitigation; routes low-confidence / split items to a small human queue (~10–15% of items)
	||CELL||Yes + human tail
	||CELL||
>

The reliability levers that make Tier 1 trustworthy
Reference-anchored, not holistic. The grader is given the gold rubric and the source contract. It checks the response against a known answer rather than reasoning from scratch — grading is far easier than generating, which is what makes delegation work.
Decomposition. Each dimension is graded as a set of yes/no sub-claims, never a single quality score. 'Score Directionality 0–4' becomes 'for each of the N edits, classify direction; Directionality = fraction favoring the client, banded to 0–4.'
Mandatory evidence quotes. For every sub-judgment the grader must cite the exact span of the response it relied on. This is the single biggest suppressant of hallucinated grading: a grade with no quotable evidence is rejected, and the citations make every grade auditable after the fact.
Cross-family judging. Grade a model's output with a judge from a different model family to neutralize self-preference. Ideally an ensemble of 2–3 judges from different families; majority vote; disagreements escalate.
Self-consistency. Run the grader k=3 at temperature > 0; high-variance items escalate to the human queue.
Blind + shuffled (carried from v2). Strip model identity labels and randomize output order per prompt. Note this is label-blind, not fully anonymized — stylistic fingerprints survive.

Validate before you trust — the step that makes this credible
Removing humans is only legitimate if the grader has been shown to agree with humans first. The protocol:
Build a calibration set: 30–50 responses graded by two human lawyers to consensus.
Measure grader-vs-human agreement per dimension — Cohen's kappa (categorical) or Krippendorff's alpha (ordinal).
Decision rule per dimension: kappa ≥ 0.80 — trust the LLM grader; 0.60–0.79 — use it but keep a higher human-audit rate; below 0.60 — that dimension stays human-led.
Re-validate whenever you change grader models, add prompt types, or add a new contract type.

>

>Dimension
	||CELL||Expected to clear kappa ≥ 0.80?
	||CELL||Why
	||CELL||
>Faithfulness
	||CELL||Yes
	||CELL||Checkable against the source — 'does this clause exist / does this number match'
	||CELL||
>Coverage
	||CELL||Yes
	||CELL||Set membership against a gold issue list; largely Tier 0
	||CELL||
>Directionality
	||CELL||Likely, once decomposed per-edit
	||CELL||Constrained classification against gold; the trap is holistic grading, which decomposition removes
	||CELL||
>Soundness
	||CELL||Borderline — validate carefully
	||CELL||Needs the gold rubric; hardest on novel/edge legal reasoning, especially Stage E strategic calls
	||CELL||
>Actionability
	||CELL||Yes, as a checklist
	||CELL||Format and specificity are mechanically checkable; only the 'usable as-is' judgment is soft
	||CELL||
>

>

>FAILURE MODES
Honest limitations of an LLM grader:
The grader needs the legal knowledge it is testing — but checking against a gold rubric is far easier than generating, so this is tractable except where the gold answer is itself contestable (some Stage E strategic calls). Those stay partly human.
Self-preference bias is real and not fully eliminable; cross-family judging and blinding mitigate but do not erase it. Always report which grader family produced the scores.
Soundness on edge-case legal reasoning is the residual hard case — gate it behind the kappa threshold rather than assuming the grader is right.
	||CELL||
>

Grader prompt template (Tier 1)
A concrete structured-output grader prompt for one dimension. The grader returns JSON only; a wrapper parses it, applies bands, and runs the gate logic.

>

>PASTE BELOW INTO MODEL

SYSTEM: You are grading a legal task response against a gold rubric. You are NOT
solving the task. Judge only what the rubric specifies. For every sub-judgment you
MUST quote the exact span of the RESPONSE you relied on. If you cannot quote
supporting text, the sub-judgment is 'unsupported' and scores 0. Output JSON only.

USER:
SOURCE_CONTRACT: <<full source text>>
PROMPT_GIVEN_TO_MODEL: <<the prompt>>
GOLD_RUBRIC: <<the dimension's gold criteria, e.g. the 6 expected vendor-favorable edits>>
RESPONSE_UNDER_TEST: <<the model's answer, identity stripped>>

DIMENSION: Directionality (named client: Vendor)
TASK: 1) Extract every edit/recommendation in RESPONSE_UNDER_TEST.
      2) For each, classify direction: FAVORS_VENDOR | FAVORS_COUNTERPARTY | NEUTRAL,
         with an evidence quote.
      3) Directionality_score = round(4 * (#FAVORS_VENDOR) / (#total non-neutral edits)).
      4) gate_tripped = true if ANY edit is FAVORS_COUNTERPARTY.

Return: { "edits": [ { "text": "...", "direction": "...", "evidence": "..." } ],
         "score": 0-4, "gate_tripped": bool, "confidence": 0.0-1.0,
         "notes": "..." }
	||CELL||
>

6.6 Stage Weights & Overall Score

>

>Stage
	||CELL||Weight
	||CELL||Rationale
	||CELL||
>A — Issue Spotting
	||CELL||20%
	||CELL||Foundation skill; mostly Tier 0 + Tier 1 gradable
	||CELL||
>B — Summarization
	||CELL||20%
	||CELL||Core extraction; Faithfulness most testable here
	||CELL||
>C — Redlining
	||CELL||25%
	||CELL||Highest billable-hour value; Directionality-heavy
	||CELL||
>D — Drafting
	||CELL||20%
	||CELL||Zero-to-draft quality; scope discipline (Faithfulness)
	||CELL||
>E — Negotiation
	||CELL||15%
	||CELL||Hardest to construct and to grade; smaller sample
	||CELL||
>

Overall model score = (A × 0.20) + (B × 0.20) + (C × 0.25) + (D × 0.20) + (E × 0.15), where each stage score is the mean of its prompts' gate-adjusted normalized scores. Report gate-trip counts alongside the headline number — a model at 0.78 with zero gate trips is very different from a model at 0.78 with six, and the headline average hides that.

6.7 Minimum Viable Eval (50 Tasks)
If building the full 200-task set is not feasible:
10 × Stage A tasks from CUAD with ground-truth clause labels (Tier 0 + Tier 1)
10 × Stage B extraction tasks from MAUD (mostly Tier 0)
15 × Stage C redlining tasks (Tier 1 grader on Directionality + Soundness; validate kappa first)
10 × Stage D drafting tasks (Tier 0 for scope/format; Tier 1 for Soundness)
5 × Stage E negotiation triage tasks (E1-type; Tier 1 with human audit on the tail)

>

>NOTE
A 50-task eval is sufficient for model comparison once the grader has cleared the kappa thresholds on a calibration set. The full 200-task eval adds statistical confidence and contract-type breakdowns for locating model weaknesses on specific clause or agreement types.
	||CELL||
>

>

>PART II — REAL-SOURCE PROMPT TEST SUITE
	||CELL||
>

Contract text is sourced from real SEC EDGAR filings, ContractNLI NDAs, and CUAD/ACORD annotated clause examples. Important: several prompts use excerpts that have been deliberately truncated or altered to plant a gap or an inconsistency. Those are constructed (modified-from-real) tasks, not verbatim reproductions of the filing, and their gold answers must not claim the manufactured gap exists in the real document (see Provenance Correction below). Each prompt is self-contained: each PASTE BELOW INTO MODEL block is the complete, verbatim model input — task instructions followed by contract text, with no provenance disclosures. Feed the block to the model as a single user message, identically for every model under test, and feed it nothing else. Everything outside the block — the source lines, provenance tags, RUBRIC FIX boxes, gold tables, and scoring rubrics — is for the eval team and the grader only and must never be shown to the model. Symmetrically, each prompt ends with a consolidated GRADER INSTRUCTIONS block: the complete gold rubric for that prompt, including its provenance and recall protections, used verbatim as the GOLD_RUBRIC payload in the Tier 1 grader template (§6.5). Score against that block; the design tables above it are rationale, not additional criteria. (v7) Detection and diagnosis prompts (A1, A2, C2) carry two instruction variants over the same instance: OPEN — printed in the paste block, existence-neutral, the headline score — and DIRECTED, preserved in the INSTRUCTION-SPECIFICITY VARIANTS note below the block. B3 carries an instructed/uninstructed A/B on its honesty sentence. Variants change only the instruction sentences, never the contract text, the gold key, or the grader contract; record which variant each response saw (see §6.2a).

>

>DESIGN NOTE
Rubric fixes from v2 are incorporated inline. Changed rubrics are flagged with RUBRIC FIX (v2) boxes. Scoring weights throughout Part II use the revised system from §6. Each prompt's label carries a gold-provenance tag (where its answer key comes from and whether it's attorney-attested) — the full provenance map is in §6.4.
	||CELL||
>
PROVENANCE CORRECTION (v5) — gold validity & contamination
A diff against the source filings found that several gold answers are built on unmarked alterations of the real documents: clauses that exist in the executed contract are presented here as “[Not stated]” or “[Redacted],” and the gold then treats those manufactured gaps as ground truth. Because these are public filings in every model’s pretraining, that is also a contamination trap — a model that correctly recalls the real document gets scored as hallucinating. Confirmed on the 3M / Cogent NDA (governing law is Minnesota, §9.4; obligations terminate at the 2nd anniversary; return/destruction is present) and the Kubient / Sphere Digital MSA (governing law is New York, §16.12; the §12.02 cap is present and readable, not redacted; the Ad Engine is defined and bounded; real §11.03 uses the defined term “Losses”). Four rules apply going forward:
1. Label provenance per document — “verbatim real” vs. “modified-from-real.” A task that deletes or alters clauses to plant a gap is a constructed task in a real-document costume; that is fine, but it must be labeled, and the gold must not claim the gap exists in the filing.
2. Never gate on recall of the true document. If a model states the real governing law, cap, or definition, that is not a Faithfulness failure. Either use genuinely private/synthetic/recent contracts, or perturb the identifying details (names, numbers, jurisdiction) so the real answer and the gold cannot diverge.
3. Re-found the B3 hallucination trap on a genuinely-unknowable figure — one actually redacted in the source, or synthetic — not a clause that is public.
4. Run a one-pass gold-verification sweep across all 13 prompts now, diffing every “[Not stated] / [Redacted] / inconsistency-in-the-filed-contract” claim against the source — cheapest at 13 prompts, expensive at 200. And soften the Directionality gate to fire only on unambiguous wrong-party advocacy, not on defensible positions (e.g. recommending a return/destruction clause) that sophisticated real parties actually included.4. Run a one-pass gold-verification sweep across all 14 prompts now, diffing every “[Not stated] / [Redacted] / inconsistency-in-the-filed-contract” claim against the source — cheapest at 14 prompts, expensive at 200. And soften the Directionality gate to fire only on unambiguous wrong-party advocacy, not on defensible positions (e.g. recommending a return/destruction clause) that sophisticated real parties actually included.
STATUS (v6): executed. All five modified-from-real prompts are now perturbed (A1: Calidon/Sferex; A2, B3, C3, E1: Kelmont/Spireline). B1/B2 retain verbatim text with header party names relabeled; D3's party names were fictionalized to match. Model-facing paste blocks carry no provenance disclosures; full provenance lives in the team-facing source notes and the per-prompt GRADER INSTRUCTIONS.

Stage A — Document Ingestion & Issue Spotting
"Read this, tell me what's wrong"

Applicable dimensions: Faithfulness /3 (gate) · Directionality /4 (gate) · Coverage /4 · Soundness /3 · Actionability /2

Prompt A1 — Missing Clause Detection

>

>Task A1 · Missing-Clause Detection · Max /16 · gates: Faithfulness, Directionality · gold: document-grounded + legal judgment (judgment layer needs review) · PROVENANCE: HYPOTHETICAL (perturbed from a real NDA) — parties fictionalized; the absent clauses are genuinely absent here, so recall cannot contradict the gold
	||CELL||
>

■ Source: Calidon Industries, Inc. / Sferex Biometrics, Inc. — Non-Disclosure Agreement (hypothetical; adapted from a real SEC-filed M&A NDA, with parties, dates, and identifying details changed). Effective Date February 12, 2014.
PERTURBATION APPLIED (v5.1). This prompt has been fictionalized to remove the contamination trap. Parties were changed (3M Company → Calidon Industries, Inc.; Cogent, Inc. → Sferex Biometrics, Inc.), the effective date was changed, and the SEC-filing reference was dropped. Because the document now has no real-world twin, the clauses the gold treats as absent (governing law, term, return/destruction, injunctive relief, no-reliance) are genuinely absent here — so no model can recall a “real” value that contradicts the gold, and the mandatory Coverage findings no longer penalize correct recall. The real source this was adapted from is documented in the Provenance Correction box and the verification sweep.

This is a hypothetical non-disclosure agreement, adapted from a real M&A filing with the parties and identifying details changed and certain provisions removed for this task. Read it carefully. (v7: open variant) Review it from the perspective of the Receiving Party (Calidon) and report any material concerns, if any — whether in the provisions as written or in anything missing or materially incomplete. For each concern, explain the practical risk it creates for Calidon. The directed variant (the v6 phrasing, which asserted that standard provisions are absent) is preserved in the variants note below the paste block.

>

>PASTE BELOW INTO MODEL

Read the non-disclosure agreement below carefully. You represent the Receiving Party (Calidon). Report any material concerns with this agreement, if any — whether in the provisions as written or in anything missing or materially incomplete. For each concern, explain the practical risk it creates for Calidon.

NON-DISCLOSURE AGREEMENT
Calidon Industries, Inc. ('Interested Party' / 'Receiving Party') and Sferex Biometrics, Inc. ('Company' / 'Disclosing Party')
Effective Date: February 12, 2014

1. PROPRIETARY INFORMATION
'Proprietary Information' means any and all information disclosed by Disclosing Party
or its Representatives in connection with the Proposed Transaction, including Derived
Information prepared by Receiving Party that reflects or is based upon the Disclosing
Party's information. Also includes: (x) discussions taking place; (y) proposed terms;
(z) existence of this Agreement.
Exclusions: information (i) generally available to the public other than by Receiving Party's breach;
(ii) known to Receiving Party on a non-confidential basis; (iii) independently developed.

2. NON-DISCLOSURE AND LIMITED USE
Receiving Party shall keep all Proprietary Information confidential and shall not disclose
it except to Representatives actively and directly participating in the evaluation of the
Proposed Transaction and who are bound by comparable confidentiality obligations.
Degree of care: same care as Receiving Party uses to protect its own confidential information
(but no less than reasonable care).

2.4 COMPELLED DISCLOSURE
If Receiving Party is required by law or legal process to disclose Proprietary Information,
it shall promptly notify Disclosing Party so that Disclosing Party may seek a protective order
or waive compliance. If no protective order is obtained, Receiving Party shall disclose only
what is legally required and seek reliable assurances of confidential treatment.

3. NO SOLICITATION OF EMPLOYEES
Interested Party agrees that for one year from the Effective Date it will not employ or
solicit for employment any key technical or management personnel of the Company who was
introduced to Interested Party in connection with the Proposed Transaction.

4. SECURITIES ISSUES
Each party confirms it is not required to make public disclosure of the Proposed Transaction
or any Proprietary Information as of the date hereof.

5. DEFINITIVE AGREEMENT
Until a definitive agreement is executed, neither party shall have any legal obligation
with respect to the Proposed Transaction except for the matters set forth herein.

GOVERNING LAW: [Not stated in this agreement]
TERM: [Not stated in this agreement]
Signed: Calidon Industries, Inc. _______________ Sferex Biometrics, Inc. _______________
	||CELL||
>
INSTRUCTION-SPECIFICITY VARIANTS (v7) — A1. The paste block above is the OPEN variant: it specifies seat, artifact, and format (the grading contract) but asserts neither that findings exist nor how many. It is the headline score. The DIRECTED variant replaces the instruction sentences with the v6 phrasing: “Read the non-disclosure agreement below carefully. Several provisions standard to commercial NDAs are absent. Your task: identify every clause that is missing or materially incomplete. For each, explain the practical risk it creates for the Receiving Party (Calidon).” Contract text, gold key, and grader contract are identical. Run both; report the open score as the headline and the open-minus-directed delta as a per-model diagnostic of spontaneous vs. prompted detection. The open variant also licenses a clean-instance control (§6.2a): the same instruction on an instance with no material gaps, gold = “no material concerns.”

>

>RUBRIC FIX (v2)
CORE REFRAME (v2): This is a target-disclosure M&A NDA. Sferex (target) discloses to Calidon (potential acquirer). Calidon is the Receiving Party.
The original rubric treated ALL absent standard clauses as Calidon risks. WRONG. Many standard clauses protect the Disclosing Party (Sferex) — their absence is neutral or favorable to Calidon.
Split scoring into TWO BUCKETS: (1) absences that harm Calidon, (2) absences that are neutral or favorable to Calidon.
A model that recommends Calidon add an unambiguously counterparty-favoring clause — e.g. a standstill that restricts Calidon as the acquirer — has failed Directionality. Milder, defensible asks (return/destruction, injunctive relief) do not trip the gate; the real sophisticated parties included return/destruction, so recommending it is at most a minor Directionality deduction.
	||CELL||
>

Bucket 1 — Absences that create genuine risk for Calidon (Receiving Party)

>

>Absence
	||CELL||Expectation
	||CELL||Scoring
	||CELL||
>Governing law / jurisdiction [ID: A1.absence.governing_law]
	||CELL||Must flag — no chosen forum means unpredictable default rules and home-turf litigation risk for Calidon
	||CELL||Required for Coverage
	||CELL||
>Term / expiration [ID: A1.absence.term]
	||CELL||Must flag — no sunset means obligations arguably perpetual; asymmetric indefinite burden on Calidon
	||CELL||Required for Coverage
	||CELL||
>Limitation of liability / damages cap [ID: A1.absence.liability_cap]
	||CELL||Should flag — no cap or consequential-damages waiver protecting Calidon
	||CELL||Partial Coverage
	||CELL||
>Residuals clause [ID: A1.absence.residuals]
	||CELL||Should flag — 'Derived Information' in §1 makes its absence acute for Calidon as the party making notes
	||CELL||Partial Coverage
	||CELL||
>4th standard exclusion (info received from permitted third party) [ID: A1.absence.fourth_exclusion]
	||CELL||Should flag — only three exclusions present; genuine drafting gap
	||CELL||Partial Coverage
	||CELL||
>Non-solicitation (§3) carve-outs [ID: A1.absence.nonsolicit_carveouts]
	||CELL||Should flag — no exception for general ads or unsolicited applicants; 'key personnel' undefined
	||CELL||Partial Coverage
	||CELL||
>§2.4 completeness [ID: A1.refine.compelled_disclosure]
	||CELL||Credit refinement (missing 'to the extent legally permitted' + cost allocation) — do NOT credit a claim that §2.4 is absent
	||CELL||Faithfulness penalty if claimed absent (gate per rubric below)
	||CELL||
>

Bucket 2 — Absences that are neutral or favorable to Calidon (do NOT recommend adding)

>

>RUBRIC FIX (v2)
A model that recommends Calidon add any of the following has failed Directionality. These protect Sferex (the Disclosing Party), not Calidon.
Standstill clause — highest-value insight. In M&A NDAs, standstills restrict the acquirer (Calidon). ABSENCE STRONGLY FAVORS Calidon. A model that surfaces this distinction earns maximum Directionality points. [ID: A1.favorable.standstill]
Return/destruction of materials — obligation would fall on Calidon (the holder). Absence is neutral-to-favorable to Calidon. [ID: A1.favorable.return_destruction]
Injunctive relief / irreparable-harm stipulation — pre-concedes harm to the Disclosing Party. Absence is neutral-to-favorable to Calidon. [ID: A1.favorable.injunctive_relief]
No-reliance / 'as-is' disclaimer — protects the Disclosing Party. Absence preserves Calidon's reliance/misrepresentation claims. [ID: A1.favorable.no_reliance]
Liability for Representatives' breaches — absence means Calidon is not automatically on the hook for advisors' leaks. [ID: A1.favorable.rep_liability]
	||CELL||
>

Scoring Rubric  ·  Max: /16  ·  Dimensions: Faithfulness /3 (gate) · Directionality /4 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||No hallucinated clauses. §2.4 must not be claimed absent. No invented provisions.
	||CELL||Claiming §2.4 is absent; inventing clauses not at issue
	||CELL||
>Directionality
	||CELL||/4
	||CELL||Discriminating dimension. MUST separate Bucket 1 (harms Calidon) from Bucket 2 (favorable to Calidon). Recognizing the standstill point scores top marks.
	||CELL||Treating return/destruction or injunctive relief as Calidon risks; recommending Calidon add a standstill
	||CELL||
>Coverage
	||CELL||/4
	||CELL||Governing law + term are mandatory (0 pts if either missing). Partial credit for remaining Bucket 1 items.
	||CELL||Missing governing law or term
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Risk explanations are legally correct; correctly reasons about who each absent clause protects in an M&A target-disclosure NDA.
	||CELL||Mischaracterizing why a clause matters; misreading the disclosure direction
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Prioritized; tells client which gaps to fix vs. which not to volunteer.
	||CELL||Long undifferentiated checklist; vague risk statements
	||CELL||
>

>

>GATE
Faithfulness gate trips if §2.4 is claimed absent or a clause is invented.
Directionality gate trips only on unambiguous wrong-party advocacy — recommending Calidon add a standstill (a clause that demonstrably restricts Calidon, the acquirer). It does NOT trip on defensible asks such as recommending a return/destruction or injunctive-relief clause: those are mild and the sophisticated real parties to this NDA in fact included return/destruction. Treat such asks as at most a minor Directionality deduction, not a gate.
	||CELL||
>

>

>FAILURE MODES
Failure mode summary: Treating Disclosing-Party-protective absences as Calidon risks; missing governing law or term; recommending Calidon add a standstill; claiming §2.4 is absent.
	||CELL||
>

GRADER INSTRUCTIONS — A1 (Missing-Clause Detection) · Max /16 · Gates: Faithfulness + Directionality
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: Perturbed hypothetical (real M&A NDA, parties fictionalized to Calidon / Sferex; 3M / Cogent in the source filing). No real-world twin for the facts that matter: the clauses the gold treats as absent (governing law, term, return/destruction, injunctive relief, no-reliance) are genuinely absent in this instance. The model was NOT told the instance is adapted; grade only against the contract as presented, and never penalize a statement for drawing on outside knowledge if it is true of the instance.
CONTEXT: Target-disclosure M&A NDA. Sferex (target) discloses to Calidon (acquirer). Calidon is the Receiving Party. Many standard absences protect the DISCLOSING party, so their absence is neutral-to-favorable for Calidon -- the bucket split below is the core of the prompt.
FAITHFULNESS /3 (GATE): No invented clauses or provisions. TRIPS IF: Section 2.4 (compelled disclosure) is claimed absent -- it is present; or any clause is invented. Does NOT trip on true statements, even ungrounded ones.
DIRECTIONALITY /4 (GATE): The discriminating dimension. The response must separate Bucket 1 (absences that harm Calidon) from Bucket 2 (absences neutral/favorable to Calidon -- standstill, return/destruction, injunctive relief, no-reliance, liability for Representatives' breaches). Surfacing that a standstill's absence FAVORS Calidon earns top marks. TRIPS ONLY on unambiguous wrong-party advocacy: recommending Calidon ADD a standstill. Defensible asks (return/destruction, injunctive relief) = minor deduction at most, never a trip.
COVERAGE /4: Mandatory -- governing law AND term must both be flagged (0/4 if either missed). Partial credit -- limitation of liability / damages cap; residuals clause (acute given 'Derived Information' in Section 1); missing 4th standard exclusion (info from permitted third party); Section 3 non-solicit carve-outs ('key personnel' undefined, no general-ads exception). Section 2.4: credit a refinement (missing 'to the extent legally permitted' + cost allocation); do NOT credit a claim that 2.4 is absent.
UNIT IDs (v7): Bucket 1 -- A1.absence.governing_law; A1.absence.term; A1.absence.liability_cap; A1.absence.residuals; A1.absence.fourth_exclusion; A1.absence.nonsolicit_carveouts; A1.refine.compelled_disclosure. Bucket 2 -- A1.favorable.standstill; A1.favorable.return_destruction; A1.favorable.injunctive_relief; A1.favorable.no_reliance; A1.favorable.rep_liability. Reference the matching unit ID in the grader JSON for every finding judged.
SOUNDNESS /3: Risk explanations legally correct; the response correctly reasons about WHO each absent clause protects in a target-disclosure M&A NDA. Dock for mischaracterizing why a clause matters or misreading the disclosure direction.
ACTIONABILITY /2: Prioritized; tells the client which gaps to fix vs. which not to volunteer. Dock for a long undifferentiated checklist or vague risk statements.
VARIANTS (v7): Two instruction variants run on this instance -- OPEN (existence-neutral; the headline score) and DIRECTED (v6 phrasing). This gold rubric applies to both unchanged; record the variant with each grade and report open, directed, and the open-minus-directed delta. OPEN-VARIANT GRADING: classify each finding as GOLD-MATCHED, DEFENSIBLE-UNGRADED, or FALSE/MISATTRIBUTED. Defensible concerns outside the gold are neither Coverage credit nor Faithfulness failures; a finding fails Faithfulness only if false of the instance or misattributed. Apply the precision/length norm (Section 6.2a): an undifferentiated list of marginal concerns docks Actionability, and immaterial padding docks precision. CLEAN INSTANCE: when this task runs on a clean sibling instance, gold = 'no material concerns'; any asserted material gap is a precision failure and, if stated as fact about the document, a Faithfulness trip.
PROCEDURE: Score every dimension -> raw total -> normalize to /16 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Prompt A2 — Problematic Clause Identification (MSA)

>

>Task A2 · Problematic-Clause ID · Max /16 · gates: Faithfulness, Directionality · gold: constructed key + judgment (needs review) · perturbed (v6) · PROVENANCE: MODIFIED-FROM-REAL — §12.02 “redaction” and undefined-Ad-Engine gap are planted
	||CELL||
>

■ Source: Kubient, Inc. / Sphere Digital — Master Services Agreement, Exhibit 10.13 to S-1 (SEC EDGAR, filed 2020-07-02, CIK 1729750). PERTURBATION (v6): Kubient, Inc. → Kelmont, Inc.; Sphere Digital → Spireline Digital; dates retained; planted divergences (§12.02 redaction, unbounded Ad Engine) are true of this instance.

Adapted from a real MSA filed with the SEC (Kubient, Inc., S-1 Exhibit 10.13) and perturbed in v6: parties fictionalized to Kelmont, Inc. / Spireline Digital, with two planted divergences (§12.02 redaction; unbounded Ad Engine) that are genuinely true of this instance. The model receives no provenance disclosure; its full instruction is inside the paste block.

>

>PASTE BELOW INTO MODEL

Read the Master Services Agreement excerpt below from the perspective of Customer (Spireline Digital). Report up to three of the most significant concerns with this agreement, if any. For each concern you report: quote the exact language, explain the risk, and suggest a fix.

MASTER SERVICES AGREEMENT
Kelmont, Inc. ('Service Provider') and Spireline Digital ('Customer')
Effective Date: June 1, 2018

ARTICLE VI — TERM
Section 6.01: This Agreement shall commence on the Effective Date and continue for
six (6) months, unless sooner terminated. The Agreement automatically renews for
successive six-month periods unless terminated by either party. Either party may
terminate this Agreement with or without cause by providing two (2) days prior written
notice (email is acceptable).

ARTICLE VII — FEES AND PAYMENT
Section 7.05: Service Provider reserves the right to suspend all Services in the event
that Customer fails to pay each invoice within 15 days of receipt.

ARTICLE VIII — INTELLECTUAL PROPERTY
Section 8.01: Customer is, and shall be, the sole and exclusive owner of all right,
title and interest in and to the Deliverables, including all Intellectual Property Rights.
Service Provider agrees that Deliverables qualifying as 'work made for hire' under
17 U.S.C. § 101 are hereby deemed such. To the extent Deliverables do not constitute
'work made for hire', Service Provider hereby irrevocably assigns all right, title and
interest therein to Customer.

Section 8.02: Notwithstanding the foregoing, the Service Provider Ad Engine contains
valuable trade secrets and proprietary information of Service Provider, and all right,
title and interest in the Service Provider Ad Engine shall remain with Service Provider.
Service Provider shall provide Customer access and copies of source code and/or object
code to all custom revisions to the Customer Image; provided, however, Service Provider
shall not provide any source code included in the Service Provider Ad Engine.

ARTICLE XI — INDEMNIFICATION
Section 11.01: Service Provider shall defend, indemnify and hold harmless Customer from
and against all Losses arising from any third-party Action arising out of Service
Provider's negligence or more culpable act or omission; breach of representations or
warranties; failure to comply with applicable Law.

Section 11.03: Customer shall defend, indemnify and hold harmless Service Provider from
and against all Losses arising from Customer's bodily injury or death; damage to real
or tangible personal property.

ARTICLE XII — LIMITATION OF LIABILITY
Section 12.01: IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR INDIRECT, INCIDENTAL,
SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES.
Section 12.02: [Redacted]
	||CELL||
>
INSTRUCTION-SPECIFICITY VARIANTS (v7) — A2. The paste block above is the OPEN variant — existence-neutral, with “up to three … if any” as a bound rather than a count assertion, preserving the triage/ranking test. It is the headline score. The DIRECTED variant replaces the instruction sentences with the v6 phrasing: “Read the Master Services Agreement excerpt below. The agreement contains clauses that are unusually one-sided or commercially problematic. Identify the three most significant problems from the perspective of Customer (Spireline Digital). For each: quote the exact language, explain the risk, and suggest a fix.” Same contract text, gold, and grader. Dropping the asserted count strengthens the precision test §2 claims for A2: a model that shotguns ten issues now fails precision (and the stated bound) honestly instead of being protected by the cap, and a clean-instance control becomes possible (gold = “no material concerns”) — under the directed phrasing, told there are three problems, every model will manufacture three.

>

>RUBRIC FIX (v2)
v2 Fix: The three target issues remain the spine, but the rubric is now an OPEN SET. Correctly-identified secondary issues earn partial credit — they should not be treated as noise.
v2 Fix: Add hallucination-restraint check on §12.02 (redacted cap). Correct behavior: note it cannot be assessed without the number. DEDUCT Faithfulness for any model that invents a cap figure or speculates on likely contents.
	||CELL||
>

Ground-Truth Issues (items 1–2 mirror the underlying filing; item 3 is true of this perturbed instance)

>

>#
	||CELL||Clause
	||CELL||Real Problem
	||CELL||Required for Coverage
	||CELL||
>1
	||CELL||§6.01 — 2-day termination notice [ID: A2.issue.termination_notice]
	||CELL||Egregiously short. Customer has no operational stability — Service Provider can walk away in 48 hours. Market standard: 30–60 days with cure period for breach.
	||CELL||YES — miss = Coverage dock
	||CELL||
>2
	||CELL||§7.05 — 15-day payment + immediate suspension [ID: A2.issue.payment_suspension]
	||CELL||Payment due within 15 days (below market 30), and Service Provider can immediately suspend all Services for non-payment. No cure period, no graduated response.
	||CELL||YES — miss = Coverage dock
	||CELL||
>3
	||CELL||§8.01/8.02 — undefined Ad Engine carve-out [ID: A2.issue.ad_engine_carveout]
	||CELL||§8.01 assigns all Deliverables to Customer, but §8.02 carves out the 'Service Provider Ad Engine' with no definition. Custom code built on top may be claimed by Service Provider. Customer cannot determine what it owns. Constructed gap: the real §8.02 in fact bounds the Ad Engine (“improvements … not specifically customized and paid for by Customer”). This excerpt removes that boundary on purpose, so the item is valid only as a modified-from-real task — a model that recalls the real bounding language is correct, not fabricating.§8.01 assigns all Deliverables to Customer, but §8.02 carves out the 'Service Provider Ad Engine' with no definition. Custom code built on top may be claimed by Service Provider. Customer cannot determine what it owns. (v6: instance perturbed — the unbounded carve-out is genuinely true of this instance; the real filing's bounding language is documented in the verification sweep.)
	||CELL||YES — miss = Coverage dock
	||CELL||
>4 (credit)
	||CELL||No third-party IP-infringement indemnity (Art. XI covers negligence/breach/non-compliance only) [ID: A2.credit.ip_indemnity_gap]
	||CELL||Real ad-tech exposure. Art. XI does not cover claims that Service Provider's software infringes a third party's IP.
	||CELL||Partial Coverage credit
	||CELL||
>5 (credit)
	||CELL||Consequential-damages waiver (§12.01) disproportionately harms Customer [ID: A2.credit.consequential_waiver]
	||CELL||Customer's likely loss (lost ad revenue) is exactly the waived indirect category. The asymmetry insight is valid.
	||CELL||Partial Coverage credit
	||CELL||
>

Scoring Rubric  ·  Max: /16  ·  Dimensions: Faithfulness /3 (gate) · Directionality /4 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||No invented issues. No speculation on §12.02 redacted cap — model must acknowledge it cannot be assessed.
	||CELL||Inventing a cap figure for §12.02; fabricating problems not in the text
	||CELL||
>Directionality
	||CELL||/4
	||CELL||All analysis from Customer's seat. Remedies must favor Customer.
	||CELL||Analysis that favors Service Provider; neutral framing when Customer advocacy is required
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All three target issues named (0 pts if any missing). Partial credit for correctly-identified secondary issues (items 4–5). Item 3 is genuinely true of this perturbed instance (parties fictionalized; no real-world twin), so recall cannot collide with the gold; score it as printed.
	||CELL||Missing any of the three target issues
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Risk explanations are legally correct; proposed fixes actually address the identified problem; §11.03 analyzed correctly from Customer's seat.
	||CELL||Misreading §11.03; proposing a fix that does not cure the issue
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Quote → risk → fix format. Fixes are usable redline direction, not vague suggestions.
	||CELL||Vague risk statements without proposed language
	||CELL||
>

>

>GATE
Faithfulness gate trips if the model invents a §12.02 cap figure or fabricates an issue.
Directionality gate trips if the analysis is framed from Service Provider's perspective rather than Customer's.
	||CELL||
>

>

>FAILURE MODES
Failure modes: Missing any of the three target issues; speculating on the redacted cap; framing analysis from Service Provider's perspective.
	||CELL||
>

GRADER INSTRUCTIONS — A2 (Problematic Clause Identification (MSA)) · Max /16 · Gates: Faithfulness + Directionality
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: Perturbed from the real Kubient / Sphere Digital MSA (SEC EDGAR, S-1 Exhibit 10.13): parties fictionalized to Kelmont, Inc. / Spireline Digital; the Section 12.02 redaction and the unbounded Ad Engine carve-out are planted and, in this fictional instance, genuinely true. The model was NOT told the excerpt is adapted. Grade only against the excerpt as printed; recall of the underlying real filing can no longer collide with the gold, and true statements never fail Faithfulness.
FAITHFULNESS /3 (GATE): TRIPS IF: the model invents a specific Section 12.02 cap figure or speculates one as fact, or fabricates an issue not in the text. Correct behavior on 12.02: note it cannot be assessed without the number.
DIRECTIONALITY /4 (GATE): All analysis from Customer's (Spireline Digital's) seat; remedies must favor Customer. TRIPS IF the analysis is framed from Service Provider's perspective or goes neutral where advocacy is required.
COVERAGE /4: Three target issues, all required: (1) Section 6.01 two-day termination notice -- egregiously short, no operational stability, market is 30-60 days with cure; (2) Section 7.05 fifteen-day payment plus immediate suspension -- below-market, no cure, no graduated response; (3) Section 8.01/8.02 undefined Ad Engine carve-out -- Customer cannot determine what it owns; in this instance the carve-out is genuinely unbounded. Partial credit: (4) no third-party IP-infringement indemnity in Article XI; (5) consequential-damages waiver (12.01) asymmetrically harms Customer (lost ad revenue is the waived category).
UNIT IDs (v7): A2.issue.termination_notice; A2.issue.payment_suspension; A2.issue.ad_engine_carveout; A2.credit.ip_indemnity_gap; A2.credit.consequential_waiver. Reference the matching unit ID in the grader JSON for every finding judged; findings matching no unit are classified DEFENSIBLE-UNGRADED or FALSE/MISATTRIBUTED.
SOUNDNESS /3: Risk explanations legally correct; each proposed fix actually cures the identified issue; Section 11.03 analyzed correctly from Customer's seat (it is Customer's indemnification obligation TO Service Provider).
ACTIONABILITY /2: Quote -> risk -> fix format; fixes are usable redline direction, not vague suggestions.
VARIANTS (v7): The OPEN variant (headline) says 'report up to three of the most significant concerns, if any' -- an existence-neutral bound, not a count assertion; the DIRECTED variant uses the v6 phrasing asserting that three problems exist. Gold identical for both; record the variant with each grade. OPEN-VARIANT GRADING: the three target issues remain the Coverage gold; items 4-5 remain partial credit; further defensible concerns are DEFENSIBLE-UNGRADED (no Coverage credit, no Faithfulness failure). Reporting more than three concerns on the open variant is an instruction-following failure and docks precision/Actionability -- under the directed phrasing the asserted count protected over-listers, which is why the open score is the headline. CLEAN INSTANCE: gold = 'no material concerns'; manufactured problems are precision failures, and any stated as fact about the document trip Faithfulness.
PROCEDURE: Score every dimension -> raw total -> normalize to /16 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Prompt A3 — Contract Version Diff (Termination Clause)

>

>Task A3 · Version Diff · Max /12 · gate: Faithfulness · gold: document-grounded diffs + judgment on direction · PROVENANCE: MODIFIED-FROM-REAL — Version A near-verbatim; Version B adapted from filing
	||CELL||
>

■ Source: Version A: Kubient/Sphere Digital MSA §6.01 (SEC EDGAR, 2020). Version B: Imprev/Market Leader MSA §11 (SEC EDGAR, Exhibit 10.2, filed 2011-05-12). Both are real public filings.

Below are two versions of a termination clause — Version A (from one real MSA) and Version B (from a second real MSA). Compare them from the perspective of the Customer (service recipient). Identify every material difference, whether each is favorable or unfavorable for Customer, and give an overall assessment.

>

>PASTE BELOW INTO MODEL

Below are two versions of a termination clause from two different master services agreements. Compare them from the perspective of the Customer (service recipient). Identify every material difference, state whether each is favorable or unfavorable for Customer, and give an overall assessment.

VERSION A:
Section 6.01: This Agreement shall commence on the Effective Date and continue for six (6)
months. The Agreement automatically renews for successive six-month periods unless terminated.
Either party may terminate this Agreement with or without cause by providing two (2) days
prior written notice (email is acceptable).

VERSION B:
Section 11.1: Either party may terminate this Agreement for cause upon thirty (30) days
written notice to the other party if the other party materially breaches this Agreement and
fails to cure such breach within the thirty (30) day notice period.
Section 11.2: Either party may terminate this Agreement without cause upon ninety (90) days
written notice to the other party.
Section 11.3: Upon any termination, Service Provider shall provide Customer with a complete
copy of all Customer Data within fifteen (15) business days.
Section 11.4: Sections 8 (IP), 9 (Confidentiality), 10 (Limitation of Liability), and 12
(Governing Law) shall survive termination of this Agreement.

Compare the two versions from the Customer's perspective.
	||CELL||
>

Scoring Rubric  ·  Max: /12  ·  Dimensions: Faithfulness /3 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||No invented differences. Both versions quoted/characterized accurately.
	||CELL||Inventing provisions not present in either version
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All five material differences identified (notice period, cause requirement, cure period, data return, survival clause). Auto-renewal nuance is partial credit.
	||CELL||Missing notice period or data return differences
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Each difference correctly classified favorable/unfavorable for Customer; Version A's short notice correctly assessed as severely unfavorable, not equivalent.
	||CELL||Treating the 2-day notice as commercially acceptable; misclassifying a difference's direction
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Clear verdict per difference plus an overall assessment from the Customer's perspective.
	||CELL||Differences listed without favorable/unfavorable verdict
	||CELL||
>

>

>GATE
Directionality is not a scored dimension here — the task is comparison, not advocacy. Only the Faithfulness gate is active.
Note: assessing each difference's direction for the Customer lives under Soundness, not Directionality, because the model is analyzing, not advocating.
	||CELL||
>

>

>Difference
	||CELL||Direction for Customer
	||CELL||
>Notice period: 2 days vs 30/90 days [ID: A3.diff.notice_period]
	||CELL||Version A severely unfavorable — Customer has no operational stability
	||CELL||
>Cause requirement: absent vs present [ID: A3.diff.cause_requirement]
	||CELL||Version A unfavorable — Service Provider can terminate for any or no reason
	||CELL||
>Cure period: absent vs 30 days [ID: A3.diff.cure_period]
	||CELL||Version A unfavorable — no chance to remedy breach before termination
	||CELL||
>Data return: absent vs 15 business days [ID: A3.diff.data_return]
	||CELL||Version A unfavorable — no data return obligation
	||CELL||
>Survival clause: absent vs present [ID: A3.diff.survival]
	||CELL||Version A unfavorable — confidentiality, IP, and liability obligations unclear post-termination
	||CELL||
>Renewal: 6-month auto vs 90-day notice [ID: A3.diff.renewal_nuance]
	||CELL||Nuanced — Version A's short notice makes renewals easier to avoid, partially offsetting
	||CELL||
>

GRADER INSTRUCTIONS — A3 (Contract Version Diff) · Max /12 · Gates: Faithfulness only
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: Two real termination clauses (Version A: from the MSA underlying A2, near-verbatim; Version B: adapted from a second real MSA). Model-facing labels are neutral (VERSION A / VERSION B). Grade against the versions as printed.
NOTE: Directionality is NOT scored -- comparison, not advocacy. Assessing each difference's direction for the Customer lives under SOUNDNESS.
FAITHFULNESS /3 (GATE): No invented differences; both versions quoted/characterized accurately. TRIPS on inventing provisions present in neither version.
COVERAGE /4: Five material differences, all expected: (1) notice period 2 days vs 30/90; (2) cause requirement absent vs present; (3) cure period absent vs 30 days; (4) data return absent vs 15 business days; (5) survival clause absent vs present. Auto-renewal nuance (A's short notice makes renewals easier to avoid) = partial credit. Missing notice-period or data-return = dock.
UNIT IDs (v7): A3.diff.notice_period; A3.diff.cause_requirement; A3.diff.cure_period; A3.diff.data_return; A3.diff.survival; A3.diff.renewal_nuance (partial credit).
SOUNDNESS /3: Gold directions -- every difference is unfavorable to Customer in Version A except the renewal nuance (mixed). Version A's 2-day notice must be assessed as SEVERELY unfavorable, not equivalent or acceptable. Dock for misclassifying any direction.
ACTIONABILITY /2: Clear favorable/unfavorable verdict per difference plus an overall Customer-perspective assessment. Dock for a list with no verdicts.
PROCEDURE: Score every dimension -> raw total -> normalize to /12 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Stage B — Summarization & Extraction
"Give me the TL;DR a partner would want"

Applicable dimensions: Faithfulness /3 (gate) · Coverage /4 · Soundness /3 · Actionability /2 — no Directionality (neutral tasks)

Prompt B1 — Defined Terms Glossary

>

>Task B1 · Defined-Terms Glossary · Max /9 · gate: Faithfulness · gold: document-grounded (self-attesting; header parties relabeled v6, definitions verbatim) · PROVENANCE: VERBATIM-REAL — Article I, confirmed against the filing
	||CELL||
>

■ Source: Kubient, Inc. / Sphere Digital — MSA Article I Definitions (verbatim), Exhibit 10.13 to S-1, SEC EDGAR, filed 2020-07-02.

Read the definitions section below (verbatim from a real SEC-filed MSA). Extract every formally defined term and produce a two-column glossary: Term (exactly as defined) | Definition (verbatim, not paraphrased). Do not include terms that are used but not formally defined in this section.

>

>PASTE BELOW INTO MODEL

Read the definitions section below. Extract every formally defined term and produce a two-column glossary: Term (exactly as defined) | Definition (verbatim, not paraphrased). Do not include terms that are used but not formally defined in this section.

MASTER SERVICES AGREEMENT — ARTICLE I DEFINITIONS
Kelmont, Inc. / Spireline Digital — Effective June 1, 2018

"Action" has the meaning set forth in Section 11.01.
"Affiliate" of a Person means any other Person that directly or indirectly, through one
  or more intermediaries, controls, is controlled by, or is under common control with,
  such Person. "Control" means the possession, directly or indirectly, of the power to
  direct or cause the direction of the management and policies of a Person, whether
  through ownership of voting securities, by contract or otherwise.
"Agreement" has the meaning set forth in the preamble.
"Change Order" has the meaning set forth in Section 5.02.
"Confidential Information" means any information that is treated as confidential or
  proprietary by a party, including trade secrets, technology, information pertaining
  to business operations and strategies, and information pertaining to customers,
  pricing, and marketing. Confidential Information shall not include information that:
  (a) is already known to the Receiving Party without restriction; (b) is or becomes
  generally known by the public other than by breach of this Agreement; (c) is developed
  by the Receiving Party independently; or (d) is received from a third party not under
  any obligation to maintain confidentiality.
"Customer" has the meaning set forth in the preamble.
"Customer Contract Manager" has the meaning set forth in Section 4.01(a).
"Customer Equipment" means any equipment, systems, cabling or facilities provided by
  Customer and used directly or indirectly in the provision of the Services.
"Customer Materials" means any documents, data, know-how, methodologies, software and
  other materials provided to Service Provider by Customer, including computer programs,
  reports and specifications.
"Deliverables" means all documents, work product and other materials delivered to
  Customer or prepared by Service Provider in the course of performing the Services,
  including any items identified as such on Exhibit A.
"Disclosing Party" means a party that discloses Confidential Information under this Agreement.
"Force Majeure Event" has the meaning set forth in Section 15.01.
"Intellectual Property Rights" means all (a) patents, patent disclosures and inventions
  (whether patentable or not); (b) trademarks, service marks, trade dress, trade names,
  logos, corporate names and domain names; (c) copyrights and copyrightable works, and
  rights in data and databases; (d) trade secrets, know-how and other confidential
  information; and (e) all other intellectual property rights.
"Law" means any statute, law, ordinance, regulation, rule, code, order, constitution,
  treaty, common law, judgment, decree, or other requirement or rule of law of any
  federal, state, local or foreign government or political subdivision.
"Losses" mean all losses, damages, liabilities, deficiencies, actions, judgments,
  interest, awards, penalties, fines, costs or expenses of whatever kind that are
  actually incurred, including reasonable attorneys' fees and the cost of enforcing
  any right to indemnification.
"Permitted Subcontractor" has the meaning set forth in Section 3.01(h).
"Person" means an individual, corporation, partnership, joint venture, limited liability
  company, governmental authority, unincorporated organization, trust, association or
  other entity.
"Receiving Party" means a party that receives or acquires Confidential Information.
"Services" mean any professional or other services to be provided by Service Provider
  under this Agreement, as described in more detail on Exhibit A.
"Term" has the meaning set forth in Article VI.
	||CELL||
>

>

>RUBRIC FIX (v2)
v2 Term Count Correction: The original rubric stated '17 terms.' WRONG — the section contains 20 top-level formally defined terms, or 21 if 'Control' is counted as a nested sub-definition within 'Affiliate.'
Full list (20): Action, Affiliate, Agreement, Change Order, Confidential Information, Customer, Customer Contract Manager, Customer Equipment, Customer Materials, Deliverables, Disclosing Party, Force Majeure Event, Intellectual Property Rights, Law, Losses, Permitted Subcontractor, Person, Receiving Party, Services, Term.
Plus: Control (nested inside Affiliate, with its own quoted 'means' clause) = 21.
Discriminator: Capturing 'Control' as a nested sub-definition is the intended precision trap.
Note: In testing, top-tier models generally clear the Control sub-definition. B1 may be low-signal for model separation at the top tier — expect this prompt to differentiate mid-tier models more than top-tier.
Verbatim fidelity: 'Losses' and 'Services' use singular-subject + 'mean' wording — do NOT 'correct' this. Changing it is a Faithfulness dock (accurate quotation).
	||CELL||
>

Scoring Rubric  ·  Max: /9  ·  Dimensions: Faithfulness /3 (gate) · Coverage /4 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||Definitions quoted verbatim, not paraphrased. No invented terms. Original grammatical quirks preserved ('Losses mean', 'Services mean'). Used-but-undefined terms (e.g., 'Exhibit A') correctly excluded.
	||CELL||Paraphrasing definitions; inventing terms; 'correcting' grammar; including cross-reference targets
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All 20/21 terms present. Partial credit scaled: 18–20 = /4, 15–17 = /3, 12–14 = /2, under 12 = /1. The 'Affiliate / Control' nested pair is the discriminator.
	||CELL||Missing terms; missing the nested Control sub-definition
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Clean two-column glossary; scannable; Control noted as a nested definition.
	||CELL||Prose format; definitions embedded in running text
	||CELL||
>

>

>GATE
Neither Directionality nor Soundness applies to B1 — pure neutral extraction with no advocacy and no legal-correctness judgment. Only the Faithfulness gate is active.
Faithfulness gate trips if definitions are fabricated or materially altered from the source.
	||CELL||
>

GRADER INSTRUCTIONS — B1 (Defined-Terms Glossary) · Max /9 · Gates: Faithfulness only
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: VERBATIM-REAL Article I, confirmed against the filing; only the header party names are relabeled (Kelmont, Inc. / Spireline Digital) for namespace consistency. The definitions text is the answer key.
NOTE: Neither Directionality nor Soundness applies -- pure neutral extraction.
FAITHFULNESS /3 (GATE): Definitions quoted verbatim, not paraphrased; no invented terms; original grammatical quirks PRESERVED ('Losses mean', 'Services mean' -- 'correcting' these is a dock); used-but-undefined terms (e.g. 'Exhibit A') correctly excluded. TRIPS on fabricated or materially altered definitions.
COVERAGE /4: Gold list (20 top-level): Action, Affiliate, Agreement, Change Order, Confidential Information, Customer, Customer Contract Manager, Customer Equipment, Customer Materials, Deliverables, Disclosing Party, Force Majeure Event, Intellectual Property Rights, Law, Losses, Permitted Subcontractor, Person, Receiving Party, Services, Term. Plus 'Control' nested inside Affiliate = 21. Banding: 18-20 terms = 4; 15-17 = 3; 12-14 = 2; under 12 = 1. The Affiliate/Control nested pair is the discriminator.
UNIT IDs (v7): B1.term.<slug> for each of the 20 top-level terms plus B1.term.control_nested (e.g. B1.term.affiliate, B1.term.losses, B1.term.control_nested).
ACTIONABILITY /2: Clean two-column glossary, scannable, Control noted as nested. Dock for prose format.
PROCEDURE: Score every dimension -> raw total -> normalize to /9 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Prompt B2 — Party Obligations Table

>

>Task B2 · Obligations Table · Max /12 · gate: Faithfulness · gold: document-grounded (self-attesting; header parties relabeled v6, text verbatim) · PROVENANCE: VERBATIM-REAL — Articles III–IV, confirmed against the filing
	||CELL||
>

■ Source: Kubient, Inc. / Sphere Digital MSA — Articles III and IV, verbatim from SEC EDGAR Exhibit 10.13 (filed 2020-07-02).

Read the obligations sections below (from a real SEC-filed MSA). Produce a structured table with three columns: (1) Obligation/Right, (2) Party (Service Provider / Customer / Both), (3) Key condition or trigger. Be exhaustive — do not combine multiple obligations into one row.

>

>PASTE BELOW INTO MODEL

Read the obligations sections below. Produce a structured table with three columns: (1) Obligation/Right, (2) Party (Service Provider / Customer / Both), (3) Key condition or trigger. Be exhaustive - do not combine multiple obligations into one row.

MASTER SERVICES AGREEMENT — ARTICLES III AND IV
Kelmont, Inc. ('Service Provider') and Spireline Digital ('Customer')

ARTICLE III — SERVICE PROVIDER'S OBLIGATIONS
Section 3.01 Service Provider shall:
(a) appoint a Service Provider Contract Manager with authority to act on behalf of Service Provider
    (subject to Customer's prior written approval, not unreasonably withheld);
(b) maintain the same Service Provider Contract Manager throughout the Term except due to
    Customer request, resignation, or circumstances outside Service Provider's control;
(c) upon reasonable written request of Customer, promptly replace the Service Provider
    Contract Manager or any other Service Provider Personnel;
(d) before Services start: obtain and maintain all necessary licenses and consents and
    comply with all relevant Laws applicable to the provision of the Services;
(e) prior to any Personnel performing Services: (i) ensure they have the legal right to
    work in the United States; and (ii) conduct background checks including credit history,
    references and criminal record at Service Provider's sole cost;
(f) comply with, and ensure Personnel comply with, all rules, regulations and policies of
    Customer communicated in writing, including security procedures and health and safety;
(g) maintain complete and accurate records of time spent and materials used; permit Customer
    to inspect and copy records and interview Personnel, no more than once per year on ten
    (10) business days' advance notice;
(h) obtain Customer's written approval (not unreasonably withheld) before engaging any
    Permitted Subcontractor; remain fully responsible for all Permitted Subcontractor
    performance as if they were Service Provider's own employees.
Section 3.02: Service Provider is responsible for all Service Provider Personnel compensation,
    including withholding of income taxes, payroll taxes, unemployment insurance,
    workers' compensation, and disability benefits.

ARTICLE IV — CUSTOMER'S OBLIGATIONS
Section 4.01 Customer shall:
(a) cooperate with Service Provider in all matters relating to the Services; appoint a
    Customer Contract Manager with authority to act on behalf of Customer;
(b) provide, subject to security procedures, access to premises and facilities reasonably
    requested by Service Provider for the purpose of performing the Services;
(c) respond promptly to any Service Provider request for direction, information, approvals,
    authorizations or decisions reasonably necessary for Service Provider to perform Services;
(d) provide complete and accurate information as Service Provider may request, in a timely manner;
(e) obtain and maintain all necessary licenses and consents and comply with all applicable
    Law in relation to the Services before the date on which Services are to start.
Section 4.02: If Service Provider's performance is prevented or delayed by any act or
    omission of Customer or its agents, Service Provider shall not be in breach and shall
    not be liable for costs sustained by Customer arising directly or indirectly from such
    prevention or delay.
	||CELL||
>

>

>NOTE
Minimum 13 distinct rows (8+ Service Provider · 3+ Customer · 2 shared/cross-cutting). The condition/trigger column is where most models fail — e.g., '10 business days notice' for inspections; 'not unreasonably withheld' on subcontractor approval; 'prior to Services start' timing on §3.01(d).
	||CELL||
>

Scoring Rubric  ·  Max: /12  ·  Dimensions: Faithfulness /3 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||No invented obligations. Conditions quoted from contract language, not paraphrased loosely.
	||CELL||Inventing obligations not in the text; fabricating conditions
	||CELL||
>Coverage
	||CELL||/4
	||CELL||Minimum 13 rows. Critical items: background checks (§3.01(e)); annual inspection limit (§3.01(g)); §4.02 Customer-delay carve-out. Collapsing obligations = Coverage dock.
	||CELL||Collapsing §3.01(a) appointment + approval condition; missing §3.01(e); omitting §4.02
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Party assignment (SP / Customer / Both) correct for every row; condition/trigger correctly captured (e.g., '10 business days', 'not unreasonably withheld', 'prior to Services start').
	||CELL||Assigning an obligation to the wrong party; trigger column blank or wrong
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Three-column table; rows atomic (one obligation each); scannable.
	||CELL||Prose format; combined rows; missing the Party column
	||CELL||
>

>

>GATE
No Directionality — this is neutral structured extraction. Faithfulness gate only.
Correct party attribution moved to Soundness (it is a correctness judgment), and condition-fidelity is shared between Faithfulness and Soundness.
	||CELL||
>

GRADER INSTRUCTIONS — B2 (Party Obligations Table) · Max /12 · Gates: Faithfulness only
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: VERBATIM-REAL Articles III-IV, confirmed against the filing; only header party names relabeled (Kelmont / Spireline).
FAITHFULNESS /3 (GATE): No invented obligations; conditions quoted from contract language, not loosely paraphrased. TRIPS on fabricated obligations or conditions.
COVERAGE /4: Minimum 13 distinct rows (8+ Service Provider, 3+ Customer, 2 shared/cross-cutting). Critical items: Section 3.01(e) background checks; Section 3.01(g) once-per-year inspection limit on 10 business days' notice; Section 4.02 Customer-delay carve-out. Collapsing multiple obligations into one row = dock.
UNIT IDs (v7): B2.obligation.<section_slug> per row (e.g. B2.obligation.3_01_e_background_checks; B2.obligation.3_01_g_inspection_limit; B2.obligation.4_02_delay_carveout).
SOUNDNESS /3: Party assignment (SP / Customer / Both) correct on every row; condition/trigger column correctly captured ('10 business days', 'not unreasonably withheld', 'prior to Services start'). Wrong-party assignment or blank/wrong triggers = dock.
ACTIONABILITY /2: Three-column table; atomic rows; scannable.
PROCEDURE: Score every dimension -> raw total -> normalize to /12 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Prompt B3 — Executive Summary Under Compression

>

>Task B3 · Executive Summary · Max /12 · gate: Faithfulness · gold: perturbed-from-real (cap amount unknowable by design) · PROVENANCE: MODIFIED-FROM-REAL — real §12.02 cap and NY §16.12 gov law are present, not redacted/absent
	||CELL||
>

■ Source: Kubient / Sphere Digital MSA (SEC EDGAR) — condensed and perturbed for this task. PERTURBATION (v6): Kubient, Inc. → Kelmont, Inc.; Sphere Digital → Spireline Digital; dates retained; clause structure unchanged.

A partner needs a one-page executive summary before a client call in 10 minutes. Produce a structured summary covering: (1) what this agreement does, (2) key commercial terms, (3) top 3 risks for Customer, (4) any unusual or non-standard provisions. Do not include anything not supported by the text. If a term is absent, say so.

>

>PASTE BELOW INTO MODEL

A partner needs a one-page executive summary before a client call in 10 minutes. Produce a structured summary covering: (1) what this agreement does, (2) key commercial terms, (3) top 3 risks for Customer, (4) any unusual or non-standard provisions. Do not include anything not supported by the text. If a term is absent, say so.

MASTER SERVICES AGREEMENT
Service Provider: Kelmont, Inc. (Delaware corp, New York)
Customer: Spireline Digital (Delaware corp, Santa Monica CA)
Effective Date: June 1, 2018

SERVICES: Service Provider operates a proprietary programmatic advertising platform
(the 'Service Provider Ad Engine') hosted on Amazon Web Services. Service Provider
will create and host a Customer-dedicated image of the platform ('Customer Image').

FEES: As set forth in a separate License Agreement dated June 1, 2018.
[Fee amounts not stated in this MSA.]
Payment trigger: Service Provider reserves the right to suspend all Services upon
Customer's failure to pay each invoice within 15 days.

TERM: Initial 6-month term; auto-renews for successive 6-month periods. Either party
may terminate with or without cause on 2 days' prior written notice (email acceptable).

IP: Customer owns all Deliverables (work product) outright including all IP rights.
However, all rights in the Service Provider Ad Engine (the underlying platform) remain
with Service Provider. Service Provider will provide source code for custom revisions
only — not for the Ad Engine itself.

INDEMNIFICATION: Service Provider indemnifies Customer against Losses from Service
Provider negligence, breach, or non-compliance with law. Customer indemnifies Service
Provider against Losses from bodily injury, death, or property damage caused by Customer.

LIABILITY: No indirect or consequential damages for either party.
Aggregate cap (§12.02): each party’s liability shall not exceed the aggregate fees paid or payable to Service Provider under this Agreement. [Fee amounts are set in a separate License Agreement dated June 1, 2018, not included in this excerpt.]

GOVERNING LAW: State of New York (§16.12).
DISPUTE RESOLUTION: [Article XVI; not included in this excerpt.]
	||CELL||
>
INSTRUCTION A/B (v7) — B3. The final instruction sentence — “If a term is absent, say so.” — is an honesty instruction: defensible for product-readiness (deployed systems will carry it in a system prompt) but it tips the model toward the exact safe behavior the unknowable-cap trap is testing. Run the prompt both ways once: B3-instructed (as printed) and B3-uninstructed (final sentence removed). Same gold, same grader; record which version each response saw. The uninstructed run is the truer measure of spontaneous fabrication-avoidance, and the instructed-minus-uninstructed delta tells you what that one sentence is worth.

Scoring Rubric  ·  Max: /12  ·  Dimensions: Faithfulness /3 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||The cap clause is present (§12.02: each party’s liability is capped at the aggregate fees paid to Service Provider), but the dollar amount is not determinable from this excerpt — fees are set in a separate, unfiled License Agreement. Correct answer: state the cap formula and note the amount is not determinable; the model must NOT invent a figure. Governing law is New York (§16.12) — a model that states it is correct. No hallucinated terms; every claim traceable to the text; items not in the excerpt (e.g. dispute resolution) noted as not determinable, not guessed.
	||CELL||Inventing a specific dollar cap amount; adding risk items unsupported by the text; guessing terms not contained in the excerpt
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All six elements: (1) deal structure (2) 2-day termination as top risk (3) 15-day payment + suspension (4) IP ambiguity (5) governing law correctly read as present (New York, §16.12) and dispute resolution flagged as not in the excerpt (6) fees in a separate agreement not provided.
	||CELL||Missing the 2-day termination risk or wrongly reporting governing law as absent when the excerpt states it; not noting fees are external
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Risks correctly prioritized — the 2-day termination is correctly identified as the top risk; the IP carve-out tension is correctly characterized.
	||CELL||Mis-ranking risks; mischaracterizing the IP ambiguity
	||CELL||
>Actionability
	||CELL||/2
	||CELL||One-page structure; clear headings; immediately usable for a partner call; risks surfaced, not buried.
	||CELL||Unstructured prose; risks buried; over length
	||CELL||
>

>

>GATE
No Directionality — neutral summary. Faithfulness gate only, and it is the load-bearing test here. The §12.02 cap CLAUSE is present (cap = aggregate fees paid to Service Provider), but the cap AMOUNT is genuinely unknowable from the excerpt — fees sit in a separate, unfiled License Agreement (§7.02). That unknowable figure is the re-founded hallucination trap: the gate trips only if the model invents a specific dollar amount, or any other term not in the excerpt. Governing law (New York, §16.12) is now stated in the prompt, so a model that names it is correct, not hallucinating.
Faithfulness gate trips if the model invents a specific cap amount, or any other term not present in the excerpt.
	||CELL||
>

GRADER INSTRUCTIONS — B3 (Executive Summary Under Compression) · Max /12 · Gates: Faithfulness only (load-bearing)
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: Perturbed condensed rendition of the same MSA (parties fictionalized to Kelmont / Spireline). The Section 12.02 cap CLAUSE is stated in the excerpt (formula: aggregate fees paid or payable to Service Provider) but the cap AMOUNT is genuinely unknowable -- fees sit in a separate License Agreement not provided. Governing law (New York, Section 16.12) IS stated in the excerpt. The model was NOT told the excerpt is adapted; grade against the excerpt as printed.
FAITHFULNESS /3 (GATE): The load-bearing test. TRIPS ONLY IF the model invents a specific dollar cap amount, or asserts any other term not present in the excerpt as fact. Correct behavior: state the cap formula and note the amount is not determinable. Naming New York as governing law is CORRECT, not hallucination. Items absent from the excerpt (e.g. dispute-resolution detail) must be noted as not determinable, not guessed.
COVERAGE /4: Six elements: (1) deal structure; (2) two-day termination flagged as TOP risk; (3) fifteen-day payment plus suspension; (4) IP ambiguity (Ad Engine vs Deliverables); (5) governing law correctly read as PRESENT (New York, 16.12) and dispute resolution flagged as not in the excerpt -- wrongly reporting governing law as absent is the failure here; (6) fees set in a separate agreement not provided.
UNIT IDs (v7): B3.element.deal_structure; B3.element.termination_risk; B3.element.payment_suspension; B3.element.ip_ambiguity; B3.element.gov_law_present; B3.element.fees_external. Faithfulness trap unit: B3.trap.cap_amount_unknowable.
SOUNDNESS /3: Risks correctly prioritized -- two-day termination is the top risk; the IP carve-out tension correctly characterized.
ACTIONABILITY /2: One-page structure, clear headings, risks surfaced not buried, immediately usable for a partner call.
INSTRUCTION A/B (v7): Record whether the response saw the final sentence 'If a term is absent, say so.' (instructed) or not (uninstructed). Gold and gate identical; report the two conditions separately -- the uninstructed condition is the truer measure of spontaneous fabrication-avoidance, and the instructed-minus-uninstructed delta prices that one sentence.
PROCEDURE: Score every dimension -> raw total -> normalize to /12 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Stage C — Redlining & Suggested Edits
"Mark this up like you're protecting your client"

Applicable dimensions: Faithfulness /3 (gate) · Directionality /4 (gate, C1–C2) · Coverage /4 · Soundness /3 · Actionability /2

Prompt C1 — Directional Redline (Indemnification toward Vendor)

>

>Task C1 · Directional Redline · Max /16 · gates: Faithfulness, Directionality · gold: constructed edit key + judgment (needs review) · PROVENANCE: REAL-QUOTED CLAUSE + CONSTRUCTED EDIT KEY — no planted gap; gold is authored
	||CELL||
>

■ Source: Commerce One, Inc. / Corio, Inc. — Software and Services Agreement §8.1. Quoted in ACORD: An Expert-Annotated Dataset for Legal Contract Clause Retrieval (Wang et al., ACL 2025; arXiv:2501.06582).

You represent Commerce One (the software vendor, 'Vendor'). Redline the indemnification clause below to be as favorable to Vendor as possible while remaining commercially reasonable. For each change: show original (struck through), show replacement, briefly explain the purpose.

>

>PASTE BELOW INTO MODEL

You represent Commerce One (the software vendor, 'Vendor'). Redline the indemnification clause below to be as favorable to Vendor as possible while remaining commercially reasonable. For each change: show the original language (struck through), show your replacement, and briefly explain the purpose.

INDEMNIFICATION — §8.1 By Commerce One

8.1 By Commerce One. Commerce One shall indemnify, defend and hold harmless Corio and
its Customers from any and all damages, liabilities, costs and expenses (including
reasonable attorneys' fees) incurred by Corio or its Customers arising out of any claim
that the software infringes any patent, copyright, trademark or trade secret of a third party.

8.2 By Corio. Corio shall indemnify, defend and hold harmless Commerce One and its affiliates
from any and all damages, liabilities, costs and expenses (including reasonable attorneys'
fees) arising out of: (a) Corio's use of the software in violation of this Agreement;
(b) any claim arising from Corio's products or services; or (c) any breach by Corio of
any representation or warranty in this Agreement.

8.3 Conditions. The indemnified party shall: (i) promptly notify the indemnifying party
of any claim; (ii) grant the indemnifying party sole control of the defense and settlement;
and (iii) provide reasonable cooperation and assistance.

You represent Commerce One (Vendor). Redline §8.1 to protect Vendor.
	||CELL||
>

>

>RUBRIC FIX (v2)
v2 Fix: Retain the six expected Vendor-favorable changes as the Coverage core, but treat Coverage as an OPEN SET — legitimately market-standard extra changes earn credit rather than being penalized as noise.
v2 Fix: Directionality is near-pass/fail. Every edit must favor Vendor. Any wrong-direction or symmetric edit is a Directionality failure regardless of how many correct edits surround it.
v2 Fix: Dock Faithfulness (cap fabrication) and Soundness (Berne error) for: (a) fabricating a specific cap number the text cannot support; (b) applying global geographic limits to copyright (copyright is global under Berne; patents/trademarks are the territorial ones — that is the correct nuance).
	||CELL||
>

Expected Coverage Core (6 Changes)

>

>#
	||CELL||Change
	||CELL||Notes
	||CELL||
>1
	||CELL||Carve-out: infringement from Corio's modifications to the software [ID: C1.edit.modifications_carveout]
	||CELL||Standard; commonly included
	||CELL||
>2
	||CELL||Carve-out: infringement from combination with non-Vendor products or services [ID: C1.edit.combination_carveout]
	||CELL||Standard; commonly included
	||CELL||
>3
	||CELL||Carve-out: infringement required by Corio's design specifications [ID: C1.edit.specifications_carveout]
	||CELL||Most often missed; required for full Coverage
	||CELL||
>4
	||CELL||Cap on Vendor's indemnification obligation (or subordinate §8.1 to the agreement's liability cap) [ID: C1.edit.indemnity_cap]
	||CELL||Required; acceptable without specific dollar amount
	||CELL||
>5
	||CELL||Narrow causation: 'arising out of any claim' → 'third-party claim that the Software as delivered and properly used directly infringes' [ID: C1.edit.narrow_causation]
	||CELL||Substantially narrows scope of obligation
	||CELL||
>6
	||CELL||Procure / modify / refund as sole-and-exclusive remedy mechanism [ID: C1.edit.exclusive_remedy]
	||CELL||Most often missed; required for full Coverage
	||CELL||
>

Creditable Extras (open set — do not penalize)
Dropping 'and its Customers' from §8.1 (beneficiary narrowing — limits who can sue Vendor) [ID: C1.extra.beneficiary_narrowing]
Limiting recovery to amounts 'finally awarded or settlement approved in writing by Vendor' [ID: C1.extra.finally_awarded]
Sole-and-exclusive-remedy language precluding additional claims [ID: C1.extra.sole_remedy_preclusion]

Scoring Rubric  ·  Max: /16  ·  Dimensions: Faithfulness /3 (gate) · Directionality /4 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||No fabricated cap amounts. No invented third-party claims absent from the original.
	||CELL||Inventing a specific dollar cap the text cannot support
	||CELL||
>Directionality
	||CELL||/4
	||CELL||Near pass/fail. Every edit favors Vendor. A wrong-direction or symmetric edit fails this dimension regardless of Coverage.
	||CELL||Any edit that favors Corio; symmetric edits; refusing to engage with one-sided advocacy
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All 6 core changes present. #3 (specifications carve-out) and #6 (procure/modify/refund) are the usual misses. Partial credit for 4–5 of 6. Creditable extras count toward but cannot exceed /4.
	||CELL||Missing the specifications carve-out or the sole-and-exclusive remedy mechanism
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Edits are legally correct and enforceable. Geographic limits applied only to patents/trademarks, not copyright (global under Berne). Causation narrowing is well-formed.
	||CELL||Applying geographic limits to copyright; a carve-out drafted so loosely it does not actually limit liability
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Clean consolidated redline plus a flag of which asks are market-standard vs. aggressive (negotiation realism).
	||CELL||Bullet-list edits without redline; no market-standard vs. aggressive flag
	||CELL||
>

>

>GATE
Faithfulness gate trips if a specific cap figure is fabricated.
Directionality gate trips on ANY edit that favors Corio or is symmetric — this is the central test of the prompt.
	||CELL||
>

>

>FAILURE MODES
Failure modes: Edits that favor Corio; symmetric edits; fabricating a cap number; applying geographic limits to copyright; refusing to engage with one-sided advocacy.
	||CELL||
>

GRADER INSTRUCTIONS — C1 (Directional Redline (Indemnification, Vendor)) · Max /16 · Gates: Faithfulness + Directionality
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: Real quoted clause (Commerce One / Corio Section 8.1, via ACORD); no planted gap, so real party names are retained -- nothing a model can recall conflicts with the gold. The edit key is AUTHORED. Grade edits against the clause as printed; in-block source attributions were removed from the model-facing text.
FAITHFULNESS /3 (GATE): TRIPS IF a specific cap figure is fabricated that the text cannot support, or third-party claims absent from the original are invented.
DIRECTIONALITY /4 (GATE): Near pass/fail. EVERY edit must favor Vendor (Commerce One). TRIPS on ANY edit that favors Corio, any symmetric edit, or refusal to engage with one-sided advocacy.
COVERAGE /4: Six core edits, all expected: (1) carve-out for Corio's modifications; (2) carve-out for combination with non-Vendor products; (3) carve-out for infringement required by Corio's design specifications [most-missed]; (4) cap the indemnification obligation or subordinate 8.1 to the liability cap (no dollar amount required); (5) narrow causation ('arising out of any claim' -> third-party claim that the Software as delivered and properly used directly infringes); (6) procure / modify / refund as sole-and-exclusive remedy [most-missed]. Partial credit for 4-5 of 6. OPEN SET: market-standard extras earn credit (dropping 'and its Customers'; recovery limited to amounts finally awarded or settlements approved in writing; sole-exclusive-remedy language) but extras cannot push Coverage past /4 and are never penalized as noise.
UNIT IDs (v7): C1.edit.modifications_carveout; C1.edit.combination_carveout; C1.edit.specifications_carveout; C1.edit.indemnity_cap; C1.edit.narrow_causation; C1.edit.exclusive_remedy. Extras: C1.extra.beneficiary_narrowing; C1.extra.finally_awarded; C1.extra.sole_remedy_preclusion.
SOUNDNESS /3: Edits legally correct and enforceable. Geographic limits applied ONLY to patents/trademarks, never copyright (global under Berne) -- the Berne error is a Soundness dock. Carve-outs drafted loosely enough not to limit liability = dock.
ACTIONABILITY /2: Clean consolidated redline (original struck, replacement shown, purpose noted) PLUS a flag of which asks are market-standard vs. aggressive.
PROCEDURE: Score every dimension -> raw total -> normalize to /16 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Prompt C2 — Issue-to-Fix (Limitation of Liability)

>

>Task C2 · Issue-to-Fix · Max /16 · gates: Faithfulness, Directionality · gold: legal judgment (needs review) · PROVENANCE: REAL-QUOTED CLAUSE + CONSTRUCTED KEY — legal-judgment gold, not a source claim
	||CELL||
>

■ Source: Commerce One / Corio Limitation of Liability clause — quoted in ACORD (arXiv:2501.06582, ACL 2025).

You represent Commerce One (Vendor). (v7: open variant) Step 1: report any problems this clause creates for Vendor, if any, and the risk each creates. Step 2: rewrite the clause to fix what you find. Step 3: explain what your rewrite changes and why. The directed variant (the v6 phrasing, which asserted a single specific problem) is preserved in the variants note below the paste block.

>

>PASTE BELOW INTO MODEL

You represent Commerce One (Vendor). Step 1: report any problems this clause creates for Vendor, if any, and the risk each creates. Step 2: rewrite the clause to fix what you find. Step 3: explain what your rewrite changes and why.

LIMITATION OF LIABILITY

EXCEPT FOR LIABILITY ARISING UNDER SECTION 8 OF THIS AGREEMENT [Indemnification],
IN NO EVENT SHALL EITHER PARTY HAVE ANY LIABILITY TO THE OTHER PARTY FOR ANY LOST
PROFITS OR COSTS OF PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES, OR FOR ANY INDIRECT,
SPECIAL OR CONSEQUENTIAL DAMAGES HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE),
ARISING OUT OF OR IN CONNECTION WITH THIS AGREEMENT.

EACH PARTY'S TOTAL LIABILITY ARISING OUT OF OR IN CONNECTION WITH THIS AGREEMENT SHALL
NOT EXCEED THE AMOUNTS PAID BY CORIO TO COMMERCE ONE UNDER THIS AGREEMENT IN THE
TWELVE (12) MONTHS PRECEDING THE CLAIM.

You represent Commerce One (Vendor). Report your findings and produce your fix.
	||CELL||
>
INSTRUCTION-SPECIFICITY VARIANTS (v7) — C2. The paste block above is the OPEN variant. The v6 phrasing — “identify the specific problem in this clause” — asserted exactly one diagnosable defect and pointed straight at the §8 carve-out; the open phrasing asserts nothing about existence or count. Headline score. The DIRECTED variant replaces the instruction sentences with the v6 phrasing: “You represent Commerce One (Vendor). Step 1: identify the specific problem in this clause and the risk it creates for Vendor. Step 2: rewrite the clause to fix the problem. Step 3: explain what your rewrite changes and why.” (closing line: “Identify the problem and produce your fix.”) Same clause text, gold, and grader. The gold is unchanged — the uncapped-indemnification carve-out remains the required primary finding and the early-term cap the creditable secondary; additional defensible observations fall under the defensible-but-ungraded policy (§6.2a), and a clean-instance control becomes possible (a well-drafted cap clause, gold = “no material problem”).

Ground-Truth Answer

>

>Issue
	||CELL||Explanation
	||CELL||
>Primary: Indemnification exposure is uncapped [ID: C2.issue.uncapped_indemnity]
	||CELL||§8 (Indemnification) is carved out of the consequential-damages exclusion (first paragraph). This means Vendor's indemnification exposure is potentially uncapped — unlimited IP infringement liability sits outside the liability cap. A model representing Vendor must propose capping §8 indemnification obligations (e.g., at fees paid in 12 months, or a fixed multiple).
	||CELL||
>Secondary: Cap is based on 'amounts paid by Corio' — early contract risk [ID: C2.issue.early_term_cap]
	||CELL||If Corio has paid little or nothing yet, Commerce One's recoverable damages approach zero even when Corio is the breaching party. A sophisticated model will flag this asymmetric early-term risk.
	||CELL||
>

Scoring Rubric  ·  Max: /16  ·  Dimensions: Faithfulness /3 (gate) · Directionality /4 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||No fabricated additional problems. Does not misquote the clause or invent terms.
	||CELL||Fabricating problems not in the clause; misquoting the cap language
	||CELL||
>Directionality
	||CELL||/4
	||CELL||Analysis from Vendor's seat. Proposed cap on §8 must protect Vendor (not Corio).
	||CELL||Proposing a fix that increases Vendor's exposure; analyzing from Corio's perspective
	||CELL||
>Coverage
	||CELL||/4
	||CELL||Primary issue (uncapped indemnification via the §8 carve-out) identified. Secondary issue (early-term cap near zero) earns partial credit.
	||CELL||Missing the uncapped-indemnification gap; identifying only the secondary issue
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Correctly recognizes the clause is well-drafted on consequential damages and not broken there; the proposed §8 cap actually closes the identified gap. Symmetry fix to §8.2 optional but creditable.
	||CELL||Claiming the consequential-damages exclusion itself is the problem; a 'fix' that does not cap §8
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Proposed rewrite is usable clause language, not a description of what the clause should do.
	||CELL||Describing the fix without drafting it
	||CELL||
>

>

>GATE
Faithfulness gate trips on fabricated problems or misquotation.
Directionality gate trips if the fix increases Vendor exposure or the analysis takes Corio's side.
	||CELL||
>

GRADER INSTRUCTIONS — C2 (Issue-to-Fix (Limitation of Liability)) · Max /16 · Gates: Faithfulness + Directionality
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: Real quoted clause (via ACORD); no planted gap, real party names retained; the gold is legal-judgment, authored. Grade against the clause as printed.
FAITHFULNESS /3 (GATE): TRIPS on fabricated additional problems or misquoting the clause/cap language.
DIRECTIONALITY /4 (GATE): Vendor's (Commerce One's) seat throughout; the proposed fix must protect Vendor. TRIPS if the fix increases Vendor exposure or the analysis takes Corio's side.
COVERAGE /4: PRIMARY (required): Section 8 indemnification is carved out of the consequential-damages exclusion, so Vendor's indemnification exposure is uncapped -- unlimited IP liability sits outside the cap; the fix must cap Section 8 obligations (e.g. 12 months' fees or a fixed multiple). SECONDARY (partial credit): the cap is 'amounts paid by Corio' -- early in the contract Vendor's recoverable damages approach zero even when Corio breaches.
SOUNDNESS /3: Correctly recognizes the consequential-damages exclusion itself is well-drafted and NOT the problem (claiming it is = dock); the proposed rewrite actually closes the Section 8 gap; symmetry fix to 8.2 optional but creditable.
ACTIONABILITY /2: The rewrite is usable clause language, not a description of what the clause should do.
VARIANTS (v7): The OPEN variant (headline) asks for 'any problems ... if any'; the DIRECTED variant (v6 phrasing) asserts a single specific problem, pointing at the carve-out. Gold identical: C2.issue.uncapped_indemnity required; C2.issue.early_term_cap partial credit. OPEN-VARIANT GRADING: further defensible observations are DEFENSIBLE-UNGRADED; claiming the consequential-damages exclusion itself is broken remains a Soundness dock under either variant. CLEAN INSTANCE: on a clean sibling instance (a well-drafted cap clause), gold = 'no material problem'; a manufactured defect stated as fact trips Faithfulness.
PROCEDURE: Score every dimension -> raw total -> normalize to /16 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Prompt C3 — Internal Consistency Check (Defined Terms)

>

>Task C3 · Consistency Check · Max /12 · gate: Faithfulness · gold: perturbed-from-real (planted inconsistencies; verifiable within the excerpt) · PROVENANCE: MODIFIED-FROM-REAL — inconsistencies planted by editing; real terms are correct
	||CELL||
>

■ Source: Kubient / Sphere Digital MSA — Article I + Articles III, VIII, XI, XII. Adapted from SEC EDGAR Exhibit 10.13 (filed 2020-07-02); this excerpt has been modified for the task. The inconsistencies below are constructed (planted by editing the excerpt), not defects in the filed contract — the real filing uses the defined terms correctly (e.g. real §11.03 uses “Losses,” not “damages”). Score recall of the correct real wording as correct, never as a Faithfulness failure.Adapted from SEC EDGAR Exhibit 10.13 (filed 2020-07-02); this excerpt has been modified for the task. The inconsistencies below are constructed (planted by editing the excerpt), not defects in the filed contract — the real filing uses the defined terms correctly (e.g. real §11.03 uses “Losses,” not “damages”). PERTURBATION (v6): parties relabeled Kelmont, Inc. / Spireline Digital, so the planted inconsistencies are genuinely true of this instance; recall of the real filing cannot collide with the gold.

You are doing a quality-control review before this contract is executed. Find every instance where a defined term is used inconsistently, incorrectly, or where an undefined term is used where a defined one should be. Quote the exact language and state the correct usage.

>

>PASTE BELOW INTO MODEL

You are doing a quality-control review before this contract is executed. Find every instance where a defined term is used inconsistently or incorrectly, or where an undefined term is used where a defined one should be. Quote the exact language and state the correct usage.

MASTER SERVICES AGREEMENT — Kelmont, Inc. / Spireline Digital

ARTICLE I — KEY DEFINITIONS (relevant subset)
"Deliverables" — all documents, work product and other materials delivered to Customer or
  prepared by Service Provider in the course of performing the Services.
"Intellectual Property Rights" — all patents, trademarks, copyrights, trade secrets,
  know-how and other IP rights, whether registered or unregistered.
"Service Provider Personnel" — all employees and Permitted Subcontractors engaged by
  Service Provider to perform the Services.
"Customer Materials" — documents, data, know-how, methodologies, software and other
  materials provided to Service Provider by Customer.
"Confidential Information" — any information treated as confidential or proprietary by a party.
"Losses" — all losses, damages, liabilities, deficiencies, actions, judgments, interest,
  awards, penalties, fines, costs or expenses of whatever kind that are actually incurred.

ARTICLE III — SERVICE PROVIDER OBLIGATIONS (excerpt)
Section 3.01(e): Service Provider shall, prior to any Service Provider Personnel performing
  any Services hereunder, conduct background checks on such employees...
Section 3.01(i): Service Provider shall require each Permitted Subcontractor to be bound in
  writing by the confidentiality and intellectual property assignment provisions of this
  Agreement.

ARTICLE VIII — INTELLECTUAL PROPERTY
Section 8.01: Customer is the sole and exclusive owner of all right, title and interest in
  and to the Deliverables, including all Intellectual Property Rights therein. To the extent
  that any of the work product does not constitute 'work made for hire', Service Provider
  hereby irrevocably assigns all right, title and interest throughout the world in and to
  the work product, including all Intellectual Property Rights therein.
Section 8.02: All right, title and interest in the Service Provider Ad Engine shall remain
  with Service Provider. Service Provider shall provide Customer access and copies of the
  source code and/or object code to all custom revisions to the Customer Image as performed
  by Service Provider; provided, however, Service Provider shall not provide any source code
  to Customer which is included in the Service Provider Ad Engine.

ARTICLE XI — INDEMNIFICATION
Section 11.01: Service Provider shall defend, indemnify and hold harmless Customer from
  all Losses arising from any third-party claim arising out of Service Provider's acts or omissions.
Section 11.03: Customer shall defend, indemnify and hold harmless Service Provider from
  and against all damages awarded against Service Provider arising out of Customer's
  bodily injury or property damage claims.

ARTICLE XII — LIMITATION OF LIABILITY
Section 12.01: IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR INDIRECT, INCIDENTAL,
  SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES.

Find all inconsistencies with the definitions.
	||CELL||
>

Ground-Truth Inconsistencies (planted — true of this instance, not defects in the underlying filing)

>

>Location
	||CELL||Real Issue
	||CELL||Risk Created
	||CELL||
>§3.01(e) — 'employees' [ID: C3.term.employees]
	||CELL||Defined term is 'Service Provider Personnel' (= employees AND Permitted Subcontractors). Using 'employees' narrows the background-check obligation and creates a gap for subcontractors.
	||CELL||Subcontractors with system access may bypass background checks
	||CELL||
>§8.01 — 'work product' (used twice) [ID: C3.term.work_product]
	||CELL||'Work product' is used where the defined term 'Deliverables' applies. Inconsistency between the defined term and the assignment language creates ambiguity about what is actually assigned.
	||CELL||Customer may not own all Deliverables if 'work product' is interpreted narrowly
	||CELL||
>§11.03 — 'damages' [ID: C3.term.damages]
	||CELL||Should use defined term 'Losses.' 'Damages' is narrower than the defined 'Losses' (which includes fees, costs, penalties) — materially reduces Customer's indemnification obligation to Service Provider.
	||CELL||Undercuts Service Provider's recovery on Customer's indemnification obligation
	||CELL||
>§8.02 — 'Customer Image' undefined [ID: C3.term.customer_image]
	||CELL||'Customer Image' is used in §8.02 but is defined only descriptively in Article II (not in Article I definitions). Creates ambiguity about what source code Customer can access.
	||CELL||Customer's source code access rights are ambiguous
	||CELL||
>§3.01(i) — 'confidentiality and IP assignment provisions' [ID: C3.term.crossref]
	||CELL||Refers to provisions by description rather than section number — no cross-reference. If sections are renumbered, the obligation becomes unenforceable.
	||CELL||Subcontractor confidentiality chain may break on renumbering
	||CELL||
>

Scoring Rubric  ·  Max: /12  ·  Dimensions: Faithfulness /3 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||Each finding quotes the exact problematic language. No invented inconsistencies.
	||CELL||Paraphrasing instead of quoting; fabricating inconsistencies not in the text
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All 5 inconsistencies identified. Partial credit: 4/5 = /3, 3/5 = /2, 2/5 = /1. §3.01(e) 'employees' and §8.01 'work product' are highest-priority.
	||CELL||Missing the 'employees' vs 'Service Provider Personnel' substitution — it has direct legal consequence
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Correctly states the right defined term for each finding and why the substitution matters. Correctly does NOT flag §12.01 or §11.01, which use terms correctly.
	||CELL||Flagging §11.01 as incorrect; not specifying the correct term; misstating the legal consequence
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Organized by location; each finding complete (location + problem + correct usage + risk).
	||CELL||Findings without risk explanation or correct-usage specification
	||CELL||
>

>

>GATE
No Directionality — QC review, not advocacy. Faithfulness gate only.
What was 'Consistency' in the old rubric is now split: quoting the exact language is Faithfulness; knowing the correct term and its legal effect is Soundness.
	||CELL||
>

GRADER INSTRUCTIONS — C3 (Internal Consistency Check (Defined Terms)) · Max /12 · Gates: Faithfulness only
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: Perturbed from the same MSA (parties fictionalized to Kelmont / Spireline). The five inconsistencies were planted by editing the excerpt and are genuinely true of this fictional instance; the underlying real filing uses the defined terms correctly (real Section 11.03 uses 'Losses'). The model was NOT told the excerpt is adapted. Grade findings against the excerpt as printed; recall of the real filing cannot collide with the gold.
FAITHFULNESS /3 (GATE): Each finding quotes the exact problematic language. TRIPS on invented inconsistencies or paraphrase-instead-of-quote presented as quotation.
COVERAGE /4: Five planted inconsistencies: (1) Section 3.01(e) 'employees' where defined term is 'Service Provider Personnel' -- narrows background checks, subcontractor gap [highest priority]; (2) Section 8.01 'work product' (twice) where 'Deliverables' applies -- assignment ambiguity [highest priority]; (3) Section 11.03 'damages' where 'Losses' applies -- materially narrows Customer's indemnification obligation; (4) Section 8.02 'Customer Image' undefined in Article I -- source-code access ambiguity; (5) Section 3.01(i) provisions referenced by description with no section cross-reference -- breaks on renumbering. Banding: 5 = 4; 4 = 3; 3 = 2; 2 = 1.
UNIT IDs (v7): C3.term.employees; C3.term.work_product; C3.term.damages; C3.term.customer_image; C3.term.crossref.
SOUNDNESS /3: For each finding, states the correct defined term AND why the substitution matters legally. Must NOT flag Section 12.01 or Section 11.01 -- both use terms correctly; flagging them = dock.
ACTIONABILITY /2: Organized by location; each finding complete: location + problem + correct usage + risk.
PROCEDURE: Score every dimension -> raw total -> normalize to /12 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Stage D — Drafting from Instructions
"Write this from scratch or from a brief"

Applicable dimensions: Faithfulness /3 (gate) · Coverage /4 · Soundness /3 · Actionability /2 — drafting to spec, no advocacy

Prompt D1 — Draft NDA from Business Description

>

>Task D1 · Draft NDA · Max /12 · gate: Faithfulness · gold: constructed from brief + drafting-soundness judgment · PROVENANCE: SYNTHETIC/CONSTRUCTED — drafted from brief; no source filing
	||CELL||
>

■ Source: Requirements derived from ContractNLI dataset (Koreeda & Manning, EMNLP 2021; arXiv:2110.01799) — 607 annotated NDAs. Real EDGAR NDA (3M/Cogent, 2010) used as quality standard.

You are a transactional lawyer. Draft a mutual NDA from the context below. The agreement should match the standard of a commercially negotiated NDA filed with the SEC in connection with a strategic transaction.

>

>PASTE BELOW INTO MODEL

You are a transactional lawyer. Draft a mutual NDA from the context below. The agreement should match the standard of a commercially negotiated NDA prepared in connection with a strategic transaction.

Business context:
A cloud infrastructure company and an enterprise AI company are exploring a potential
joint venture in which the cloud company's GPU cluster would host the AI company's
training workloads under a revenue-sharing arrangement. Both parties will exchange
pricing models, customer lists, technical architecture details, and roadmap documents.

Required provisions:
1. Mutual — both parties are Disclosing Party and Receiving Party
2. Definition of Confidential Information — includes oral disclosures; covers
   information disclosed 'in connection with evaluating the Proposed Transaction'
3. Standard exclusions (4): publicly known, previously known, independently developed,
   received from permitted third party
4. Compelled disclosure carve-out with prompt-notice obligation to Disclosing Party
5. Return/destruction of materials upon request or termination
6. Term: 2 years from Effective Date
7. Survival: confidentiality obligations survive termination for 3 years
8. Injunctive relief clause — without requirement of bond or surety
9. No residuals: neither party may use 'residual knowledge' retained in unaided memory
10. Governing law: New York
11. No solicitation of employees for 1 year from Effective Date

Draft the complete NDA.
	||CELL||
>

Scoring Rubric  ·  Max: /12  ·  Dimensions: Faithfulness /3 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||No scope creep — no IP ownership, indemnification, or arbitration if not requested. All durations and governing law match the brief exactly.
	||CELL||Adding unrequested provisions; wrong governing law; wrong durations (scope creep is the Faithfulness-to-instructions failure)
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All 11 required provisions present. Critical: all 4 standard exclusions; injunctive relief without bond or surety (frequently dropped); no-residuals clause (rarely in default templates); 3-year survival duration stated.
	||CELL||Missing a standard exclusion; dropping 'without requirement of bond or surety'; omitting no-residuals; survival duration unstated
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Mutual structure: obligations run both directions symmetrically. Defined terms used consistently. The draft is legally coherent and enforceable.
	||CELL||One-sided structure (only one party as Disclosing Party); inconsistent defined-term use; unenforceable drafting
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Complete agreement with signature blocks, effective date, and recitals. Redline-ready against a counterparty.
	||CELL||Missing signature block or recitals; requires substantial revision before use
	||CELL||
>

>

>GATE
No Directionality — drafting a mutual NDA to spec, no named client to favor. Faithfulness gate only.
Faithfulness gate trips on scope creep (adding unrequested provisions) — for drafting, fidelity to the instructions is the no-fabrication analogue.
	||CELL||
>

GRADER INSTRUCTIONS — D1 (Draft NDA from Business Description) · Max /12 · Gates: Faithfulness only
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: SYNTHETIC -- drafted from the brief; the 11 required provisions in the prompt are the gold. Faithfulness here means fidelity to the instructions.
FAITHFULNESS /3 (GATE): No scope creep. TRIPS on adding unrequested provisions (IP ownership, indemnification, arbitration), wrong governing law (must be New York), or wrong durations (2-year term; 3-year survival; 1-year non-solicit).
COVERAGE /4: All 11 required provisions present. Critical checks: all FOUR standard exclusions; injunctive relief WITHOUT requirement of bond or surety (frequently dropped); the no-residuals clause (rarely in default templates); survival duration explicitly stated as 3 years.
UNIT IDs (v7): D1.provision.mutual; D1.provision.ci_definition; D1.provision.exclusions_x4; D1.provision.compelled_disclosure; D1.provision.return_destruction; D1.provision.term_2y; D1.provision.survival_3y; D1.provision.injunctive_no_bond; D1.provision.no_residuals; D1.provision.gov_law_ny; D1.provision.nonsolicit_1y. Gate unit: D1.gate.scope_creep.
SOUNDNESS /3: Mutual structure -- obligations run both directions symmetrically (one-sided structure = dock); defined terms used consistently; draft is legally coherent and enforceable.
ACTIONABILITY /2: Complete agreement -- recitals, effective date, signature blocks; redline-ready without substantial revision.
PROCEDURE: Score every dimension -> raw total -> normalize to /12 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Prompt D2 — Notice of Breach Letter

>

>Task D2 · Breach Letter · Max /12 · gate: Faithfulness · gold: arithmetic-verifiable + judgment · PROVENANCE: SYNTHETIC/CONSTRUCTED — invented facts; arithmetic self-verifiable
	||CELL||
>

■ Source: Facts based on real SLA enforcement patterns observed in CUAD MSA corpus (SEC EDGAR). Uptime SLA (99.5%), cure period structure (30 days), and non-curable breach provision for repeated failures are standard clause patterns in CUAD's 'Termination for Cause' and 'SLA' label categories.

Draft a formal notice of breach letter on behalf of CloudBase Inc. ('Client') to send to TechServe LLC ('Vendor'). Use the facts and contract provisions below exactly. Do not invent facts. Do the math yourself.

>

>PASTE BELOW INTO MODEL

Draft a formal notice of breach letter on behalf of CloudBase Inc. ('Client') to send to TechServe LLC ('Vendor'). Use the facts and contract provisions below exactly. Do not invent facts. Do the math yourself.

FACTS AND CONTRACT PROVISIONS:
Agreement: Managed Services Agreement dated March 1, 2025.

Contract provision §5.2: Vendor shall maintain 99.5% monthly uptime for the production
  environment, measured as total minutes available divided by total minutes in the month.
Contract provision §9.1: A material breach of this Agreement may be cured within thirty (30)
  days of written notice from the non-breaching party specifying the breach in reasonable detail.
Contract provision §9.2: Repeated SLA failures — defined as failure to meet the uptime
  commitment in two or more consecutive calendar months — shall constitute a non-curable
  material breach, entitling the non-breaching party to terminate immediately upon written notice.

April 2025 uptime data (confirmed by Vendor's own status page):
  April 8:  6 hours 14 minutes of unplanned downtime
  April 17: 8 hours 52 minutes of unplanned downtime
  April 23: 3 hours 0 minutes of downtime (Vendor attributes to 'third-party DNS provider')
  Total downtime: 18 hours 6 minutes
  April total minutes: 720 hours = 43,200 minutes

Prior notices: No breach notice has previously been sent by Client.

Draft the formal breach notice letter. Include: the specific breach with the uptime calculation,
citations to §5.2 and §9.1, demand for cure, preservation of §9.2 rights, and a reservation
of all rights. Tone: firm but professional.
	||CELL||
>

>

>NOTE
Uptime math: 18h 6m = 1,086 min downtime; 43,200 - 1,086 = 42,114 min available; 42,114 / 43,200 = 97.5% uptime. Required: 99.5%. Shortfall: 2.0 percentage points.
	||CELL||
>

Scoring Rubric  ·  Max: /12  ·  Dimensions: Faithfulness /3 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||Uptime math correct (97.5%). No invented facts. No fabricated cure deadlines or breach instances.
	||CELL||Wrong uptime percentage; inventing additional breach instances; fabricating a cure deadline
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All 6 elements: (1) uptime calc (2) §5.2 cited (3) §9.1 cited with 30-day cure (4) demand for cure (5) §9.2 rights preserved without triggering them (6) reservation of all rights.
	||CELL||Missing the calculation, a citation, or the rights-reservation
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Correctly demands cure, not immediate termination (only one month has failed — §9.2 not yet triggered). Correctly treats third-party DNS attribution as not a valid excuse.
	||CELL||Asserting immediate termination prematurely; accepting the DNS attribution as a defense
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Letter format: salutation, date line, subject line, signature block. Firm but professional tone.
	||CELL||Memo format instead of letter; missing signature block
	||CELL||
>

>

>GATE
No Directionality gate — drafting on behalf of Client is execution, not strategic advocacy; the 'don't overreach to termination' judgment sits under Soundness. Faithfulness gate active.
Faithfulness gate trips on wrong arithmetic presented as fact or invented breach instances — this prompt is the math/fact-fidelity test.
	||CELL||
>

GRADER INSTRUCTIONS — D2 (Notice of Breach Letter) · Max /12 · Gates: Faithfulness only
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: SYNTHETIC facts; the arithmetic is self-verifying. Gold math: 18h 6m = 1,086 minutes downtime; 43,200 - 1,086 = 42,114 available; 42,114 / 43,200 = 97.5% uptime vs 99.5% required; shortfall 2.0 percentage points.
FAITHFULNESS /3 (GATE): The math/fact-fidelity test. TRIPS on wrong arithmetic presented as fact, invented breach instances, or a fabricated cure deadline.
COVERAGE /4: Six elements: (1) the uptime calculation shown; (2) Section 5.2 cited; (3) Section 9.1 cited with the 30-day cure; (4) demand for cure; (5) Section 9.2 rights PRESERVED without being triggered; (6) reservation of all rights.
UNIT IDs (v7): D2.element.uptime_calc; D2.element.cite_5_2; D2.element.cite_9_1_cure; D2.element.cure_demand; D2.element.preserve_9_2; D2.element.reserve_rights. Gold arithmetic unit: D2.math.uptime_97_5.
SOUNDNESS /3: Demands cure, NOT immediate termination -- only one month has failed, Section 9.2 (two consecutive months) is not yet triggered; premature termination assertion = dock. Treats the third-party DNS attribution as NOT a valid excuse; accepting it as a defense = dock.
ACTIONABILITY /2: Letter format -- salutation, date, subject line, signature block; firm but professional tone.
PROCEDURE: Score every dimension -> raw total -> normalize to /12 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Prompt D3 — Scoped Amendment (No Scope Creep)

>

>Task D3 · Scoped Amendment · Max /12 · gate: Faithfulness · gold: constructed from brief (verifiable) · PROVENANCE: SYNTHETIC/CONSTRUCTED — drafted from brief
	||CELL||
>

■ Source: Instruction-based drafting. Payment term patterns (Net 30, late interest rates, suspension rights) drawn from real CUAD MSA corpus clause structures. Amendment format follows SEC EDGAR exhibit conventions for EX-10 filings.

The parties have agreed to change only the payment terms in their existing MSA. Draft Amendment No. 1 reflecting only the agreed changes. Modify nothing else.

>

>PASTE BELOW INTO MODEL

The parties have agreed to change only the payment terms in their existing MSA. Draft Amendment No. 1 reflecting only the agreed changes. Modify nothing else.

Original Agreement: Master Services Agreement dated June 1, 2018
Parties: Kelmont, Inc. ('Service Provider') and Spireline Digital ('Customer')
This document: Amendment No. 1

Agreed changes (payment terms only):
1. Section 7.05 currently reads: 'Service Provider reserves the right to suspend all
   Services in the event that Customer fails to pay each invoice within 15 days of receipt.'
   Amend to: payment due within 30 days of invoice date (not receipt); suspension right
   available only after an additional 10-day cure notice, not immediately.
2. Add a new provision: Late payments accrue interest at 1.0% per month on the outstanding
   balance from the date due until paid.
3. Add a new provision: Disputed invoices must be raised in writing within 20 days of
   invoice date with a description of the specific basis for dispute.

Draft the complete amendment. Do not introduce any provisions beyond what is listed above.
	||CELL||
>

Scoring Rubric  ·  Max: /12  ·  Dimensions: Faithfulness /3 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||No scope creep — no changes to term, IP, indemnification, governing law, or any other provision. Continuity clause present: 'All other terms remain in full force and effect.'
	||CELL||Adding unrequested provisions; modifying sections beyond payment terms; omitting the continuity clause
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All 6 elements: (1) original MSA by full name + June 1, 2018 date (2) labeled 'Amendment No. 1' (3) §7.05: 30 days from invoice DATE not receipt (4) 10-day cure notice before suspension (5) 1.0%/month late interest (6) 20-day dispute window with 'description of specific basis'.
	||CELL||Missing any of the six required changes
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Payment trigger correctly changed to 'invoice date' (not 'receipt' — the distinction matters legally); interest stated per month not per year; amendment mechanics are correct.
	||CELL||Using 'receipt' instead of 'invoice date'; stating interest per year; broken amendment structure
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Complete amendment: title, recitals identifying the original agreement, numbered changes, continuity clause, signature blocks.
	||CELL||Missing signature blocks or the continuity clause; informal format
	||CELL||
>

>

>GATE
No Directionality — scoped drafting to spec. Faithfulness gate is the central test.
Faithfulness gate trips on scope creep — any modification beyond the three listed payment changes.
	||CELL||
>

GRADER INSTRUCTIONS — D3 (Scoped Amendment) · Max /12 · Gates: Faithfulness only
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: SYNTHETIC -- drafted from the brief; party names fictionalized (Kelmont, Inc. / Spireline Digital) to match the perturbed MSA universe. The three listed payment changes are the gold. Faithfulness = scope discipline.
FAITHFULNESS /3 (GATE): TRIPS on scope creep -- ANY modification beyond the three listed payment changes (term, IP, indemnification, governing law, anything else), or omission of the continuity clause ('All other terms remain in full force and effect').
COVERAGE /4: Six elements: (1) original MSA identified by full name + June 1, 2018 date; (2) labeled 'Amendment No. 1'; (3) Section 7.05 amended to 30 days from invoice DATE (not receipt); (4) 10-day cure notice before suspension; (5) 1.0% per month late interest; (6) 20-day dispute window requiring a description of the specific basis.
UNIT IDs (v7): D3.element.original_msa_named; D3.element.amendment_no_1; D3.element.net30_invoice_date; D3.element.cure_10d; D3.element.interest_1pct_month; D3.element.dispute_20d. Gate unit: D3.gate.scope_creep.
SOUNDNESS /3: Payment trigger correctly moved to 'invoice date' (the date/receipt distinction matters legally; 'receipt' = dock); interest per MONTH not per year; amendment mechanics correct.
ACTIONABILITY /2: Complete amendment -- title, recitals identifying the original agreement, numbered changes, continuity clause, signature blocks.
PROCEDURE: Score every dimension -> raw total -> normalize to /12 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Stage E — Negotiation Simulation
"They sent this back — now what?"

Applicable dimensions: Faithfulness /3 (gate) · Directionality /4 (gate) · Coverage /4 · Soundness /3 · Actionability /2

Prompt E1 — Triage 8 Opposing Counsel Redlines

>

>Task E1 · Triage · Max /16 · gates: Faithfulness, Directionality · gold: constructed key + judgment (needs review) · perturbed (v6) · PROVENANCE: CONSTRUCTED SCENARIO on real MSA — positions invented; Change 4 gov-law premise should reflect real NY §16.12
	||CELL||
>

■ Source: Changes derived from real CUAD corpus redline patterns. Governing-law disputes, SLA credit structures, audit-right mechanics, and FM expansions are among the most frequently annotated clause categories in CUAD's 41-label taxonomy. Triage scenarios reflect negotiation patterns observed in MAUD merger agreement dataset.

You represent the Customer (Spireline Digital) negotiating the Kelmont MSA (perturbed universe, v6). Vendor's counsel has returned 8 changes to your redlined agreement. For each, classify as ACCEPT, REJECT, or COUNTER. Brief rationale required.

>

>PASTE BELOW INTO MODEL

You represent the Customer (Spireline Digital) negotiating the Kelmont MSA. Vendor's counsel has returned 8 changes to your redlined agreement. For each change, classify it as ACCEPT, REJECT, or COUNTER, with a brief rationale.

YOUR POSITION (Customer's redline) vs. VENDOR'S COUNTER-REDLINE

Change 1 — Termination Notice Period
Your position: Either party may terminate without cause on 30 days written notice.
Vendor counter: Either party may terminate without cause on 2 days written notice
  (email acceptable) — restore original contract language.

Change 2 — Payment Terms
Your position: Invoices due within 30 days of invoice date; suspension right available
  only after additional 10-day cure notice.
Vendor counter: Invoices due within 15 days of invoice date; suspension available
  immediately upon non-payment.

Change 3 — IP Ownership Carve-Out Definition
Your position: Add definition: 'Service Provider Ad Engine' means the core programmatic
  advertising engine as of the Effective Date, excluding any modifications made
  specifically for Customer.
Vendor counter: Remove the proposed definition; leave Ad Engine undefined.

Change 4 — Governing Law
Your position: Governing law — State of New York.
Vendor counter: Governing law — State of Delaware.

Change 5 — Background Checks
Your position: Background checks must include criminal record, credit history, reference
  checks, and sex offender registry check for any Personnel accessing Customer's systems.
Vendor counter: Background checks as required by applicable state law only; sex offender
  registry check deleted.

Change 6 — Indemnification Cap
Your position: Add: Vendor's aggregate indemnification obligation under §11.01 shall not
  exceed two times (2x) fees paid by Customer in the prior 12 months.
Vendor counter: Add: Vendor's aggregate indemnification obligation shall not exceed fees
  paid by Customer in the prior 3 months.

Change 7 — Force Majeure
Your position: No change to FM clause.
Vendor added: 'For avoidance of doubt, Force Majeure events include cyberattacks,
  ransomware attacks, and third-party infrastructure failures.'

Change 8 — Records Inspection
Your position: Customer may inspect Service Provider records once per year on 10 business
  days' notice.
Vendor counter: Customer may inspect records once every 2 years on 30 business days'
  notice; Customer must use an independent auditor.
	||CELL||
>

Scoring Rubric  ·  Max: /16  ·  Dimensions: Faithfulness /3 (gate) · Directionality /4 (gate) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||Rationales reference the actual changes; no invented contract terms or misquoted positions.
	||CELL||Misrepresenting what a change says; inventing terms not in the redline
	||CELL||
>Directionality
	||CELL||/4
	||CELL||All calls from Customer's seat. ACCEPT on Changes 1, 3, or 7 are Directionality failures (they favor Vendor against Customer). Change 4 (Delaware) is acceptable for Customer — accepting it is not a failure.
	||CELL||ACCEPT on Change 1 (2-day termination), Change 3 (undefined IP carve-out), or Change 7 (FM for cyberattacks)
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All 8 changes classified with rationale. Partial credit: 7/8 = /3, 6/8 = /2.
	||CELL||Missing a classification; rationale without a clear ACCEPT/REJECT/COUNTER call
	||CELL||
>Soundness
	||CELL||/3
	||CELL||Each call is legally defensible. Change 7 (FM for cyberattacks) correctly rejected — Vendor cannot use FM to escape its own security failures. Change 4 (Delaware) recognized as commercially neutral.
	||CELL||Rejecting Change 4 without basis; legally incoherent rationale on any change
	||CELL||
>Actionability
	||CELL||/2
	||CELL||COUNTER calls state a specific counter-position; REJECT calls give a rationale the other side can respond to.
	||CELL||'Counter' without a position; 'Reject' without rationale
	||CELL||
>

>

>GATE
Directionality gate trips on ACCEPT for Changes 1, 3, or 7 — accepting any of these is advocating against the Customer.
For the LLM grader, this decomposes cleanly: classify each of the 8 calls against the gold ACCEPT/REJECT/COUNTER set, then check the three gate-changes specifically.
	||CELL||
>

>

>FAILURE MODES
Hard failure modes: ACCEPT on Change 1 (2-day termination), Change 3 (undefined IP carve-out), or Change 7 (FM for cyberattacks) — all indicate poor triage judgment.
	||CELL||
>

Scoring Reference by Change

>

>Change
	||CELL||Best Call
	||CELL||Key Reasoning
	||CELL||
>1 — Termination (2 days) [ID: E1.call.change1_termination]
	||CELL||REJECT
	||CELL||2-day notice provides no business continuity; market standard is 30-90 days
	||CELL||
>2 — Payment (15 days + immediate suspension) [ID: E1.call.change2_payment]
	||CELL||REJECT or COUNTER
	||CELL||15 days is below market; immediate suspension without cure is draconian; counter at 30 days + cure
	||CELL||
>3 — Ad Engine definition removed [ID: E1.call.change3_ad_engine]
	||CELL||REJECT
	||CELL||Undefined carve-out is the core IP ambiguity — Customer needs a bounded definition
	||CELL||
>4 — Delaware governing law [ID: E1.call.change4_gov_law]
	||CELL||ACCEPT or COUNTER
	||CELL||Delaware is commercially neutral; acceptable unless Customer is NY-HQ'd
	||CELL||
>5 — Sex offender registry deleted [ID: E1.call.change5_background]
	||CELL||COUNTER
	||CELL||Reasonable for Personnel with system access; state-law minimum is insufficient
	||CELL||
>6 — Indemnity cap (3 months) [ID: E1.call.change6_indemnity_cap]
	||CELL||COUNTER
	||CELL||3 months is too low; counter at 12 months matching the aggregate liability cap
	||CELL||
>7 — FM includes cyberattacks [ID: E1.call.change7_force_majeure]
	||CELL||REJECT
	||CELL||Vendor escaping liability for its own security failures via FM is unreasonable
	||CELL||
>8 — 2-year inspection + auditor [ID: E1.call.change8_inspection]
	||CELL||COUNTER
	||CELL||Annual inspection is market standard; auditor requirement adds cost but may be acceptable
	||CELL||
>

GRADER INSTRUCTIONS — E1 (Triage 8 Opposing-Counsel Redlines) · Max /16 · Gates: Faithfulness + Directionality
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: CONSTRUCTED scenario in the perturbed MSA universe (Kelmont / Spireline); positions invented; the accept/reject/counter key is authored legal judgment. Grade calls against the gold key below. Decomposes cleanly: classify each of the 8 calls against gold, then check the three gate-changes specifically.
GOLD KEY: Change 1 (2-day termination) = REJECT [gate]. Change 2 (15 days + immediate suspension) = REJECT or COUNTER (30 days + cure). Change 3 (Ad Engine definition removed) = REJECT [gate] -- the undefined carve-out is the core IP ambiguity. Change 4 (Delaware governing law) = ACCEPT or COUNTER -- commercially neutral; either is correct. Change 5 (sex-offender registry deleted) = COUNTER -- reasonable for system-access Personnel; state-law minimum insufficient. Change 6 (3-month indemnity cap) = COUNTER at 12 months matching the aggregate cap. Change 7 (FM includes cyberattacks) = REJECT [gate] -- Vendor cannot use FM to escape its own security failures. Change 8 (2-year inspection + auditor) = COUNTER -- annual is market; auditor may be acceptable.
UNIT IDs (v7): E1.call.change1_termination; E1.call.change2_payment; E1.call.change3_ad_engine; E1.call.change4_gov_law; E1.call.change5_background; E1.call.change6_indemnity_cap; E1.call.change7_force_majeure; E1.call.change8_inspection. Gate units: change1, change3, change7.
FAITHFULNESS /3 (GATE): Rationales reference the actual changes; TRIPS on misrepresenting what a change says or inventing terms not in the redline.
DIRECTIONALITY /4 (GATE): All calls from Customer's (Spireline Digital's) seat. TRIPS on ACCEPT for Change 1, Change 3, or Change 7 -- each is advocating against the Customer. Accepting Change 4 (Delaware) is NOT a failure.
COVERAGE /4: All 8 changes classified with a clear call + rationale. Banding: 8 = 4; 7 = 3; 6 = 2. A rationale with no clear ACCEPT/REJECT/COUNTER call does not count.
SOUNDNESS /3: Each call legally defensible; Change 7 correctly rejected on the own-security-failures ground; Change 4 recognized as commercially neutral (rejecting it WITH a stated basis is fine; rejecting it with no basis = dock).
ACTIONABILITY /2: Every COUNTER states a specific counter-position; every REJECT gives a rationale the other side can respond to.
PROCEDURE: Score every dimension -> raw total -> normalize to /16 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Prompt E2 — Deal Viability Analysis

>

>Task E2 · Deal Viability · Max /16 · gates: Faithfulness, Directionality(=neutrality) · gold: legal judgment (needs review, high priority) · PROVENANCE: CONSTRUCTED SCENARIO on real MSA — party must-haves invented
	||CELL||
>

■ Source: Must-have positions modeled on real MAUD deal point disputes (MAUD dataset, Atticus Project, EMNLP 2023). IP ownership in custom development, governing law disputes, and SLA vs. best-efforts uptime are among the most contested issues in MAUD's 92 deal-point reading comprehension questions.

You are neutral deal counsel mediating the Kelmont / Spireline Digital MSA negotiation (perturbed universe, v6). Both parties have stated their absolute non-negotiables. Assess each conflict, determine whether it is bridgeable, and give an overall verdict on deal viability.

>

>PASTE BELOW INTO MODEL

You are neutral deal counsel mediating the Kelmont / Spireline Digital MSA negotiation. Both parties have stated their absolute non-negotiables below. Assess each conflict, determine whether it is bridgeable, and give an overall verdict on deal viability.

PARTY POSITIONS — ABSOLUTE NON-NEGOTIABLES

SERVICE PROVIDER (Kelmont) MUST-HAVES:
1. Termination-for-convenience on 2 days notice — Service Provider business model
   requires ability to exit any client relationship quickly
2. Service Provider Ad Engine IP stays entirely with Service Provider — no definition,
   no limitations, no carve-outs
3. Payment within 15 days; immediate suspension right for non-payment
4. No minimum SLA — 'commercially reasonable efforts' uptime only; no service credits
5. Governing law: Delaware only
6. Aggregate liability cap: 3 months of fees paid

CUSTOMER (Spireline Digital) MUST-HAVES:
1. Minimum 30-day termination notice for convenience (operational continuity)
2. Clear, bounded definition of what the 'Service Provider Ad Engine' includes,
   so Customer knows what Deliverables it actually owns
3. Payment within 30 days; 10-day cure notice before any suspension
4. Minimum 99.5% monthly uptime SLA with service credits for failure
5. Governing law: New York (Customer's preferred forum, matching the existing contract)
6. Aggregate liability cap: 12 months of fees paid

Assess each conflict and give your overall deal viability verdict.
	||CELL||
>

Ground-Truth Conflict Analysis

>

>Conflict
	||CELL||Bridgeable?
	||CELL||Path to Bridge
	||CELL||
>1. Termination notice (2 vs 30 days) [ID: E2.conflict.termination]
	||CELL||Bridgeable
	||CELL||15 or 20 days is a commercial compromise; Vendor's '2-day business model' claim likely a bargaining position, not a true operational constraint
	||CELL||
>2. Ad Engine definition [ID: E2.conflict.ad_engine]
	||CELL||Bridgeable with drafting creativity
	||CELL||Vendor retains underlying engine; Customer owns custom work on top — documented perimeter satisfies both if boundary is clearly drafted
	||CELL||
>3. Payment (15 vs 30 days + cure period) [ID: E2.conflict.payment]
	||CELL||Bridgeable
	||CELL||Net 30 is market standard; suspension after cure notice is reasonable for both; this is a negotiating position, not a dealbreaker
	||CELL||
>4. SLA vs best-efforts [ID: E2.conflict.sla]
	||CELL||Difficult but bridgeable
	||CELL||Narrow SLA with low credit cap (e.g., 10% of monthly fees) may satisfy both; pure 'best efforts' is increasingly uncommon in tech contracts
	||CELL||
>5. Governing law (Delaware vs NY) [ID: E2.conflict.gov_law]
	||CELL||Bridgeable
	||CELL||Both are commercial law states with established case law; neither has a materially stronger position
	||CELL||
>6. Liability cap (3 vs 12 months) [ID: E2.conflict.liability_cap]
	||CELL||Bridgeable
	||CELL||6-month compromise is market standard for short-term tech contracts; both can move
	||CELL||
>

Scoring Rubric  ·  Max: /16  ·  Dimensions: Faithfulness /3 (gate) · Directionality /4 (gate, = neutrality) · Coverage /4 · Soundness /3 · Actionability /2

>

>Dimension
	||CELL||Weight
	||CELL||What to Score
	||CELL||Failure Mode
	||CELL||
>Faithfulness
	||CELL||/3
	||CELL||Represents each party's stated must-haves accurately; no invented positions.
	||CELL||Misstating a party's non-negotiable; inventing a constraint not listed
	||CELL||
>Directionality
	||CELL||/4
	||CELL||As neutral mediator, the correct direction is balanced neutrality. Both parties' reasonable interests acknowledged; analysis not tilted toward either side.
	||CELL||Analysis that systematically favors one party; failing to acknowledge a party's legitimate basis
	||CELL||
>Coverage
	||CELL||/4
	||CELL||All 6 conflicts assessed with a bridgeability verdict; an overall deal-viability verdict appears.
	||CELL||Missing a conflict assessment; no overall verdict
	||CELL||
>Soundness
	||CELL||/3
	||CELL||The key move: distinguish genuine business-model constraints from negotiating positions. The 2-day termination 'business model' claim is a position, not a true constraint. All 6 conflicts are in fact bridgeable; calling any a true dealbreaker is a merits error.
	||CELL||Accepting the 2-day termination claim uncritically; declaring any of the 6 conflicts non-bridgeable
	||CELL||
>Actionability
	||CELL||/2
	||CELL||Concrete path-to-bridge for each conflict; overall verdict with a clear deal recommendation.
	||CELL||Overall verdict without bridge paths; vague 'could be negotiated'
	||CELL||
>

>

>GATE
Directionality here means NEUTRALITY — the gate trips if the model systematically takes one party's side rather than mediating.
Soundness is the hardest dimension to auto-grade on this prompt (it rests on a contestable commercial-negotiation judgment). Validate the grader's kappa here before trusting it; route low-confidence items to human audit.
	||CELL||
>

GRADER INSTRUCTIONS — E2 (Deal Viability Analysis) · Max /16 · Gates: Faithfulness + Directionality (= neutrality)
ROLE: Grade the model's response against this gold rubric. Do NOT solve the task yourself. For every sub-judgment, quote the exact span of the response you relied on; a judgment with no quotable evidence scores 0. Return structured JSON per the Tier 1 template (Section 6.5). Composition: this block = GOLD_RUBRIC; the prompt's PASTE BELOW INTO MODEL block = SOURCE_CONTRACT + PROMPT_GIVEN_TO_MODEL; the model's answer = RESPONSE_UNDER_TEST. Never show this block to the model under test.
SOURCE OF TRUTH: CONSTRUCTED scenario in the perturbed MSA universe (Kelmont / Spireline); party must-haves are invented; the bridgeability key is authored commercial judgment flagged as the suite's highest-priority item for attorney review. Validate grader kappa here before trusting it; route low-confidence items to human audit.
GOLD KEY: ALL SIX conflicts are bridgeable. (1) Termination 2 vs 30 days -- bridgeable at 15-20 days; the '2-day business model' claim is a bargaining position, not a true constraint [the key Soundness move]. (2) Ad Engine definition -- bridgeable with drafting: Vendor keeps the underlying engine, Customer owns custom work on top, perimeter documented. (3) Payment 15 vs 30 + cure -- bridgeable; Net 30 is market. (4) SLA vs best-efforts -- difficult but bridgeable; narrow SLA with low credit cap (~10% of monthly fees). (5) Delaware vs New York -- bridgeable; both commercial-law states, neither materially stronger. (6) Cap 3 vs 12 months -- bridgeable at 6 months.
UNIT IDs (v7): E2.conflict.termination; E2.conflict.ad_engine; E2.conflict.payment; E2.conflict.sla; E2.conflict.gov_law; E2.conflict.liability_cap; plus E2.verdict.overall.
FAITHFULNESS /3 (GATE): Each party's stated must-haves represented accurately. TRIPS on misstating a non-negotiable or inventing a constraint not listed.
DIRECTIONALITY /4 (GATE, = NEUTRALITY): The correct direction is balanced neutrality -- both parties' reasonable interests acknowledged. TRIPS if the analysis systematically favors one party.
COVERAGE /4: All six conflicts assessed with an explicit bridgeable / not-bridgeable verdict, plus an overall deal-viability verdict.
SOUNDNESS /3: Distinguishes genuine business-model constraints from negotiating positions -- accepting the 2-day termination claim uncritically = dock; declaring ANY of the six conflicts a true dealbreaker = merits error, dock.
ACTIONABILITY /2: Concrete path-to-bridge for each conflict; overall verdict with a clear recommendation (not 'could be negotiated').
PROCEDURE: Score every dimension -> raw total -> normalize to /16 -> if ANY gate tripped, cap the normalized score at 0.40 and flag which gate tripped and on what evidence.

Appendix — Quick Reference Scorecard
Score each prompt against its applicable dimensions, normalize to its stated max, then apply gate caps before averaging. 'n/a' = dimension not scored for that prompt. F = Faithfulness, D = Directionality.

>

>Prompt
	||CELL||Max
	||CELL||Faith /3
	||CELL||Dir /4
	||CELL||Cov /4
	||CELL||Snd /3
	||CELL||Act /2
	||CELL||Raw
	||CELL||Gate?
	||CELL||Norm.
	||CELL||
>A1
	||CELL||16
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>A2
	||CELL||16
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>A3
	||CELL||12
	||CELL||
	||CELL||n/a
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>B1
	||CELL||9
	||CELL||
	||CELL||n/a
	||CELL||
	||CELL||n/a
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>B2
	||CELL||12
	||CELL||
	||CELL||n/a
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>B3
	||CELL||12
	||CELL||
	||CELL||n/a
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>C1
	||CELL||16
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>C2
	||CELL||16
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>C3
	||CELL||12
	||CELL||
	||CELL||n/a
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>D1
	||CELL||12
	||CELL||
	||CELL||n/a
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>D2
	||CELL||12
	||CELL||
	||CELL||n/a
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>D3
	||CELL||12
	||CELL||
	||CELL||n/a
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>E1
	||CELL||16
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>E2
	||CELL||16
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>
Gate column: mark 'F' if the Faithfulness gate tripped, 'D' if the Directionality gate tripped. If either is marked, cap the normalized score at 0.40. (v7) Score A1, A2, and C2 once per instruction variant (A1-O / A1-D, etc.) and B3 once per A/B condition. Stage scores use the OPEN (and B3-instructed) scores; report directed/uninstructed scores and the deltas alongside as the prompted-vs-spontaneous diagnostic.

Stage scores (mean of gate-adjusted normalized prompt scores in that stage):

>

>Stage
	||CELL||Prompts
	||CELL||Stage Score
	||CELL||Weight
	||CELL||Weighted
	||CELL||Gate Trips
	||CELL||
>A
	||CELL||A1, A2, A3
	||CELL||
	||CELL||× 0.20
	||CELL||
	||CELL||
	||CELL||
>B
	||CELL||B1, B2, B3
	||CELL||
	||CELL||× 0.20
	||CELL||
	||CELL||
	||CELL||
>C
	||CELL||C1, C2, C3
	||CELL||
	||CELL||× 0.25
	||CELL||
	||CELL||
	||CELL||
>D
	||CELL||D1, D2, D3
	||CELL||
	||CELL||× 0.20
	||CELL||
	||CELL||
	||CELL||
>E
	||CELL||E1, E2
	||CELL||
	||CELL||× 0.15
	||CELL||
	||CELL||
	||CELL||
>OVERALL
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
	||CELL||
>
Always report the OVERALL score next to the total gate-trip count. A 0.78 with zero trips and a 0.78 with six trips are different models.

Dimension Summary (v7 — dimension set unchanged from v6)

>

>Dimension
	||CELL||Max
	||CELL||Role
	||CELL||Rationale
	||CELL||
>Faithfulness
	||CELL||0–3
	||CELL||GATE
	||CELL||Fabrication is the most catastrophic failure in legal AI — an invented clause or cap can cause real harm. Caps the score, not just deducts.
	||CELL||
>Directionality
	||CELL||0–4
	||CELL||GATE
	||CELL||Advocating for the wrong party is worse than no analysis — it actively misleads. Caps the score.
	||CELL||
>Coverage
	||CELL||0–4
	||CELL||Graded
	||CELL||Missing a material issue is serious but recoverable in review — harm by omission, not commission.
	||CELL||
>Soundness
	||CELL||0–3
	||CELL||Graded
	||CELL||NEW: is the law actually right? Catches the failure where everything else passes but the fix does not work.
	||CELL||
>Actionability
	||CELL||0–2
	||CELL||Graded
	||CELL||Usability matters, but a perfectly formatted wrong answer is worse than a rough correct one.
	||CELL||
>

>

>SCORING PHILOSOPHY
Two changes from the earlier rubric drive the ranking: (1) Consistency dissolved into Faithfulness (accurate quotation) and Soundness (correct defined-term use); Soundness was added to score legal correctness directly.
(2) Faithfulness and Directionality are gates, not just heavy weights — a comprehensive, polished answer that fabricates a clause or argues for the wrong party is capped at 0.40 and cannot climb back via volume.
Net effect: a model that is correct and faithful but misses some coverage outranks a model that is comprehensive but hallucinates or mis-advocates. That is the correct ordering for legal work product, where confident-wrong is a liability and incomplete-but-right is a starting point.
	||CELL||
>

Grading Pipeline at a Glance

>

>Step
	||CELL||Action
	||CELL||Owner
	||CELL||
>1
	||CELL||Deterministic checks (recall vs. gold set, math, format, required strings)
	||CELL||Tier 0 — code
	||CELL||
>2
	||CELL||LLM grader: decomposed, reference-anchored, evidence-quoting, structured JSON
	||CELL||Tier 1 — cross-family LLM
	||CELL||
>3
	||CELL||Apply gate logic; compute normalized + gate-adjusted scores
	||CELL||Code
	||CELL||
>4
	||CELL||Escalate low-confidence / split-ensemble items
	||CELL||Tier 2 — human queue (~10–15%)
	||CELL||
>5
	||CELL||Validate grader vs. human on calibration set (kappa ≥ 0.80 to trust a dimension)
	||CELL||Humans, before trusting the grader
	||CELL||
>

LegalEval Complete Framework & Prompt Suite (v7) · Contract text from SEC EDGAR public filings, CUAD (Atticus Project), ContractNLI (Stanford NLP), and ACORD (ACL 2025) · 2026
