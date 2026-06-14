# summary  

**Design Details & Grading:** [LegalEval\_v6](https://drive.google.com/drive/folders/14ixUKBPOV-zZfhcmD1OBJBjdUGsIKeJ_?usp=sharing)

  

**Note:** Eval created w/ help of Claude Opus 4.8 and Fable 5; this model will also act as the grader / give the standard. Not sure if this is cause for concern on updates of 

  

**Current Models** 

1.  Claude Sonnet 4.6 
2.  Gemini 3.1 Flash 
3.  GPT 5.5 
4.  Muse Spark 
5.  Qwen 3.7 Plus

Here's the full prompt suite — 14 prompts across 5 stages

**Stage A — Document Ingestion & Issue Spotting** ("read this, tell me what's wrong")

  - **A1 · Missing-Clause Detection** — /16 — gates: Faithfulness + Directionality — *modified-from-real* (3M/Cogent NDA)
  - **A2 · Problematic-Clause ID** — /16 — gates: Faithfulness + Directionality — *modified-from-real* (Kubient MSA)
  - **A3 · Version Diff** — /12 — gate: Faithfulness — *modified-from-real* (Kubient + adapted Version B)

**Stage B — Summarization & Extraction**

  - **B1 · Defined-Terms Glossary** — /9 — gate: Faithfulness — *verbatim-real* (Kubient Art. I)
  - **B2 · Obligations Table** — /12 — gate: Faithfulness — *verbatim-real* (Kubient Art. III–IV)
  - **B3 · Executive Summary** — /12 — gate: Faithfulness — *modified-from-real, re-founded in v5* (Kubient/3M)

**Stage C — Redlining & Suggested Edits**

  - **C1 · Directional Redline** — /16 — gates: Faithfulness + Directionality — *real-quoted clause + constructed key* (ACORD)
  - **C2 · Issue-to-Fix** — /16 — gates: Faithfulness + Directionality — *real-quoted clause + constructed key* (ACORD)
  - **C3 · Consistency Check** — /12 — gate: Faithfulness — *modified-from-real* (planted inconsistencies)

**Stage D — Drafting from Instructions**

  - **D1 · Draft NDA** — /12 — gate: Faithfulness — *synthetic/constructed*
  - **D2 · Breach Letter** — /12 — gate: Faithfulness — *synthetic* (arithmetic-verifiable)
  - **D3 · Scoped Amendment** — /12 — gate: Faithfulness — *synthetic/constructed*

**Stage E — Negotiation Simulation**

  - **E1 · Triage** — /16 — gates: Faithfulness + Directionality — *constructed scenario on real MSA*
  - **E2 · Deal Viability** — /16 — gates: Faithfulness + Directionality (= neutrality) — *constructed scenario on real MSA*

Totals: 189 points across the suite (A: 44, B: 33, C: 44, D: 36, E: 32). Two underlying source contracts (3M/Cogent NDA, Kubient/Sphere Digital MSA) plus ACORD clauses for C1/C2 and synthetic briefs for D1–D3.  

# A1  

Read the non-disclosure agreement below carefully. Several provisions standard to commercial NDAs are absent. Your task: identify every clause that is missing or materially incomplete. For each, explain the practical risk it creates for the Receiving Party (Calidon).

 

NON-DISCLOSURE AGREEMENT

Calidon Industries, Inc. ('Interested Party' / 'Receiving Party') and Sferex Biometrics, Inc. ('Company' / 'Disclosing Party')

Effective Date: February 12, 2014

 

1\. PROPRIETARY INFORMATION

'Proprietary Information' means any and all information disclosed by Disclosing Party

or its Representatives in connection with the Proposed Transaction, including Derived

Information prepared by Receiving Party that reflects or is based upon the Disclosing

Party's information. Also includes: (x) discussions taking place; (y) proposed terms;

(z) existence of this Agreement.

Exclusions: information (i) generally available to the public other than by Receiving Party's breach;

(ii) known to Receiving Party on a non-confidential basis; (iii) independently developed.

 

2\. NON-DISCLOSURE AND LIMITED USE

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

 

3\. NO SOLICITATION OF EMPLOYEES

Interested Party agrees that for one year from the Effective Date it will not employ or

solicit for employment any key technical or management personnel of the Company who was

introduced to Interested Party in connection with the Proposed Transaction.

 

4\. SECURITIES ISSUES

Each party confirms it is not required to make public disclosure of the Proposed Transaction

or any Proprietary Information as of the date hereof.

 

5\. DEFINITIVE AGREEMENT

Until a definitive agreement is executed, neither party shall have any legal obligation

with respect to the Proposed Transaction except for the matters set forth herein.

 

GOVERNING LAW: \[Not stated in this agreement\]

TERM: \[Not stated in this agreement\]

Signed: Calidon Industries, Inc. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ Sferex Biometrics, Inc. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ 

  

# Claude Sonnet 4.6 

Here is a systematic gap analysis of this NDA, organized by risk severity to Calidon as the Receiving Party.

## **Critical Missing Clauses**

**1. No Governing Law or Jurisdiction** The agreement explicitly flags this as absent. Without it, any dispute triggers threshold litigation just to determine which state's or country's law applies and which court has jurisdiction. This is expensive, time-consuming, and creates uncertainty about what legal standards govern the entire agreement — including what "reasonable care" means and how exclusions are interpreted.

**2. No Defined Term / Confidentiality Duration** Also explicitly flagged as absent. This is a significant exposure for Calidon. Without a stated term, the confidentiality obligation could theoretically be argued to be perpetual, or conversely, it could be argued to expire immediately once the transaction evaluation ends. Perpetual obligations are often unenforceable in certain jurisdictions, leaving Calidon with no protection at all. A standard NDA fixes a clear period (typically 2–5 years).

**3. No Definition of "Proposed Transaction"** The agreement references this term repeatedly but never defines it. If the parties disagree about the scope of what they were evaluating, there is no anchor for what Proprietary Information is even covered. Calidon could find itself bound by confidentiality obligations over information it never understood to be in scope — or find that critical information falls outside the agreement entirely.

**4. No Definition of "Representatives"** Section 2 allows disclosure to "Representatives" but the term is never defined. A standard NDA would define this to include employees, directors, legal counsel, financial advisors, and similar agents. Without a definition, Sferex could argue a narrow reading that excludes Calidon's advisors (creating operational problems), or Calidon could face claims that it disclosed to parties who didn't qualify. Either way, the ambiguity is a liability.

## **Materially Incomplete Provisions**

**5. Standard of Care is One-Sided and Potentially Weak** Section 2 requires Calidon to protect Proprietary Information with "the same care as Receiving Party uses to protect its own confidential information (but no less than reasonable care)." The problem: if Calidon has lax internal security practices, the contractual floor defaults to those lax practices. Sferex could argue the "no less than reasonable care" floor is a minimum, not a defined standard. A well-drafted NDA specifies "reasonable care" more concretely or ties it to industry standards. Calidon is exposed if its own practices fall below what a court would consider adequate.

**6. No Return or Destruction of Materials Clause** There is no requirement for Calidon to return or destroy Proprietary Information if the transaction falls through. This is standard and significant. Without it, Calidon is in continuous possession of Sferex's materials indefinitely, with ongoing confidentiality obligations and potential liability but no clear mechanism to terminate its exposure. Conversely, it also means Sferex could demand return at any time with no agreed process, creating operational disruption.

**7. No Limitation on Remedies / Injunctive Relief Clause** Most NDAs include an explicit acknowledgment that breach would cause irreparable harm and that the Disclosing Party is entitled to seek injunctive relief without posting a bond. Its absence here cuts both ways for Calidon: Sferex may be able to seek an emergency injunction anyway under general equity principles, but without agreed language, the standard and process are unpredictable. More importantly, there is no reciprocal limitation protecting Calidon from disproportionate remedies for minor or inadvertent disclosures.

**8. No Limitation on Damages** The agreement contains no cap on Calidon's liability for a breach. In a commercial NDA of this type, receiving parties typically negotiate a damages cap (often tied to a multiple of fees paid or a fixed dollar amount). Without one, a breach — even an inadvertent one — exposes Calidon to unlimited consequential, indirect, and punitive damages depending on the governing law (which, as noted above, is also undefined).

**9. No Residuals Clause** For Calidon's benefit, there is no residuals provision — meaning that information retained in the unaided memory of Calidon's representatives (ideas, concepts, know-how) cannot be freely used after the transaction evaluation ends. Depending on how broadly "Derived Information" in Section 1 is construed, Calidon's personnel could face claims that their subsequent work infringes the NDA even years later. A residuals clause would carve out good-faith memory-retained knowledge.

**10. No "No License" or "No Warranty" Clause** The agreement doesn't state that disclosure of Proprietary Information does not grant Calidon any license to use it beyond the evaluation, or that Sferex makes no representations about the accuracy of the information. This matters practically: Calidon could make a transaction decision based on Sferex's Proprietary Information and have no recourse if it turns out to be inaccurate, while simultaneously facing claims that any use of insights derived from that information is a breach.

## **Securities Provision (Section 4) — Materially Incomplete**

Section 4 contains only a point-in-time confirmation that neither party is *currently* required to disclose the transaction. It provides no forward-looking framework — no standstill obligation, no process for coordinating required future disclosures, and no agreement on who controls public announcements. If regulatory events require disclosure later (e.g., a tender offer, material definitive agreement, or SEC inquiry), Calidon has no contractual mechanism to coordinate with Sferex, exposing it to both securities law risk and breach claims simultaneously.

## **Non-Solicitation (Section 3) — Narrow but Notable**

The one-year non-solicitation is limited to personnel "introduced to Interested Party in connection with the Proposed Transaction." This creates a significant gap: Calidon could identify and poach Sferex employees it learned about through the disclosed materials (org charts, patents, technical documents) even if those individuals were never personally introduced. The clause protects introductions, not information-based identification. Sferex's drafting error, but Calidon should be aware of this if it becomes relevant in a dispute.

## **Summary Table**

|  |  |
| :-: | :-: |
| \*\*Missing / Incomplete Clause\*\* | \*\*Risk to Calidon\*\* |
| No governing law | Threshold litigation to determine applicable law |
| No term | Potentially perpetual or immediately expired obligations |
| "Proposed Transaction" undefined | Scope of covered information is ambiguous |
| "Representatives" undefined | Disclosure permissions are uncertain |
| Weak standard of care | Liability if Calidon's own practices are lax |
| No return/destruction obligation | Indefinite possession with indefinite liability |
| No injunctive relief / remedies clause | Unpredictable exposure to emergency court orders |
| No damages cap | Unlimited liability for any breach |
| No residuals clause | Employee knowledge may be permanently encumbered |
| No license / warranty disclaimer | No recourse if Sferex's information is inaccurate |
| Securities provision is point-in-time only | No coordination mechanism for future required disclosures |

  

# Gemini 3.1 Flash 

Based on a careful review of the provided Non-Disclosure Agreement (NDA), several standard commercial provisions are either entirely missing or materially incomplete.

Because this agreement is heavily one-way (protecting Sferex, the Disclosing Party, while placing restrictions on Calidon, the Receiving Party), the absence of these clauses creates significant legal, operational, and financial risks specifically for **Calidon**.

Here is the breakdown of the missing or incomplete clauses and the practical risks they pose to Calidon:

### **1. Missing an "Acknowledge No Representation or Warranty" Clause**

  - **What is missing:** A standard commercial NDA explicitly states that the Disclosing Party (Sferex) provides the information "as is" and makes no representations or warranties regarding its accuracy or completeness. It also explicitly states that the Disclosing Party will have no liability resulting from the Receiving Party's use of that information.
  - **The Risk to Calidon:** Without this clause, if Calidon relies on Sferex’s technical or financial data to evaluate the transaction, suffers a loss, or discovers the data was flawed, Calidon has no clear, pre-negotiated barrier protecting it from finger-pointing. Conversely, if Calidon accidentally misuses the information due to Sferex's own errors, Sferex could attempt to hold Calidon liable for the resulting fallout.

### **2. Missing a Definite "Term of Confidentiality" (Expiration)**

  - **What is missing:** The agreement explicitly notes TERM: \[Not stated in this agreement\]. A standard commercial NDA defines a specific survival period for confidentiality obligations (typically 2 to 5 years from disclosure or termination).
  - **The Risk to Calidon:** In the absence of an explicit term, this obligation could legally be interpreted as **perpendicular/perpetual**. Calidon is effectively signing up to protect Sferex’s biometrics data *forever*. This creates an indefinite operational burden for Calidon’s compliance, IT, and legal teams, who must continuously isolate and track this data decades into the future.

### **3. Materially Incomplete "Exclusions from Proprietary Information" (Clause 1)**

  - **What is missing:** While Clause 1 lists standard exclusions (public knowledge, prior knowledge, independent development), it completely omits a critical fourth exception: **information received from a third party** who has a legal right to disclose it and is not bound by a confidentiality agreement with Sferex.
  - **The Risk to Calidon:** If Calidon legitimately acquires identical biometrics data or market insights from an independent third-party vendor, consultant, or public researcher, Sferex could still claim that Calidon is in breach of *this* agreement because the third-party route isn't a carved-out exclusion. Calidon would bear the heavy evidentiary burden of proving independent development instead of a simple third-party receipt.

### **4. Missing a "Return or Destruction of Information" Clause**

  - **What is missing:** Commercial NDAs always feature a clause dictating what happens to the data if negotiations collapse. It usually requires the Receiving Party to promptly return or destroy all Proprietary Information (and Derived Information) upon the written request of the Disclosing Party, often allowing Calidon to retain one copy for legal compliance/archival purposes.
  - **The Risk to Calidon:** Because there is no protocol, Sferex could demand immediate physical return of all items at an exorbitant cost to Calidon, or conversely, sue for breach if Calidon automatically purges the data during routine server maintenance. Furthermore, without a standard **"IT Backup/Archival Exception"** (which allows data to persist on automated, secure backup tapes until overwritten per standard retention policies), Calidon is technically in breach the moment Sferex's data hits Calidon's disaster-recovery backups, as it is nearly impossible to completely scrub a single file from enterprise-level mirrors.

### **5. Materially Incomplete "Compelled Disclosure" Clause (Clause 2.4)**

  - **What is missing:** While Clause 2.4 allows Calidon to disclose information if legally required, it states that Calidon must *"seek reliable assurances of confidential treatment"* if no protective order is obtained.
  - **The Risk to Calidon:** This places an unrealistic, mandatory burden on Calidon. If Calidon is subpoenaed by a court or government regulator, Calidon cannot force a judge or federal agency to provide "reliable assurances" of confidentiality. As written, if the court refuses to give assurances, Calidon is trapped in a paradox: comply with the law and breach the NDA, or respect the NDA and face contempt of court. The clause should instead state that Calidon will use *reasonable efforts* to request confidential treatment, without making it a strict condition of disclosure.

### **6. Missing "Remedies" and "No Equitable Relief Acknowledgment" Clauses**

  - **What is missing:** Standard NDAs usually include an injunction clause stating that a breach would cause irreparable harm, entitling the injured party to equitable relief (injunctions) without proving actual damages.
  - **The Risk to Calidon:** While this omission usually favors a Receiving Party, its absence here creates **ambiguity**. If Sferex sues Calidon alleging a leak, the lack of defined remedies, lack of a waiver of jury trial, and lack of an **Attorneys' Fees provision** means that if Calidon successfully defends itself against a frivolous lawsuit by Sferex, Calidon cannot automatically recover its massive legal fees from Sferex. Each party would bear its own costs under the American Rule.

### **7. Missing "Governing Law and Jurisdiction"**

  - **What is missing:** The text explicitly states GOVERNING LAW: \[Not stated in this agreement\].
  - **The Risk to Calidon:** If a dispute arises, it triggers an expensive, unpredictable pre-lawsuit battle over *where* the lawsuit should take place and *which* state's laws apply. If Sferex is based in a different state or country, Calidon risks being dragged into an inconvenient, hostile forum to litigate under unfamiliar state laws.

### **Summary of the Overarching Threat to Calidon**

This NDA functions as a regulatory trap for Calidon. Because **"Derived Information"** (Clause 1) is included in the definition of protected data, any internal data science models, evaluation spreadsheets, or analysis Calidon's team builds during this project are permanently locked under Sferex's ownership control. Combined with the **indefinite term**, the **strict non-solicitation of key personnel** (Clause 3), and the **lack of a third-party exclusion**, Calidon risks paralyzing its own internal development or future hiring in the biometrics space simply by reviewing Sferex's materials.

  

# GPT 5.5 

### **Key takeaway**

This NDA covers definition of confidential information, use/disclosure restrictions, compelled disclosure, non-solicitation, and no-obligation-to-close. For Calidon as the Receiving Party, the biggest risks come from what is missing or materially incomplete: no term, no return/destruction mechanics, no residuals carve-out, no disclosure-right carve-outs for advisors/financing/regulators, no remedies/exclusive-remedies framework, no assignment/change-of-control rule, no integration/waiver clauses, no notice mechanics, and no export/privacy/security provisions despite biometric subject matter. Several other clauses are present but drafted too narrowly or one-sided.

Highest-risk omissions for Calidon

1.  No confidentiality term or survival period → obligations may be argued to last indefinitely.
2.  No return/destruction of information → uncertainty about what Calidon must retain, destroy, or can legally keep for records/compliance.
3.  No residuals clause → risk that employees cannot later use general know-how retained in unaided memory.
4.  No express carve-out for disclosure to financing sources, auditors, insurers, affiliates, or regulators → ordinary transaction workstreams become contractual risk.
5.  No data-security / privacy / export-control allocation despite biometric information → potential compliance exposure and unclear responsibility boundaries.

### **Clause-by-clause gap analysis**

|  |  |
| :-: | :-: |
| \*\*Missing / materially incomplete provision\*\* | \*\*Practical risk to Calidon (Receiving Party)\*\* |
| 1\\. No term / duration of confidentiality obligationsAgreement explicitly says TERM: \\\[Not stated\\\]. | Calidon may face arguments that confidentiality, use restrictions, and the ban on disclosing the existence/terms of discussions survive indefinitely. This creates record-retention burdens, operational uncertainty, and potential future disputes over stale information that has lost commercial sensitivity. |
| 2\\. No survival structure tied to categories of informationThere is no distinction between trade secrets, technical data, business plans, or transaction discussions. | Even if a court implies a “reasonable time,” the lack of category-specific survival creates litigation uncertainty. Calidon cannot confidently determine when obligations end for non–trade-secret business information. |
| 3\\. No return or destruction clauseNo requirement or permission regarding return, deletion, destruction, backup tapes, legal holds, audit copies, or compliance archives. | Calidon does not know whether it must destroy everything on demand, may keep archival copies, or may retain materials required by law, litigation hold, tax, accounting, or regulatory obligations. That ambiguity itself becomes breach risk and operational cost. |
| 4\\. No residuals / unaided memory carve-outThe definition sweeps in Derived Information prepared by Receiving Party that reflects or is based upon the Disclosing Party's information. | Employees who legitimately learned general ideas, skills, or know-how during evaluation could later be accused of using “derived” information. Without a residuals clause, Calidon has less protection for future independent work by personnel who were exposed to the information. |
| 5\\. No express carve-out for disclosures to financing sources, auditors, insurers, affiliates, potential acquirers, regulators, or professional advisorsClause 2 permits disclosure only to Representatives actively and directly participating in the evaluation of the Proposed Transaction. | The phrase is too narrow for real transaction practice. Calidon may need to share information with lenders, investment committees, insurers, auditors, outside accountants, tax advisors, or affiliated entities involved in diligence or approval. Each disclosure becomes debatable breach territory. |
| 6\\. No explicit permission to retain/use information for legal, compliance, tax, audit, or insurance purposes after evaluation ends | Calidon may be forced into an all-or-nothing position: destroy materials and impair compliance evidence, or retain them and face an argument that continued possession or internal use violates the agreement. |
| 7\\. No data-security standard, incident-notification clause, or allocation of responsibility for biometric dataThe counterparty is Sferex Biometrics, Inc., suggesting potentially sensitive biometric-related information. | If biometric, personal, or regulated data are disclosed, the agreement does not specify required safeguards, breach notification timing, subcontractor controls, or whether such data may be disclosed at all. Calidon faces unclear compliance expectations and potential statutory exposure. |
| 8\\. No privacy-law compliance representation or data-minimization restrictionThe NDA does not say whether disclosed data were lawfully collected, whether consents exist, or whether personal data should be anonymized. | Calidon could receive data that create obligations under privacy, biometric, employment, or sector-specific laws without any contractual assurance from the disclosing party that the disclosure is lawful. |
| 9\\. No export-control / sanctions compliance clause | Technical information may be export-controlled. The agreement provides no allocation of responsibility or warning mechanism. Calidon could inadvertently transmit controlled technical data across borders or to restricted persons during diligence. |
| 10\\. No non-reliance / no-representation clauseThe agreement says no obligation to complete a transaction, but it does not say the disclosing party makes no representation or warranty as to accuracy/completeness of the information. | Calidon has weaker contractual protection against claims or disputes arising from inaccurate diligence materials. While tort and securities-law issues are separate, a standard NDA often clarifies that diligence information is provided “as is” except as later set forth in a definitive agreement. |
| 11\\. No remedies framework (injunctive relief, specific performance, exclusive remedies, bond waiver, fee shifting)The NDA says nothing about equitable relief, damages, attorneys’ fees, or whether remedies are cumulative. | This omission is not always pro-disclosing-party; it creates uncertainty for both sides. For Calidon, the risk is unpredictability: the disclosing party may seek broad equitable relief under general law, and the parties have not negotiated limits, fee allocation, or procedural protections. |
| 12\\. No assignment / change-of-control clause | If Calidon reorganizes, sells a business unit, merges, or assigns diligence activities to an affiliate, it is unclear whether confidentiality obligations can be transferred or whether sharing with successors is permitted. |
| 13\\. No entire agreement / integration clause | Emails, decks, meeting statements, or prior understandings may be argued to supplement or modify the NDA. Calidon loses certainty about the full contractual universe governing confidentiality. |
| 14\\. No amendment / waiver formalities | Without a “written amendment only” and “no waiver unless in writing” clause, parties may later dispute whether conduct, oral statements, or selective enforcement changed the NDA. |
| 15\\. No notice provisionClause 2.4 requires promptly notify Disclosing Party, but gives no notice addresses, methods, deemed-receipt rules, or emergency contact process. | In a subpoena or regulatory demand, Calidon may be accused of insufficient or untimely notice even though the agreement provides no operational mechanics. |
| 16\\. No severability clause | If a court invalidates the non-solicit, the confidentiality definition, or another provision, the parties may litigate whether the rest of the NDA survives intact. |
| 17\\. No counterpart / electronic-signature clause | Usually low risk today, but it creates avoidable execution and evidentiary questions if signatures were exchanged electronically. |
| 18\\. No governing law or forum selectionThe agreement expressly leaves GOVERNING LAW: \\\[Not stated\\\] blank. | This is a major litigation-risk omission. Calidon faces uncertainty over applicable law, enforceability standards (especially for the non-solicit), available remedies, limitation periods, and where disputes may be brought. |

### **Material incompleteness in clauses that do exist**

|  |  |  |
| :-: | :-: | :-: |
| \*\*Existing clause\*\* | \*\*Why incomplete / one-sided\*\* | \*\*Risk to Calidon\*\* |
| Proprietary Information definition | No requirement that information be marked confidential, identified as confidential, or confirmed in writing after oral disclosure. It also includes the existence of discussions and all “Derived Information.” | Calidon must treat a very broad universe of information as confidential, including internally created analyses and possibly oral statements that were never identified as confidential, increasing compliance burden and dispute risk. |
| Exclusions | No express exclusion for information received from a third party without breach; no exclusion for information approved for release in writing by the disclosing party; no carve-out for legally compelled disclosures beyond §2.4. | Calidon may have to prove “independent development” instead of relying on a cleaner third-party-source exclusion, and may face arguments that information obtained from another lawful source remains restricted. |
| Disclosure to Representatives | Limited to those “actively and directly participating in the evaluation.” No express coverage for financing, governance approvals, or back-office functions supporting the transaction. | Ordinary diligence and approval workflows become harder to manage contractually. |
| Compelled disclosure | Requires prompt notice and efforts to seek confidential treatment, but does not excuse notice when legally prohibited, does not allocate who bears the cost of protective-order efforts, and does not specify response timing. | Calidon may be forced to choose between obeying a subpoena/regulatory order and risking an NDA claim, while also absorbing legal costs and operational uncertainty. |
| Non-solicitation | No geographic scope, no carve-out for general solicitations or employees who apply without solicitation, no definition of “key technical or management personnel,” and no forum/law selection to assess enforceability. | Calidon could face claims over ordinary recruiting activity, and the enforceability question becomes more expensive because governing law and venue are unstated. |

Most consequential risk cluster

For Calidon, the most consequential combination is no term + no return/destruction + no residuals + no governing law/forum. Together they make it difficult to know how long obligations last, what must be retained or destroyed, whether employees can later use generalized know-how, and which jurisdiction’s rules apply. That uncertainty is often more expensive than a clearly drafted but stricter NDA, because it raises ongoing compliance costs and future litigation risk.

If Calidon were redlining this NDA, the highest-priority additions would be

1.  A fixed confidentiality term (for example, 2–5 years for non–trade-secret information; trade secrets protected while they remain trade secrets under applicable law).
2.  A return/destruction clause with archival, backup, legal-hold, audit, tax, insurance, and regulatory-retention carve-outs.
3.  A residuals clause protecting use of unaided memory/general know-how.
4.  Expanded permitted-disclosure language for affiliates, financing sources, auditors, accountants, insurers, and regulators/advisors involved in the transaction.
5.  Governing law, forum selection, notice mechanics, and standard integration/amendment/waiver/severability language.
6.  Privacy, security, and export-control provisions tailored to any biometric or personal data actually being shared.

Not legal advice: This is a contract-risk analysis, not a legal opinion. The enforceability of the non-solicit, confidentiality duration, and available remedies can vary significantly by jurisdiction—particularly because governing law and venue are unstated.

  
  

# Muse Spark 

This 2014 draft is a classic one-way NDA written for Sferex, not Calidon. It gives Sferex broad rights and leaves Calidon with open-ended duties because the normal guardrails are blank or vague.

  

Here are the gaps, and what each one means for you as the Receiving Party:

  

\#\# 1. No confidentiality term or survival period

\- \*\*What’s missing:\*\* "TERM: \[Not stated\]" and no end date for the secrecy duty.

\- \*\*Risk for Calidon:\*\* Without a term, the default is perpetual. A standard NDA usually says the duty lasts "until the Confidential Information no longer qualifies as a trade secret... or until Disclosing Party sends written notice". Here you would have to protect every discussion from 2014 forever, even after the deal dies, which creates storage costs, training burden, and litigation exposure for ancient emails.

  

\#\# 2. No return-or-destroy provision

\- \*\*What’s missing:\*\* No requirement to give back or delete Sferex materials when evaluation ends.

\- \*\*Risk:\*\* Holland & Knight notes a return provision "is desirable" because it lets the receiving party clean house. Without it, Calidon must keep Sferex data indefinitely, increasing the chance of an accidental leak and making e-discovery more expensive.

  

\#\# 3. "Limited use" is not actually limited

\- \*\*What’s incomplete:\*\* Section 2 only bans disclosure, it never says you may use the information "solely to evaluate the Proposed Transaction."

\- \*\*Risk:\*\* Holland & Knight flags that an NDA "establishes limits on the recipient's permissible use". Because use is undefined, Sferex could later claim that any internal product work that even resembles their data is a breach, even if you never disclosed it.

  

\#\# 4. Overbroad definition with no marking protocol

\- \*\*What’s incomplete:\*\* "any and all information... including discussions, proposed terms, existence of this Agreement" with no requirement to mark or confirm in writing.

\- \*\*Risk:\*\* Courts accept broad definitions, but they "may engender debate about whether particular information is covered". For Calidon, that debate cuts the wrong way: you must treat every hallway conversation as secret, and you have no way to prove something was not confidential.

  

\#\# 5. Exclusions are missing the third-party source carve-out

\- \*\*What’s incomplete:\*\* Standard exclusions include information "learned by Receiving Party through legitimate means other than from Disclosing Party". Your draft only lists public, prior knowledge, and independent development.

\- \*\*Risk:\*\* If Calidon later gets the same biometrics data from a university partner, you are still bound by this NDA because the third-party path is not excluded.

  

\#\# 6. "Representatives" undefined, no written downstream NDAs

\- \*\*What’s incomplete:\*\* Section 2 allows disclosure to Representatives "bound by comparable confidentiality obligations" but never defines who counts, and does not require Calidon to get signed agreements.

\- \*\*Risk:\*\* A standard clause requires you to "carefully restrict access... and shall require those persons to sign nondisclosure restrictions at least as protective". Without that clarity, you could breach by looping in outside counsel or a contractor, and you would be strictly liable for their mistakes.

  

\#\# 7. No ownership and no-license language

\- \*\*What’s missing:\*\* No statement that Sferex retains all rights.

\- \*\*Risk:\*\* Normal NDAs say disclosure "shall not be construed as granting Receiving Party any rights". Without it, Sferex could argue that your "Derived Information" gives them ownership claims over Calidon work product.

  

\#\# 8. No disclaimer of accuracy or warranties

\- \*\*What’s missing:\*\* No "as-is" clause.

\- \*\*Risk:\*\* Calidon may rely on Sferex data to model a deal, then discover it was wrong. Without a disclaimer, expectations are unclear, and Sferex could claim you assumed the risk of using flawed data.

  

\#\# 9. Compelled disclosure is one-sided

\- \*\*What’s incomplete:\*\* You must notify Sferex promptly, but there is no "to the extent legally permitted" qualifier and no cost-shifting.

\- \*\*Risk:\*\* If a subpoena bars notice, you breach by notifying. If Sferex wants to fight, Calidon pays the lawyers.

  

\#\# 10. No residuals clause

\- \*\*What’s missing:\*\* No right to use general knowledge retained in unaided memory.

\- \*\*Risk:\*\* Tech attorneys warn that omitting residuals favors the discloser. Calidon engineers who remember a concept must pretend they do not, chilling future R\&D.

  

\#\# 11. Non-solicitation is blunt and broad

\- \*\*What’s incomplete:\*\* One-year ban on employing or soliciting "any key technical or management personnel... introduced," with no carve-outs for general advertising, unsolicited applications, or terminations by Sferex.

\- \*\*Risk:\*\* Calidon cannot hire talent that approaches you independently, even for unrelated roles. "Key" and "introduced" are undefined, inviting disputes.

  

\#\# 12. No remedies, injunctive relief, or liability cap

\- \*\*What’s missing:\*\* No acknowledgment of irreparable harm.

\- \*\*Risk:\*\* Standard NDAs address relief because "the primary goal is to halt the ongoing misappropriation through a temporary or permanent injunction". Without language, Calidon faces uncertainty: Sferex can still seek injunctions and unlimited damages, but you have not negotiated a limit or a bond requirement.

  

\#\# 13. Governing law and venue blank

\- \*\*What’s missing:\*\* "\[Not stated\]"

\- \*\*Risk:\*\* A normal clause specifies which state's law controls. Without it, Sferex could sue Calidon in Delaware or wherever Sferex is incorporated, forcing you to litigate under unfamiliar law and travel.

  

\#\# 14. Missing boilerplate protections

\- \*\*Entire Agreement:\*\* absent, so prior emails could modify the deal. Standard form says it "replaces and supersedes any and all oral agreements".

\- \*\*Waiver:\*\* absent, meaning a single failure to enforce could be argued as a waiver. Standard says failure "shall not be a waiver".

\- \*\*Severability:\*\* absent, so if a court finds the non-solicit overbroad, the whole NDA could fall. Standard keeps remaining provisions alive.

\- \*\*Assignment:\*\* absent, so Sferex could assign the NDA to a competitor, and Calidon would owe duties to a stranger.

\- \*\*Notices:\*\* absent, so you have no safe address for the compelled-disclosure notice.

  

\#\# 15. Securities clause is toothless

\- \*\*What’s incomplete:\*\* Section 4 only says no public disclosure is required today. It does not prohibit trading on material nonpublic information.

\- \*\*Risk:\*\* Calidon personnel who learn deal terms get no warning about insider-trading rules, leaving Calidon exposed to SEC risk without contractual cover.

  

\#\# 16. No "no obligation to transact" clarity beyond Section 5

\- \*\*What’s incomplete:\*\* Section 5 is vague and does not say Sferex has no duty to disclose anything.

\- \*\*Risk:\*\* Minor, but it leaves room for an argument that Sferex must share more once discussions start.

  

\---

  

\#\#\# Bottom line for Calidon

  

You would be signing up to:

\- keep everything secret forever, with no way to purge files

\- limit hiring for a year without safe harbors

\- face lawsuits in an unknown court, with unlimited damages and no cost protection

\- treat all oral discussions as confidential, while lacking the usual exclusions that let you use public or third-party information

  

In a balanced commercial NDA, Calidon would insist on: a 3-5 year confidentiality term (longer for trade secrets), a return/destroy obligation, a clear "use solely to evaluate" purpose, a marking protocol or written confirmation for oral disclosures, full exclusions including third-party receipt, a defined Representatives list with written downstream NDAs, a residuals carve-out, narrowed non-solicit with general-advertising exceptions, governing law (California, given your Stanford base), venue, cost-shifting for compelled disclosure, and standard boilerplate.

  

Without those, the practical burden stays entirely on the Receiving Party.

  
  
  

# Qwen 3.7 Plus

  

\# Missing or Materially Incomplete Provisions — Risk Analysis for Calidon Industries, Inc.

  

Below is a systematic review of the NDA. I have grouped the omissions into categories, noting for each why it matters to Calidon as the Receiving Party.

  

\---

  

\#\# 1. No Stated Term or Duration of Confidentiality Obligations

  

\*\*What is missing:\*\* There is no expiration date — neither for the agreement as a whole nor for the confidentiality obligations themselves.

  

\*\*Risk to Calidon:\*\* Calidon is exposed to \*\*perpetual liability\*\*. Even decades from now, Sferex could allege a breach based on information received under this 2014 NDA. In M\&A and commercial contexts, confidentiality periods are typically 2–5 years (with trade secrets sometimes carved out for longer). The absence of a term makes Calidon's ongoing compliance burden unbounded and uninsurable in practice.

  

\---

  

\#\# 2. No Governing Law or Jurisdiction / Forum Selection Clause

  

\*\*What is missing:\*\* The bracketed placeholder "\[Not stated in this agreement\]" appears under Governing Law, and there is no forum selection or dispute-resolution clause.

  

\*\*Risk to Calidon:\*\* If Sferex brings a claim, Calidon has no contractual basis to insist on a particular state's law or a convenient court. Sferex could select a plaintiff-friendly jurisdiction, forcing Calidon into costly, distant litigation under unfamiliar legal standards. This is especially problematic because the parties appear to be U.S. corporations (Inc.), where choice-of-law can materially affect remedies and interpretation.

  

\---

  

\#\# 3. No Return or Destruction of Confidential Information Clause

  

\*\*What is missing:\*\* There is no provision requiring or permitting Calidon to return or destroy Proprietary Information upon termination of discussions, nor any standard carve-out allowing retention of one archival copy for compliance purposes.

  

\*\*Risk to Calidon:\*\* When the Proposed Transaction ends (whether it closes or collapses), Calidon has \*\*no contractually agreed exit mechanism\*\*. Sferex could later demand return of every document, email, and notebook — and Calidon would have no defense that it followed an agreed destruction protocol. Routine IT backups, compliance archives, or litigation holds could later be characterized as breaches.

  

\---

  

\#\# 4. No Notice Provisions

  

\*\*What is missing:\*\* There is no clause specifying how notices must be delivered (e.g., certified mail, email to a specified address, overnight courier), to whom, or when notice is deemed effective.

  

\*\*Risk to Calidon:\*\* Section 2.4 requires Calidon to "promptly notify" Sferex if legally compelled to disclose information. Without a notice clause, Calidon has no safe harbor for how to deliver that notice. Sferex could later argue that notice was inadequate, late, or sent to the wrong person — turning a procedural gap into a substantive breach claim.

  

\---

  

\#\# 5. No Assignment Clause

  

\*\*What is missing:\*\* There is no restriction on either party's ability to assign its rights or obligations under the NDA.

  

\*\*Risk to Calidon:\*\* Sferex could \*\*assign the NDA to a competitor of Calidon\*\* or to a hostile third party, who would then step into Sferex's shoes and gain broad enforcement rights — including the right to sue Calidon for breach and to receive the benefit of all confidentiality obligations. Calidon entered into this agreement based on a specific counterparty; assignment destroys that assumption.

  

\---

  

\#\# 6. No "Entire Agreement," Amendment, or Waiver Clauses

  

\*\*What is missing:\*\* There is no integration clause (stating this is the entire agreement), no clause requiring amendments to be in writing, and no clause stating that a failure to enforce a right does not constitute a waiver.

  

\*\*Risk to Calidon:\*\*

\*   Sferex could allege that \*\*oral side-agreements or email exchanges\*\* modified Calidon's obligations.

\*   If Sferex tolerates a minor breach and later decides to enforce the NDA strictly, Calidon cannot point to a no-waiver clause to argue that the right was forfeited. This creates significant evidentiary uncertainty in any dispute.

  

\---

  

\#\# 7. No Severability Clause

  

\*\*What is missing:\*\* There is no provision stating that if one clause is held unenforceable, the remainder of the agreement survives.

  

\*\*Risk to Calidon:\*\* If a court finds one provision (e.g., the employee non-solicitation in Section 3, or the breadth of the "Proprietary Information" definition) to be overbroad or unenforceable, it could void the \*\*entire NDA\*\*. While this might seem to benefit Calidon, it creates total uncertainty — neither party would know which obligations remain, and Sferex could seek equitable relief outside the contract entirely.

  

\---

  

\#\# 8. Missing Standard Exclusion from "Proprietary Information"

  

\*\*What is missing:\*\* Section 1 lists three standard exclusions (public availability, prior knowledge, independent development) but \*\*omits the exclusion for information received from a third party without a confidentiality obligation\*\*.

  

\*\*Risk to Calidon:\*\* If Calidon legitimately receives the same information from another source (e.g., a different bidder, a public filing, a consultant working for multiple parties), Calidon is still bound by this NDA with respect to that information. This is an unreasonable restriction that could trap Calidon in a breach claim even when the information was obtained through an independent, lawful channel.

  

\---

  

\#\# 9. Undefined "Representatives"

  

\*\*What is missing:\*\* Section 2 permits disclosure to "Representatives" but the term is never defined.

  

\*\*Risk to Calidon:\*\* It is unclear whether Calidon's outside counsel, accountants, financial advisors, lenders, or potential equity co-investors qualify as "Representatives." If a court interprets the term narrowly, Calidon could be found in breach for sharing information with its own deal team or professional advisors — the very people it needs to evaluate the Proposed Transaction.

  

\---

  

\#\# 10. No Carve-Out for Regulatory, Auditor, or Stock Exchange Disclosures

  

\*\*What is missing:\*\* Section 2.4 covers disclosures compelled by "law or legal process," but there is no express permission for voluntary (but legally expected) disclosures to auditors, regulators, or stock exchange listing authorities.

  

\*\*Risk to Calidon:\*\* If Calidon is a public company (or is regulated), its auditors may request information about the Proposed Transaction as part of routine audit procedures, or a regulator may make an informal inquiry. Without a specific carve-out, Calidon is caught between breaching the NDA or breaching its regulatory/audit obligations. The "compelled disclosure" language may not cover informal but customary regulatory inquiries.

  

\---

  

\#\# 11. No Ownership or Usage Rights for "Derived Information"

  

\*\*What is missing:\*\* Section 1 defines "Derived Information" (work product prepared by Calidon that reflects or is based on Sferex's information) as Proprietary Information, but \*\*no clause allocates ownership\*\* of that Derived Information or states whether Calidon may use its own analytical work product.

  

\*\*Risk to Calidon:\*\* Calidon may invest significant time and resources preparing valuation models, technical analyses, or integration plans. Under the NDA as drafted, all of that work product belongs to — or is at least controlled by — Sferex. If the deal fails, Calidon may be prohibited from reusing its own analytical frameworks or insights in connection with a competing transaction, even where no raw Sferex data is used.

  

\---

  

\#\# 12. No Residual Knowledge / Residuals Clause

  

\*\*What is missing:\*\* There is no clause permitting Calidon to use information retained in the unaided memories of its Representatives.

  

\*\*Risk to Calidon:\*\* In the absence of a residuals clause, Calidon's executives and directors could be liable for acting on general ideas, concepts, or impressions they remember from reviewing Sferex's information — even if they cannot point to any specific document or data they misappropriated. This is an exceptionally broad and difficult-to-police standard that creates litigation risk long after the deal ends.

  

\---

  

\#\# 13. No Survival Clause

  

\*\*What is missing:\*\* There is no clause specifying which obligations survive termination or expiration of the NDA.

  

\*\*Risk to Calidon:\*\* If the parties treat the NDA as having ended (e.g., after the deal is abandoned), there is no clarity on whether the confidentiality obligations, the non-solicitation covenant, or the securities representations continue. This ambiguity cuts both ways, but for Calidon it means it cannot confidently wind down its compliance processes.

  

\---

  

\#\# 14. Section 2.4 (Compelled Disclosure) Is Materially Incomplete

  

\*\*What is missing:\*\* The clause requires Calidon to notify Sferex and to disclose "only what is legally required," but it does not specify:

\*   A minimum time period Calidon must wait for Sferex to seek a protective order before disclosing.

\*   What happens if Sferex simply does not respond to the notice.

\*   Whether Calidon must cooperate at its own expense in Sferex's legal efforts.

  

\*\*Risk to Calidon:\*\* If a court or agency sets a short deadline for production, Calidon cannot safely wait indefinitely for Sferex to act. Without a "drop-dead" date or a provision allowing disclosure if Sferex fails to pursue relief, Calidon is forced to guess — and a wrong guess is either contempt of a legal order (if it waits too long) or breach of the NDA (if it discloses too soon).

  

\---

  

\#\# 15. No Clause Addressing the Interaction with the Non-Solicitation Covenant (Section 3)

  

\*\*What is missing:\*\* Section 3 prohibits solicitation of personnel "introduced to Interested Party in connection with the Proposed Transaction" for one year from the Effective Date — but there is no carve-out for \*\*general solicitations\*\* (e.g., public job postings, recruiter engagements) that happen to reach a Sferex employee.

  

\*\*Risk to Calidon:\*\* Standard non-solicitation clauses expressly exclude general, non-targeted recruiting. Without that carve-out, Calidon could be in breach of the NDA simply because a Sferex employee responded to a public LinkedIn posting or a headhunter's general outreach. The one-year period runs from the Effective Date (February 2014), meaning it expires in February 2015 — but if deal discussions drag on, the restriction could lapse while due diligence is still ongoing, creating a false sense of security.

  

\---

  

\#\# Summary

  

The NDA is heavily skewed toward Sferex's protections but is, paradoxically, so incomplete that it creates \*\*significant interpretive and litigation risk for Calidon\*\*. The most commercially dangerous omissions for Calidon are the \*\*perpetual term\*\*, the \*\*absence of a return/destruction protocol\*\*, the \*\*undefined "Representatives,"\*\* and the \*\*treatment of Derived Information as Sferex's Proprietary Information\*\* without any ownership clarification. Calidon should not sign this agreement in its current form.

  
  

# A1 grading  

**LegalEval v6 — A1 Grading**

Missing-Clause Detection · /16 · Gates: Faithfulness + Directionality

|  |
| :-: |
| \*\*GRADING NOTE\*\*  Scores produced by an Anthropic Claude-family grader; Claude Sonnet 4.6 is among the models under test. Procedure per v6 §6.2: score dimensions → raw total → normalize to prompt max → cap at 0.40 on any gate trip. Run date June 9, 2026. |

**Task:** Missing-Clause Detection (Calidon/Sferex NDA). Max /16. Gates: Faithfulness + Directionality. Gold: Bucket 1 (harms Calidon: governing law + term mandatory; cap, residuals, 4th exclusion, non-solicit carve-outs, §2.4 refinement partial) vs Bucket 2 (favors Calidon: standstill, return/destruction, injunctive relief, no-reliance, Representatives liability). Faithfulness trips on claiming §2.4 absent or inventing clauses; Directionality trips only on recommending Calidon add a standstill.

|  |  |  |  |  |  |  |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| \*\*Model\*\* | \*\*Faith /3\*\* | \*\*Dir /4\*\* | \*\*Cov /4\*\* | \*\*Snd /3\*\* | \*\*Act /2\*\* | \*\*Raw → Norm\*\* |
| \*\*Claude Sonnet 4.6\*\* | 3 | 1.5 | 3 | 2 | 1.5 | 11 → 0.69 |
| \*\*Gemini 3.1 Flash\*\* | 3 | 1.5 | 2.5 | 2 | 1 | 10 → 0.63 |
| \*\*GPT 5.5\*\* | 3 | 2 | 4 | 2.5 | 1.5 | 13 → 0.81 |
| \*\*Muse Spark\*\* | 1 ⚠ GATE | 1.5 | 4 | 2 | 1.5 | 10 → 0.63 → 0.40 capped |
| \*\*Qwen 3.7 Plus\*\* | 3 | 2 | 3.5 | 2.5 | 1.5 | 12.5 → 0.78 |

**Claude Sonnet 4.6 — 11/16 (0.69)**

  - **Faithfulness 3/3.** No invented clauses; §2.4 never claimed absent (not discussed).
  - **Directionality 1.5/4.** No bucket split. Return/destruction (\#6) and the no-warranty disclaimer (\#10) framed as Calidon risks — the no-warranty framing is backwards (absence preserves Calidon's reliance claims). Names 'no standstill obligation' as a deficiency inside the §4 analysis — graded as a deduction, not a gate trip, since no addition is recommended and the attached risk reasoning concerns disclosure coordination; flagged for human confirm. Offsetting credit: the §3 non-solicit analysis correctly reads the introduced-only gap as favoring Calidon — the one genuinely directional insight in the response.
  - **Coverage 3/4.** Governing law ✓, term ✓. Partial: damages cap ✓, residuals ✓. Missed: 4th third-party exclusion; §2.4 refinement; non-solicit carve-outs at half-credit.
  - **Soundness 2/3.** No-warranty direction misread; injunctive-relief framing hedged ('cuts both ways'). Otherwise legally correct.
  - **Actionability 1.5/2.** Severity-ordered with summary table; no which-gaps-not-to-volunteer guidance.

**Gemini 3.1 Flash — 10/16 (0.63)**

  - **Faithfulness 3/3.** §2.4 correctly treated as present-but-incomplete with the reasonable-efforts refinement. No fabrications ('perpendicular/perpetual' is a typo, not a claim).
  - **Directionality 1.5/4.** No bucket split; no-warranty (\#1) and return/destruction (\#4) framed as Calidon risks. No standstill recommendation; no offsetting directional insight.
  - **Coverage 2.5/4.** Mandatory met. Partial: 4th exclusion ✓, §2.4 refinement ✓. Missed: damages cap, residuals (derived-info lock-in in the summary earns half at most), non-solicit carve-outs.
  - **Soundness 2/3.** 'Permanently locked under Sferex's ownership control' conflates confidentiality with ownership; no-warranty direction misread. Backup-tape breach point is genuinely practical.
  - **Actionability 1/2.** Undifferentiated 7-item list; no prioritization.

**GPT 5.5 — 13/16 (0.81)**

  - **Faithfulness 3/3.** 18-item sweep, zero fabrications; §2.4 treated as present and refined (notice-when-prohibited, cost allocation, timing — matches the rubric's refinement credit).
  - **Directionality 2/4.** Best of field but still no bucket split. Directional awareness present ('this omission is not always pro-disclosing-party'). Residuals correctly a Calidon risk (Bucket 1 ✓). Misframes: no-reliance as Calidon risk; return/destruction as risk (defensible-ask, minor).
  - **Coverage 4/4.** Mandatory ✓✓; residuals ✓, 4th exclusion ✓, non-solicit carve-outs ✓, §2.4 refinement ✓, cap partially via remedies framework. Most complete Bucket 1 sweep in the run.
  - **Soundness 2.5/3.** Legally strong; no-reliance misread is the one error. Privacy/export/biometric items are defensible extensions, not fabrications.
  - **Actionability 1.5/2.** Closes with an explicit 6-item priority list, but the 18-row table is the long undifferentiated checklist the rubric dings.

**Muse Spark — raw 10/16 (0.63) → CAPPED 0.40 · FAITHFULNESS GATE**

  - **Faithfulness 1/3 — GATE.** Trip evidence: 'governing law (California, given your Stanford base)' — asserts a party fact about Calidon found nowhere in the instance (apparent context bleed). Compounding: quoted attributions to external commentary ('Holland & Knight notes…', 'Standard form says…') presented as quotations without verifiable sourcing — fabricated-citation risk under the gate definition. Queued for human confirm; uncapped counterfactual is 0.63.
  - **Directionality 1.5/4.** 'The practical burden stays entirely on the Receiving Party' framing; no-warranty (\#8) and injunctive relief (\#12) framed as Calidon needs; no bucket split; no standstill recommendation.
  - **Coverage 4/4.** Widest sweep alongside GPT: mandatory ✓✓, residuals ✓, 4th exclusion ✓, non-solicit carve-outs ✓, §2.4 refinement ✓ ('to the extent legally permitted' + cost-shifting — exact rubric language), cap ✓, plus use-limitation and marking-protocol finds.
  - **Soundness 2/3.** Severability all-or-nothing overstatement; derived-info ownership conflation; the California recommendation rests on the fabricated fact.
  - **Actionability 1.5/2.** Strong bottom-line section with a concrete insist-on list.

**Qwen 3.7 Plus — 12.5/16 (0.78)**

  - **Faithfulness 3/3.** No fabrications; §2.4 treated as present with refinement (drop-dead date, non-response handling, cost cooperation); correct in-instance date math (non-solicit expires Feb 2015).
  - **Directionality 2/4.** No bucket split, but the cleanest hands: avoids the no-warranty misframe entirely, hedges survival ('cuts both ways'), no standstill. Return/destruction as risk = minor defensible-ask deduction only.
  - **Coverage 3.5/4.** Mandatory ✓✓; residuals ✓, 4th exclusion ✓, non-solicit carve-outs ✓, §2.4 refinement ✓. Missed: damages cap.
  - **Soundness 2.5/3.** Generally correct; mild ownership/control conflation on Derived Information.
  - **Actionability 1.5/2.** Names the 'most commercially dangerous omissions'; do-not-sign verdict.

*Prompt-level signal: A1 discriminated as designed — Directionality spread the field (1.5–2/4), no model performed the bucket split, and the standstill insight went unclaimed by all five. The no-reliance misframe caught four of five models (Qwen excepted).*

  
  

# A2  

Read the Master Services Agreement excerpt below. The agreement contains clauses that are unusually one-sided or commercially problematic. Identify the three most significant problems from the perspective of Customer (Spireline Digital). For each: quote the exact language, explain the risk, and suggest a fix.

 

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

Section 12.02: \[Redacted\] 

  

# Claude Sonnet 4.6 

Here are the three most significant problems from Spireline Digital's perspective, in order of severity.

## **Problem 1: Two-Day Termination Notice — Article VI, Section 6.01**

**Exact language:**

*"Either party may terminate this Agreement with or without cause by providing two (2) days prior written notice (email is acceptable)."*

**The Risk**

This is the most operationally dangerous clause in the agreement. Two calendar days is not a notice period — it is effectively no notice at all. Kelmont can send an email on a Monday morning and be fully within its rights to shut down all services by Wednesday. For a digital services customer like Spireline, this creates catastrophic exposure:

  - Any business processes, campaigns, or infrastructure dependent on Kelmont's services could be severed with no meaningful transition window
  - Spireline cannot realistically identify an alternative vendor, negotiate a replacement contract, migrate data, and restore operations in 48 hours
  - The "email is acceptable" language means there is no friction or formality required — a single message triggers the clock
  - Because the clause is mutual, Spireline also only gets two days' notice, but the harm is asymmetric: the Customer bears the operational dependency, not the vendor

The combination of no-cause termination and a two-day window means Kelmont can exit at any time for any reason — including to serve a competitor — with virtually no consequence.

**Suggested Fix**

Replace with a minimum 30-to-90-day notice period for termination without cause, tiered to the agreement's renewal cycle. Add a transition services obligation requiring Kelmont to continue providing services at current rates for a defined wind-down period (typically 60–90 days) following a termination notice, regardless of which party terminates. For cause termination should include a cure period (typically 30 days) before termination becomes effective.

## **Problem 2: Indemnification Is Grossly Asymmetric — Article XI, Sections 11.01 and 11.03**

**Exact language:**

Section 11.01: *"Service Provider shall defend, indemnify and hold harmless Customer from and against all Losses arising from any third-party Action arising out of Service Provider's negligence or more culpable act or omission; breach of representations or warranties; failure to comply with applicable Law."*

Section 11.03: *"Customer shall defend, indemnify and hold harmless Service Provider from and against all Losses arising from Customer's bodily injury or death; damage to real or tangible personal property."*

**The Risk**

Read side by side, these two provisions reveal a striking imbalance. Kelmont's indemnification obligation to Spireline is substantive and commercially relevant — it covers negligence, warranty breaches, and law violations, which are the actual risks in a digital services relationship. Spireline's reciprocal obligation to Kelmont, however, is limited exclusively to bodily injury, death, and physical property damage — risks that are essentially non-existent in a software/digital services context.

The consequence is that Spireline bears the full risk for the categories that actually matter and are likely to occur in practice:

  - If Kelmont's Ad Engine infringes a third party's intellectual property, that claim almost certainly falls outside Section 11.01's enumerated triggers (it would need to be framed as negligence or a warranty breach to be covered, which is not guaranteed)
  - If Kelmont causes a data breach, regulatory violation, or reputational harm through its services, Spireline may have no indemnification path unless it can specifically fit the claim within "negligence" or "failure to comply with applicable Law"
  - There is no IP indemnification for Spireline — a standard and critical protection in any technology services agreement, ensuring the vendor defends the customer if the vendor's technology is alleged to infringe third-party IP rights

**Suggested Fix**

Section 11.01 should be expanded to explicitly include: (a) infringement of any third-party intellectual property rights by the services or deliverables; (b) data breaches or unauthorized access arising from Kelmont's systems or negligence; and (c) violations of data protection laws. Section 11.03 should be rebalanced to mirror Section 11.01's structure — covering Customer's own negligence, breach of its representations, and failure to comply with law — rather than being confined to inapplicable physical tort scenarios.

## **Problem 3: Section 12.02 Is Redacted — Article XII, Limitation of Liability**

**Exact language:**

*"Section 12.02: \[Redacted\]"*

**The Risk**

This is analytically the most alarming provision in the agreement. Section 12.01 caps both parties' liability by eliminating all indirect, consequential, and punitive damages — a mutual limitation that, while standard, already significantly restricts Spireline's ability to recover for service failures (since most damages from a vendor's breach in a digital context are consequential: lost revenue, lost customers, reputational harm).

Section 12.02 immediately follows, and it is redacted. In a standard MSA structure, Section 12.02 is where the aggregate liability cap lives — the dollar ceiling on each party's total exposure under the agreement. The redaction means Spireline is signing an agreement where:

  - It does not know whether there is any cap on Kelmont's liability
  - It does not know whether there is any cap on its own liability to Kelmont
  - If the cap is very low (e.g., one month's fees), Spireline's practical recovery for a material breach is negligible even for direct damages
  - If the cap is asymmetric — higher for Customer than for Service Provider — Spireline is exposed to outsized liability while its own recovery is double-capped by both 12.01 and 12.02

Signing a contract with a redacted liability provision is not a drafting oversight — it is signing a blank check. Spireline cannot assess its risk profile, obtain appropriate insurance coverage, or make informed business decisions without knowing what this section says.

**Suggested Fix**

Spireline should refuse to execute this agreement until Section 12.02 is restored and reviewed. The market standard for an aggregate cap in a services agreement is total fees paid or payable in the 12 months preceding the claim, applied mutually. If Kelmont insists on a lower cap for its own liability, Spireline should negotiate a carve-out ensuring the cap does not apply to Kelmont's IP indemnification obligations, data breach liability, or gross negligence — categories where the actual harm to Spireline could far exceed a fee-based cap.

  
  

# Gemini 3.1 Flash 

Based on a review of this Master Services Agreement (MSA) excerpt, there are three severe commercial and operational risks for **Spireline Digital (Customer)**.

Here are the three most significant problems, their risks, and how to fix them.

### **1. The 2-Day Termination Notice Chaos (Operational Instability)**

  - **The Exact Language:**
  - *"Either party may terminate this Agreement with or without cause by providing two (2) days prior written notice (email is acceptable)."* (Section 6.01)
  - **The Risk to Spireline:**
  - A two-day notice period for termination "without cause" is incredibly dangerous for a software or marketing services agreement. If Kelmont decides to drop Spireline for a competitor, or if negotiations turn sour, they can abruptly stop all work and pull their services in 48 hours. This leaves Spireline with virtually zero time to transition its projects, download data, or hire a replacement vendor, completely paralyzing Spireline's daily operations.
  - **The Suggested Fix:**
  - Differentiate between termination *with cause* (for material breach) and *without cause* (convenience). Extend the convenience notice timeline to give Spireline a safety net.
      
      - **Revised Phrasing:** *"Either party may terminate this Agreement without cause by providing at least thirty (30) days prior written notice to the other party. Either party may terminate this Agreement for cause immediately upon written notice if the other party materially breaches this Agreement and fails to cure such breach within ten (10) days of receiving written notice thereof."*

### **2. The Overbroad IP Carve-Out (Ownership & Black Box Risk)**

  - **The Exact Language:**
  - *"Service Provider shall provide Customer access and copies of source code and/or object code to all custom revisions to the Customer Image; provided, however, Service Provider shall not provide any source code included in the Service Provider Ad Engine."* (Section 8.02)
  - **The Risk to Spireline:**
  - While Section 8.01 tells Spireline "you own the deliverables," Section 8.02 introduces a massive loophole. If Kelmont embeds their proprietary "Ad Engine" deeply into Spireline’s custom deliverables, Spireline owns a product it cannot actually modify, fix, or host independently because the underlying core source code is a black box withheld by Kelmont. If Spireline ever fires Kelmont, Spireline could be left with useless, unmaintainable code.
  - **The Suggested Fix:**
  - While it is fair for Kelmont to retain ownership of their pre-existing Ad Engine, Spireline *must* secure a perpetual, irrevocable license to use, run, and modify it as embedded within the deliverables.
      
      - **Revised Phrasing:** Add to the end of Section 8.02: *"...provided, however, Service Provider shall not provide any source code included in the Service Provider Ad Engine. Notwithstanding the foregoing, to the extent that any Service Provider proprietary materials or the Ad Engine are embedded in or required to utilize the Deliverables, Service Provider hereby grants Customer a perpetual, worldwide, royalty-free, fully paid-up, non-exclusive, irrevocable license to use, execute, reproduce, and display such proprietary materials solely as integrated into the Deliverables."*

### **3. Mutual Waiver of Consequential Damages (The IP/Data Liability Trap)**

  - **The Exact Language:**
  - *"IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES."* (Section 12.01)
  - **The Risk to Spireline:**
  - An absolute, unqualified waiver of consequential damages heavily favors the Service Provider. In technology and data services, the most severe damages resulting from a vendor's screw-up are almost always "consequential" or "indirect." For example, if Kelmont suffers a data breach that leaks Spireline's customer data, or if they infringe on a third party's intellectual property, Spireline's resulting losses—such as lost profits, regulatory fines, notification costs, and reputational damage—are legally classified as consequential damages. Under this clause, Spireline could not recover a single penny of those costs from Kelmont.
  - **The Suggested Fix:**
  - Carve out critical liabilities from the consequential damages waiver so that both parties are fully protected if something catastrophic happens.
      
      - **Revised Phrasing:** *"IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES; PROVIDED, HOWEVER, THAT THIS LIMITATION SHALL NOT APPLY TO (I) A PARTY'S BREACH OF ITS CONFIDENTIALITY OBLIGATIONS, (II) A PARTY'S INDEMNIFICATION OBLIGATIONS UNDER ARTICLE XI, OR (III) A PARTY'S GROSS NEGLIGENCE OR WILLFUL MISCONDUCT."*

  

# GPT 5.5 

From Spireline Digital's perspective, the three most significant issues are:

## **1. Termination on Two Days' Notice**

### **Problematic Language**

"Either party may terminate this Agreement with or without cause by providing two (2) days prior written notice (email is acceptable)."

### **Why This Is Risky for Customer**

This provision effectively allows Kelmont to walk away from the relationship with almost no warning.

For a services arrangement, two days is rarely enough time for the customer to:

  - Transition services to another vendor.
  - Complete in-progress projects.
  - Recover data, source code, credentials, or work product.
  - Avoid operational disruption.

The risk is particularly severe because the agreement appears to involve software and advertising technology. If Kelmont terminates unexpectedly, Spireline could lose critical support or development resources almost immediately.

The automatic renewal language makes the relationship appear stable, but the two-day termination right largely negates that stability.

### **Suggested Fix**

Require:

  - At least **30–90 days' notice for termination without cause**.
  - Immediate termination only for material breach that remains uncured after a cure period.
  - A transition-assistance obligation during the notice period.

Example:

Either party may terminate without cause upon sixty (60) days' prior written notice. Either party may terminate for material breach if such breach remains uncured for thirty (30) days after written notice.

## **2. Suspension of Services for Minor Payment Delays**

### **Problematic Language**

"Service Provider reserves the right to suspend all Services in the event that Customer fails to pay each invoice within 15 days of receipt."

### **Why This Is Risky for Customer**

This gives Kelmont a powerful self-help remedy with almost no protections for Spireline.

Key concerns:

  - No requirement that the invoice be undisputed.
  - No notice before suspension.
  - No cure period beyond the original payment deadline.
  - Suspension of **all** services, even for a relatively small disputed amount.
  - No obligation to continue providing critical services during a billing dispute.

A common scenario is that an invoice contains an error or disputed charge. Under this clause, Kelmont could still suspend all services after 15 days, potentially disrupting Spireline's business.

### **Suggested Fix**

Add:

  - A dispute right.
  - Additional notice before suspension.
  - A cure period.

Example:

Service Provider may suspend Services only for undisputed amounts that remain unpaid thirty (30) days after written notice of delinquency. Customer shall not be deemed in default with respect to any amount disputed in good faith.

## **3. Intellectual Property Reservation Is Overly Broad and Potentially Overrides Ownership Grant**

### **Problematic Language**

Section 8.01:

"Customer is, and shall be, the sole and exclusive owner of all right, title and interest in and to the Deliverables..."

Section 8.02:

"Notwithstanding the foregoing, the Service Provider Ad Engine contains valuable trade secrets and proprietary information of Service Provider, and all right, title and interest in the Service Provider Ad Engine shall remain with Service Provider."

### **Why This Is Risky for Customer**

At first glance, Section 8.01 gives Spireline complete ownership of deliverables.

However, Section 8.02 begins with:

"Notwithstanding the foregoing..."

which overrides the ownership grant.

The agreement never clearly defines:

  - What constitutes the "Service Provider Ad Engine."
  - Whether the Ad Engine is embedded within deliverables.
  - Whether deliverables can function without it.
  - Whether Customer receives a perpetual license to use it.

As drafted, Kelmont could argue that major portions of the software or deliverables are part of the Ad Engine and therefore remain Kelmont's property.

The result is uncertainty over whether Spireline truly owns and can freely use what it paid for.

### **Suggested Fix**

Preserve Kelmont's ownership of pre-existing technology while guaranteeing Customer's operational rights.

Example:

Service Provider retains ownership of its pre-existing technology, including the Service Provider Ad Engine. To the extent any Deliverable incorporates such technology, Service Provider grants Customer a perpetual, irrevocable, worldwide, royalty-free license to use, execute, modify, maintain, and support such technology as incorporated into the Deliverables.

The agreement should also precisely define "Service Provider Ad Engine" and identify which components are excluded from the assignment.

## **Honorable Mention: Incomplete Limitation of Liability**

Another significant concern is:

"Section 12.02: \[Redacted\]"

The liability cap is missing. If there is no liability cap, Kelmont could face unlimited exposure while simultaneously disclaiming consequential damages. Conversely, if the redacted section contains a very low cap, Spireline's indemnification rights could become largely meaningless.

Because the liability framework is incomplete, it would be one of the first provisions to review in the full agreement. However, based solely on the text provided, the termination, suspension, and intellectual-property provisions present the clearest and most immediate commercial risks to Spireline.

  

# Muse Spark 

  

Here are the three clauses that hurt Spireline Digital the most — each looks mutual on the surface, but the practical burden falls on you as Customer.

  

\---

  

\#\#\# 1. Two-day walk-away termination

  

\*\*Exact language — Section 6.01:\*\*

\> "This Agreement shall commence on the Effective Date and continue for six (6) months, unless sooner terminated. The Agreement automatically renews for successive six-month periods unless terminated by either party. Either party may terminate this Agreement with or without cause by providing two (2) days prior written notice (email is acceptable)."

  

\*\*Why it's a problem for you:\*\*

\- Kelmont can shut off the Ad Engine in the middle of a live campaign with a Friday email. You get no transition period, no data-export obligation, and no wind-down services.

\- The auto-renew creates the impression of stability, but the 2-day right overrides it. Combined with Section 12.01 (which bars consequential damages), you cannot recover lost media spend, missed conversions, or reputational harm if they walk.

\- Email notice is too informal for a business-critical service — a missed spam filter equals termination.

  

\*\*Fix to propose:\*\*

\- Change termination for convenience to 90 days' written notice, and require notice by tracked delivery, not just email.

\- Keep termination for cause with 30 days to cure a material breach.

\- Add a termination-assistance clause: for 30 days after termination, Kelmont must keep services running, provide data exports in industry-standard format, and cooperate in migration at its then-current time-and-materials rates.

  

\---

  

\#\#\# 2. You "own" the Deliverables but can't use them without Kelmont's black box

  

\*\*Exact language — Section 8.02:\*\*

\> "Notwithstanding the foregoing, the Service Provider Ad Engine contains valuable trade secrets and proprietary information of Service Provider, and all right, title and interest in the Service Provider Ad Engine shall remain with Service Provider. Service Provider shall provide Customer access and copies of source code and/or object code to all custom revisions to the Customer Image; provided, however, Service Provider shall not provide any source code included in the Service Provider Ad Engine."

  

\*\*Why it's a problem for you:\*\*

\- Section 8.01 gives you ownership of Deliverables, but 8.02 immediately hollows it out. Anything that touches the Ad Engine — which is likely the core bidding, targeting, and optimization logic — stays with Kelmont, and you get no source code.

\- There is no license grant at all. After the 2-day termination above, you legally own the Deliverables but have no right to run them, because they depend on an engine you cannot access.

\- "custom revisions to the Customer Image" is undefined, and Kelmont only promises object code for engine-related parts. You cannot maintain, audit, or port the work to another vendor. That is classic vendor lock-in.

  

\*\*Fix to propose:\*\*

\- Add a perpetual, irrevocable, royalty-free, non-exclusive license to use, copy, and modify the Ad Engine solely as necessary to operate the Deliverables, including after termination.

\- Narrow the definition of "Ad Engine" to pre-existing, generally available code, and state that any modifications made for Spireline are Deliverables owned by you.

\- Require delivery of full source code for all Deliverables, and place the current Ad Engine source in escrow with release triggers for insolvency, material breach, or termination without cause.

  

\---

  

\#\#\# 3. Indemnity is lopsided and misses the biggest risk — IP infringement

  

\*\*Exact language — Section 11.01:\*\*

\> "Service Provider shall defend, indemnify and hold harmless Customer from and against all Losses arising from any third-party Action arising out of Service Provider's negligence or more culpable act or omission; breach of representations or warranties; failure to comply with applicable Law."

  

\*\*Exact language — Section 11.03:\*\*

\> "Customer shall defend, indemnify and hold harmless Service Provider from and against all Losses arising from Customer's bodily injury or death; damage to real or tangible personal property."

  

\*\*Why it's a problem for you:\*\*

\- Kelmont does NOT indemnify you for intellectual property infringement. For an ad-tech platform, patent troll or copyright claims on the engine are the top risk, and you would be left defending them alone.

\- Your indemnity to Kelmont is oddly broad and mismatched to a digital service. You are on the hook for "bodily injury or death" and "damage to real or tangible personal property" — risks that almost never arise from using software — with no carve-out if Kelmont's negligence caused the harm.

\- The imbalance is amplified by the limitation of liability: you cannot claim lost profits from a shutdown, but you must pay Kelmont's legal bills for physical-world claims.

  

\*\*Fix to propose:\*\*

\- Replace 11.01 with a standard IP indemnity: Kelmont defends and indemnifies Spireline against third-party claims that the Services or Deliverables infringe any US patent, copyright, trademark, or trade secret, with standard carve-outs for your data and modifications not made by Kelmont.

\- Narrow 11.03 to what makes sense for you: Spireline indemnifies Kelmont only for claims arising from (a) Customer Data, (b) your breach of use restrictions, or (c) your gross negligence or willful misconduct causing bodily injury or tangible property damage.

\- Make both indemnities subject to prompt notice, sole control of defense by indemnitor, and no settlement without indemnitee consent.

  
  

# Qwen 3.7 Plus

  

Based on the provided excerpt, here are the three most significant problems in the Master Services Agreement from the perspective of the Customer (Spireline Digital), along with the exact language, the associated risks, and suggested fixes.

  

\#\#\# 1. Unreasonably Short Termination for Convenience Notice

\*\*Quote:\*\* 

\> "Either party may terminate this Agreement with or without cause by providing two (2) days prior written notice (email is acceptable)." \*(Section 6.01)\*

  

\*\*Risk:\*\* 

A 48-hour termination window creates extreme operational instability and renders the "six-month" initial term and auto-renewal provisions entirely illusory. Spireline cannot rely on the service for any meaningful business continuity, campaign execution, or transition planning. Kelmont can pull the plug at any moment for any reason, leaving Spireline stranded without a viable alternative or time to migrate to a new vendor. 

  

\*\*Fix:\*\* 

Extend the termination for convenience notice period to a commercially reasonable timeframe (e.g., 30, 60, or 90 days). Alternatively, remove the right to terminate for convenience entirely and limit termination to material breach subject to a 30-day cure period.

  

\---

  

\#\#\# 2. Draconian, Unilateral Suspension Rights Without Notice or Dispute Resolution

\*\*Quote:\*\* 

\> "Service Provider reserves the right to suspend all Services in the event that Customer fails to pay each invoice within 15 days of receipt." \*(Section 7.05)\*

  

\*\*Risk:\*\* 

This allows Kelmont to shut down Spireline's entire operation with zero prior notice and zero opportunity to cure, simply because an invoice is 15 days old. It also fails to account for good-faith billing disputes; a minor disagreement over a single line item could trigger a total service blackout. Furthermore, 15 days is an unusually short payment term for enterprise services (standard is Net 30).

  

\*\*Fix:\*\* 

Change the payment term to Net 30 days. Require Kelmont to provide written notice of the failure to pay and grant Spireline a cure period (e.g., 10 days) before any suspension can occur. Add a carve-out explicitly prohibiting suspension for any amounts that are disputed in good faith by the Customer.

  

\---

  

\#\#\# 3. Vendor Lock-In and Lack of Perpetual Rights to Underlying Technology

\*\*Quote:\*\* 

\> "Service Provider shall provide Customer access and copies of source code and/or object code to all custom revisions to the Customer Image; provided, however, Service Provider shall not provide any source code included in the Service Provider Ad Engine." \*(Section 8.02)\*

  

\*\*Risk:\*\* 

Spireline is paying for custom Deliverables but is denied the source code for the underlying "Ad Engine" required to run them. This creates severe vendor lock-in. If the contract ends, Spireline owns the custom revisions but cannot maintain, modify, or run them independently. Additionally, the clause only grants "access and copies," not a perpetual license to the Ad Engine itself, meaning Kelmont could revoke access post-termination, rendering Spireline's owned Deliverables useless.

  

\*\*Fix:\*\* 

Grant Spireline a perpetual, irrevocable, royalty-free, non-exclusive license to use the Service Provider Ad Engine solely to the extent necessary to run, maintain, and utilize the custom Deliverables. Alternatively, require Kelmont to place the Ad Engine source code in a third-party technology escrow account, with release to Spireline triggered by the termination of the MSA or Kelmont's insolvency.

  
  
  

# A2 grading  

**LegalEval v6 — A2 Grading**

Problematic-Clause ID (MSA) · /16 · Gates: Faithfulness + Directionality

|  |
| :-: |
| \*\*GRADING NOTE\*\*  Scores produced by an Anthropic Claude-family grader; Claude Sonnet 4.6 is among the models under test. Procedure per v6 §6.2: score dimensions → raw total → normalize to prompt max → cap at 0.40 on any gate trip. Run date June 9, 2026. |

**Task:** Problematic-Clause ID, Kelmont/Spireline MSA. Max /16. Gates: Faithfulness + Directionality. Required targets: §6.01 (2-day termination), §7.05 (15-day payment + suspension), §8.01/8.02 (undefined Ad Engine carve-out). Secondaries: IP-infringement indemnity gap; §12.01 asymmetry. Faithfulness trips on inventing a §12.02 cap figure; deduction for speculating on the redacted section's contents.

*Coverage operationalized as 1 pt per target + up to 1 pt secondary (per the GRADER INSTRUCTIONS wording 'all required' + partial credit). The design table's '0 pts if any missing' floor conflicts with its own secondary-credit clause — under the strict floor, Claude falls to 12/16 and Gemini/Muse to 13/16; Qwen and GPT unaffected. Flagged for a v6.1 wording fix.*

|  |  |  |  |  |  |  |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| \*\*Model\*\* | \*\*Faith /3\*\* | \*\*Dir /4\*\* | \*\*Cov /4\*\* | \*\*Snd /3\*\* | \*\*Act /2\*\* | \*\*Raw → Norm\*\* |
| \*\*Claude Sonnet 4.6\*\* | 2 | 4 | 2 | 3 | 2 | 13 → 0.81 |
| \*\*Gemini 3.1 Flash\*\* | 3 | 4 | 3 | 3 | 2 | 15 → 0.94 |
| \*\*GPT 5.5\*\* | 2 | 4 | 3 | 3 | 2 | 14 → 0.88 |
| \*\*Muse Spark\*\* | 3 | 4 | 3 | 3 | 2 | 15 → 0.94 |
| \*\*Qwen 3.7 Plus\*\* | 3 | 4 | 3 | 3 | 2 | 15 → 0.94 |

**Claude Sonnet 4.6 — 13/16 (0.81)**

  - **Targets 1/3** (§6.01 only). §7.05 absent; §8.02 reduced to a passing mention. Secondaries: IP-infringement indemnity ✓ and consequential-damages asymmetry ✓ → Coverage 2/4.
  - **Faithfulness 2/3.** 'Section 12.02 is where the aggregate liability cap lives' — speculation on the redacted section's likely contents (the explicit v2-fix deduction). No figure invented; correctly states it cannot be assessed → deduction, no gate.
  - **Dir 4/4 · Snd 3/3 · Act 2/2.** §11.03 read correctly as Customer's obligation; refuse-to-execute advice on §12.02 sound; quote→risk→fix throughout.

**Gemini 3.1 Flash — 15/16 (0.94)**

  - **Targets 2/3** (§6.01 ✓; §8.02 ✓ with the strongest embedded-black-box analysis of the run). §7.05 missed. Secondary: §12.01 asymmetry ✓ → Coverage 3/4.
  - **Faithfulness 3/3.** Never mentions §12.02 — no restraint credit but no speculation. Fixes are full drafted replacement language.

**GPT 5.5 — 14/16 (0.88)**

  - **Targets 3/3** — all required issues as its three problems (with Qwen, the only model to do so). No listed secondary → Coverage 3/4.
  - **Faithfulness 2/3.** Honorable-mention §12.02 opens 'The liability cap is missing' — asserting the redacted section's contents before hedging properly. Same contents-speculation deduction as Claude; no figure, no gate.
  - **Snd 3/3 · Act 2/2.** Undisputed-amounts + notice + cure fix on §7.05 is textbook; example clause language supplied.

**Muse Spark — 15/16 (0.94)**

  - **Targets 2/3** (§6.01 ✓ with the §12.01 interplay insight — 'you cannot recover lost media spend… if they walk'; §8.02 ✓ with escrow + narrowed-definition fix). §7.05 missed. Secondary: IP-infringement indemnity ✓ → Coverage 3/4.
  - **Faithfulness 3/3.** §12.02 not mentioned; 'likely the core bidding… logic' properly hedged. Correctly spots that §8.02 contains no license grant at all.

**Qwen 3.7 Plus — 15/16 (0.94)**

  - **Targets 3/3** — all required issues, cleanly. No secondaries → Coverage 3/4.
  - **Faithfulness 3/3 · Snd 3/3 · Act 2/2.** 'Renders the six-month term entirely illusory'; Net-30 + cure + good-faith-dispute carve-out on §7.05; perpetual license or escrow on §8.02.

*Prompt-level signal: §7.05 is the most-missed required issue (Claude, Muse). The §12.02 hallucination-restraint check worked — no model invented a figure, but Claude and GPT both asserted the section 'is' the cap (−1 Faithfulness each).*

  
  

# A3  

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

  

# Claude Sonnet 4.6 

Here is a provision-by-provision comparison, followed by an overall assessment.

## **1. Notice Period for Termination Without Cause**

**Version A:** Two (2) days written notice, email acceptable, no-cause termination by either party.

**Version B:** Ninety (90) days written notice required for no-cause termination.

**Assessment: Version A is severely unfavorable; Version B is favorable.**

This is the most consequential difference in the comparison. As discussed previously, a two-day notice period is operationally indistinguishable from no notice at all. The vendor can send an email Monday and be contractually free by Wednesday. Ninety days is a commercially reasonable window — it gives Customer time to identify an alternative vendor, negotiate a replacement agreement, migrate data and workflows, and maintain business continuity. The difference between these two provisions is the difference between a manageable transition and an emergency.

## **2. Termination for Cause — Cure Period**

**Version A:** No for-cause termination mechanism exists. The only termination right is no-cause with two days' notice, meaning the parties are not even distinguished by fault.

**Version B:** Either party may terminate for cause with 30 days' notice, but only if the breaching party fails to cure within that 30-day window.

**Assessment: Version A is unfavorable; Version B is favorable.**

Version A's absence of a for-cause framework creates two problems for Customer. First, there is no incentive structure — Vendor faces identical consequences whether it performs perfectly or breaches materially, since the exit mechanism is the same either way. Second, Customer has no contractual leverage to demand cure before termination; it must either terminate (and lose the service) or do nothing. Version B's cure-period mechanism is favorable to Customer in both directions: it gives a breaching Vendor the opportunity to fix problems before Customer loses the service, while also giving Customer a clean, documented path to exit if Vendor fails to remedy a material breach.

## **3. Data Return Upon Termination**

**Version A:** No provision. Silent on what happens to Customer's data when the agreement ends.

**Version B:** Service Provider must deliver a complete copy of all Customer Data within 15 business days of termination.

**Assessment: Version A is unfavorable; Version B is strongly favorable.**

Version A's silence on data return is a serious gap. Without an express obligation, Customer must negotiate or litigate to recover its own data after termination — at exactly the moment when the relationship has broken down and Vendor has the least incentive to cooperate. Version B's provision is well-drafted: it is time-bound (15 business days), comprehensive ("complete copy"), and automatic (triggered by "any termination" without requiring Customer to make a separate demand). For a digital services customer whose data may be the most valuable asset in the relationship, this provision is essential.

## **4. Survival of Key Provisions**

**Version A:** No survival clause. Silent on which obligations persist after termination.

**Version B:** Explicitly preserves IP (Section 8), Confidentiality (Section 9), Limitation of Liability (Section 10), and Governing Law (Section 12) post-termination.

**Assessment: Version A is unfavorable; Version B is favorable.**

Without a survival clause, the enforceability of critical protections after termination becomes a legal question rather than a contractual certainty. Version A leaves open whether confidentiality obligations survive (a significant exposure if either party received sensitive information), whether IP ownership is preserved (critical for Customer's deliverables), and whether the liability cap continues to apply to post-termination disputes. Version B eliminates all of this ambiguity. The explicit survival of the limitation of liability provision is particularly notable — without it, a party could argue that post-termination claims are not subject to the agreed cap.

## **5. Automatic Renewal Structure**

**Version A:** Automatically renews for successive six-month periods unless terminated, with a two-day exit window at any point.

**Version B:** No automatic renewal is specified. The agreement continues until terminated under Sections 11.1 or 11.2.

**Assessment: Mixed, with Version A slightly unfavorable.**

Version A's automatic renewal is not inherently problematic — it is common in services agreements. However, paired with a two-day termination window, the renewal structure creates false comfort: the six-month periods imply a medium-term commitment, but the two-day exit clause means neither party is actually committed to anything. From Customer's perspective, this is worse than it appears because it may deter Customer from investing in integration or onboarding while not actually providing any meaningful service continuity. Version B's open-ended structure, combined with a 90-day exit right, gives Customer genuine planning certainty.

## **6. Form of Notice**

**Version A:** Email explicitly stated as acceptable.

**Version B:** "Written notice" required; form not specified.

**Assessment: Version A is marginally favorable on this narrow point.**

Explicit acceptance of email notice reduces friction and is practically modern. Version B's silence on acceptable notice form is a minor gap — in practice, most courts treat email as written notice, but the ambiguity could allow a party to argue that email termination was ineffective, which in a 90-day notice context is less dangerous but still worth specifying.

## **Overall Assessment**

|  |  |  |
| :-: | :-: | :-: |
| \*\*Provision\*\* | \*\*Version A\*\* | \*\*Version B\*\* |
| No-cause notice period | ❌ 2 days | ✅ 90 days |
| For-cause termination with cure | ❌ Absent | ✅ Present |
| Data return obligation | ❌ Absent | ✅ 15 business days |
| Survival clause | ❌ Absent | ✅ Explicit |
| Renewal structure | ⚠️ Auto-renews / illusory | ✅ Open-ended with real notice |
| Notice form | ✅ Email accepted | ⚠️ Unspecified |

**Version B is materially superior for Customer in every substantively important respect.** Version A is not merely weak — it is structured in a way that creates the appearance of a contractual relationship while stripping away the protections that make a services agreement valuable: transition time, data recovery, preserved obligations, and meaningful leverage over a breaching vendor. The only minor point in Version A's favor (explicit email notice) is trivially negotiable and does not begin to offset its deficiencies.

If Customer is evaluating which agreement to sign, Version B is the clear choice. If Customer is currently bound by Version A, the immediate priorities should be negotiating an extended notice period and adding a data return obligation — the two gaps with the most acute operational consequences.

  

# Gemini 3.1 Flash 

When you compare these two clauses from the perspective of the Customer (the service recipient), **Version B is vastly superior and far safer.**

Version A is a barebones, high-risk clause that exposes your operations to sudden disruption. Version B is a structured, commercial-grade clause designed to protect business continuity and data security.

Here is the breakdown of every material difference and how they impact you.

### **Material Differences & Customer Impact**

|  |  |  |  |
| :-: | :-: | :-: | :-: |
| \*\*Feature / Dimension\*\* | \*\*Version A\*\* | \*\*Version B\*\* | \*\*Impact on Customer\*\* |
| \*\*Termination Without Cause (Convenience)\*\* | \*\*2 days\*\* notice via email. | \*\*90 days\*\* written notice. | \*\*Version B is Highly Favorable.\*\* 2 days notice means the vendor can walk away and shut off your service virtually overnight, leaving you no time to find a replacement. 90 days ensures business continuity. |
| \*\*Termination for Cause & Cure Rights\*\* | Conflated with convenience; \*\*2 days\*\* notice, no cure period mentioned. | \*\*30 days\*\* notice for material breach, with a \*\*30-day window to fix (cure)\*\* the breach. | \*\*Version B is Favorable.\*\* While Version A lets you fire a bad vendor quickly, it also lets them fire \*you\* instantly over a minor dispute. Version B provides predictable guardrails to fix technical or service issues before pulling the plug. |
| \*\*Customer Data Exit Strategy\*\* | \*\*Completely silent.\*\* | Mandates vendor return a complete copy of data within \*\*15 business days\*\*. | \*\*Version B is Massively Favorable.\*\* Without Section 11.3, a disgruntled vendor could hold your data hostage when the relationship ends or demand exorbitant "extraction fees" to give it back. |
| \*\*Survival of Critical Terms\*\* | \*\*Completely silent.\*\* | Explicitly states that \*\*IP, Confidentiality, Liability, and Governing Law survive\*\* termination. | \*\*Version B is Highly Favorable.\*\* Without a survival clause, a vendor could argue that their obligation to keep your company secrets wraps up the moment the contract ends. Section 11.4 legally locks those protections in perpetuity. |

  

### **Key Takeaway: Why the Differences Matter**

#### **1. The Operational Abandonment Risk (Section 6.01 vs. Section 11.2)**

In Version A, the 2-day termination right applies to both "with or without cause." If the Service Provider suddenly hooks a massive new client and runs out of bandwidth, they can send you a brief email on Thursday night and legally stop servicing you by Saturday. Finding, onboarding, and migrating to a new vendor takes weeks, if not months. Version B’s 90-day cushion gives your team a realistic window to transition smoothly.

#### **2. The Data Hostage Trap (Section 11.3)**

If a contract ends poorly under Version A, you have zero contractual leverage to force the vendor to hand over your databases, user logs, or system history. Version B turns the return of your data into a strict, timed legal obligation for the vendor.

#### **3. Erasing Legal Protections (Section 11.4)**

Contracts don't just dictate how you work together; they dictate how you handle fallout after you split up. Because Version A lacks a survival clause, core protections regarding who owns the intellectual property or who is liable for past mistakes become incredibly muddy the moment the agreement terminates. Version B ensures that even if the operational relationship ends, the legal shields stay up.

  
  

### **Overall Assessment**

**Do not sign Version A.** It functions as an unmitigated operational hazard for a service recipient.

**Version B is the standard you want.** It acknowledges that transitioning away from a service provider takes time, requires data mobility, and demands that legal protections (like confidentiality) outlive the operational run of the contract. The only minor negotiation point in Version B is ensuring that 90 days isn't *too* restrictive if *you* are the one who wants to pivot away from them quickly—but as a shield against vendor abandonment, it is exactly what you need.

  

# GPT 5.5 

## **Executive Summary**

**Version B is substantially more favorable to the Customer than Version A.**

Version A gives both parties the ability to terminate almost immediately (2 days' notice) and contains no transition, data-return, cure, or survival provisions. While the flexibility may benefit the Customer if it wants to exit quickly, the greater practical risk is that the Service Provider can abruptly terminate services.

Version B provides a much more typical commercial framework: cure rights, meaningful notice periods, data-return obligations, and survival provisions. These protections significantly reduce the Customer's operational and legal risk.

# **Material Differences**

|  |  |  |  |
| :-: | :-: | :-: | :-: |
| \*\*Issue\*\* | \*\*Version A\*\* | \*\*Version B\*\* | \*\*Impact on Customer\*\* |
| Termination without cause | Either party may terminate on \*\*2 days' notice\*\* | Either party may terminate on \*\*90 days' notice\*\* | \*\*Favorable to Customer (Version B)\*\* |
| Termination for breach | No breach-specific termination mechanism | Material breach + \*\*30-day cure period\*\* | \*\*Favorable to Customer (Version B)\*\* |
| Cure rights | None | Breaching party gets 30 days to cure | \*\*Generally favorable to Customer (Version B)\*\* |
| Service continuity | Potential loss of services after 2 days | At least 90 days before no-cause termination becomes effective | \*\*Favorable to Customer (Version B)\*\* |
| Customer data return | Silent | Provider must return Customer Data within 15 business days | \*\*Strongly favorable to Customer (Version B)\*\* |
| Survival of key provisions | Silent | IP, confidentiality, liability, governing law survive | \*\*Favorable to Customer (Version B)\*\* |
| Contract duration | Initial 6-month term with automatic renewals | Not addressed in excerpt | Neutral/unclear |
| Customer exit flexibility | Very high (2-day exit right) | Reduced (90-day notice required) | \*\*Slightly unfavorable to Customer in Version B\*\* |

# **Detailed Analysis**

## **1. Notice Period for Termination Without Cause**

### **Version A**

"Either party may terminate this Agreement with or without cause by providing two (2) days prior written notice."

### **Version B**

"Either party may terminate this Agreement without cause upon ninety (90) days written notice."

### **Customer Impact**

This is the single biggest difference.

Under Version A, the Service Provider can effectively abandon the relationship on two days' notice. For most service arrangements, that is commercially dangerous because the Customer may:

  - Lose critical services unexpectedly.
  - Have insufficient time to find a replacement vendor.
  - Experience business disruption.
  - Lose support for active projects.

Version B provides a substantial transition window.

### **Assessment**

**Version B is strongly favorable to Customer.**

The only downside is reduced flexibility if the Customer wants to leave immediately, but Customers are usually more concerned about service continuity than rapid exit rights.

## **2. Termination for Cause and Cure Rights**

### **Version A**

No dedicated breach termination provision.

### **Version B**

"Either party may terminate ... if the other party materially breaches this Agreement and fails to cure such breach within the thirty (30) day notice period."

### **Customer Impact**

Version B creates a structured process:

1.  Material breach occurs.
2.  Written notice is provided.
3.  Breaching party gets 30 days to fix the problem.
4.  Termination occurs only if the breach remains uncured.

This protects Customer in two ways:

  - Prevents Service Provider from terminating immediately over minor disputes.
  - Gives Customer time to fix accidental noncompliance.

### **Assessment**

**Version B is favorable to Customer.**

## **3. Data Return Obligation**

### **Version A**

No provision.

### **Version B**

"Upon any termination, Service Provider shall provide Customer with a complete copy of all Customer Data within fifteen (15) business days."

### **Customer Impact**

This is an important protection.

Without it, Customer may face disputes regarding:

  - Access to business records.
  - Migration to a replacement provider.
  - Historical data recovery.
  - Operational continuity.

In Version A, there is no express obligation for the Service Provider to return Customer data.

### **Assessment**

**Strongly favorable to Customer.**

This is one of the most valuable protections added by Version B.

## **4. Survival of Key Obligations**

### **Version A**

Silent.

### **Version B**

"Sections 8 (IP), 9 (Confidentiality), 10 (Limitation of Liability), and 12 (Governing Law) shall survive termination."

### **Customer Impact**

Without a survival clause, parties may argue over whether important obligations continue after termination.

Version B confirms that:

  - Customer retains IP protections.
  - Confidential information remains protected.
  - Liability rules continue to govern post-termination disputes.
  - Governing law remains applicable.

### **Assessment**

**Favorable to Customer.**

It reduces litigation uncertainty. 

## **5. Contract Structure**

### **Version A**

"continue for six (6) months"

"automatically renews for successive six-month periods"

### **Version B**

No term language included in the excerpt.

### **Customer Impact**

Version A creates recurring six-month terms, but because either party can terminate on two days' notice, the six-month structure has limited practical value.

Version B's excerpt does not specify term length, so no direct comparison can be made.

### **Assessment**

**Neutral based on available text.**

# **Overall Assessment**

### **Version A**

Customer risks:

  - Abrupt loss of services.
  - No transition assistance.
  - No data-return obligation.
  - No cure period.
  - No survival clause.
  - Minimal predictability.

The clause is heavily weighted toward flexibility at the expense of stability.

### **Version B**

Customer protections:

  - 90-day transition period.
  - Cure rights before termination for breach.
  - Guaranteed return of Customer data.
  - Explicit survival of critical contractual protections.
  - Greater operational predictability.

The only meaningful advantage of Version A for Customer is the ability to exit quickly on two days' notice. In most commercial service relationships, that benefit is outweighed by the risk that the Service Provider can do the same.

## **Conclusion**

**Version B is materially more Customer-friendly and commercially balanced.** It significantly reduces the Customer's operational risk and better protects Customer assets and rights upon termination. The addition of a 90-day notice period, cure rights, data-return obligations, and survival provisions makes Version B substantially preferable from the Customer's perspective.

  

# Muse Spark 

Here is the head-to-head from the Customer side — the party that needs the service to stay up and needs its data back.

  

\#\#\# Version A (6.01)

\- 6-month initial term, then auto-renews every 6 months

\- Either side can quit for any reason, or no reason, with 2 days written notice. Email counts.

  

\#\#\# Version B (11.1–11.4)

\- No fixed term stated

\- For cause: 30 days written notice, but only if the other side materially breaches and fails to cure in those 30 days

\- Without cause: 90 days written notice

\- Provider must return a complete copy of all Customer Data within 15 business days after any termination

\- IP, Confidentiality, Limitation of Liability, and Governing Law survive

  

\---

  

\#\# Material differences, Customer impact

  

\*\*1. How fast you can walk away without cause\*\*

\- A: 2 days. B: 90 days.

\- \*\*Favorable to Customer in A\*\* — you can switch vendors almost instantly, no penalty.

\- Trade-off: the same 2 days applies to the Provider, see \#2.

  

\*\*2. How fast the Provider can walk away without cause\*\*

\- A: 2 days. B: 90 days.

\- \*\*Unfavorable to Customer in A, favorable in B\*\* — with 2 days you get no time to migrate, retrain staff, or find a replacement. 90 days gives a real transition window. For most Customers, this risk outweighs the benefit in \#1.

  

\*\*3. Termination for cause standards\*\*

\- A: no distinction between cause and convenience, no materiality test, no cure period. 2 days notice is enough.

\- B: must be a material breach, and the breaching party gets 30 days to cure.

\- \*\*If you are terminating the Provider:\*\* A is favorable (faster, easier).

\- \*\*If Provider is terminating you:\*\* B is favorable — you cannot be cut off for a trivial breach, and you get 30 days to fix it. A leaves you exposed to a 2-day shutdown for any alleged breach.

  

\*\*4. Data return on exit\*\*

\- A: silent.

\- B: Provider must deliver a complete copy of all Customer Data within 15 business days.

\- \*\*Favorable to Customer in B, unfavorable in A.\*\* Without this, you risk losing access, paying a ransom, or rebuilding from scratch.

  

\*\*5. Survival of key terms\*\*

\- A: silent — survival left to common law and whatever is in other sections.

\- B: expressly keeps Confidentiality alive (Provider must keep protecting your data), and also keeps Limitation of Liability alive (caps Provider's exposure post-termination), plus IP and Governing Law.

\- \*\*Confidentiality survival: favorable in B.\*\* You get a clear ongoing duty.

\- \*\*Limitation of Liability survival: unfavorable in B\*\* — it preserves the Provider's cap on damages, which limits your recovery. Most Customers accept this trade because certainty is better than silence, but it is a concession.

\- Overall, B gives predictability; A creates ambiguity.

  

\*\*6. Form of notice\*\*

\- A: email expressly acceptable.

\- B: "written notice" only, no medium specified.

\- \*\*Favorable to Customer in A\*\* for speed and proof, though the practical benefit is small compared to the termination risks.

  

\*\*7. Term structure\*\*

\- A: fixed 6-month term with automatic 6-month renewals.

\- B: evergreen until terminated.

\- \*\*Slightly favorable in B.\*\* With a 2-day exit right, the 6-month clock in A does not lock you in, but it adds administrative tracking. B is simpler.

  

\---

  

\#\# Overall assessment for the Customer

  

Version A looks attractive because you can leave in 2 days, but that same 2 days is the Provider's weapon. From a Customer perspective, service continuity and data security usually matter more than the ability to quit on a whim.

  

Version B is the more Customer-protective structure, even though it slows you down:

  

\- You lose the 2-day exit, but you gain a 90-day notice before the Provider can leave you stranded.

\- You lose the ability to terminate instantly for cause, but you gain a 30-day cure period that protects you from being terminated for minor issues.

\- Most importantly, you get a contractual right to your data back in 15 business days, which Version A does not give you at all.

\- You also get clear post-termination confidentiality.

  

\*\*Bottom line:\*\* Take B if you depend on the service. The only scenario where A is better is if you are testing a non-critical, easily replaceable tool and you value the option to pull the plug in 48 hours more than you fear the Provider doing the same to you. For a typical master services agreement, the stability, cure rights, and data-return obligation in Version B outweigh the speed advantage in Version A.

  

# Qwen 3.7 Plus

Based on a comparison of the two excerpts, here are the material differences from the perspective of the Customer, along with an assessment of each and an overall conclusion.

  

\#\#\# 1. Notice Period for Termination Without Cause (Convenience)

\*   \*\*Version A:\*\* Allows either party to terminate with or without cause by providing just \*\*two (2) days\*\* prior written notice.

\*   \*\*Version B:\*\* Allows either party to terminate without cause upon \*\*ninety (90) days\*\* written notice.

\*   \*\*Impact on Customer:\*\* \*\*Highly Unfavorable (A) / Favorable (B).\*\* Two days is commercially unreasonable and creates catastrophic operational risk. It allows the Service Provider to pull the plug almost instantly, leaving the Customer with zero time to transition to a new vendor, migrate systems, or maintain business continuity. Ninety days provides a reasonable, standard runway for the Customer to secure alternative services and execute a transition plan. 

  

\#\#\# 2. Termination for Cause and Cure Rights

\*   \*\*Version A:\*\* Lumps "with or without cause" into the same 2-day notice bucket. There is no requirement for a material breach and no cure period.

\*   \*\*Version B:\*\* Requires a \*\*material breach\*\*, \*\*thirty (30) days\*\* written notice, and a \*\*thirty (30) day cure period\*\* before termination is effective.

\*   \*\*Impact on Customer:\*\* \*\*Unfavorable (A) / Favorable (B).\*\* Under Version A, the Provider could terminate the contract over a minor, easily fixable issue (or no reason at all) in 48 hours. Version B protects the Customer by ensuring that if the Provider breaches, the Customer can force them to fix the issue (cure) rather than just walking away. It also gives the Customer a 30-day safety net to correct their own accidental breaches before the contract is killed.

  

\#\#\# 3. Post-Termination Transition and Return of Data

\*   \*\*Version A:\*\* Completely silent on what happens to the Customer's data upon termination.

\*   \*\*Version B:\*\* Explicitly requires the Service Provider to provide a complete copy of all Customer Data within \*\*fifteen (15) business days\*\* of termination.

\*   \*\*Impact on Customer:\*\* \*\*Highly Unfavorable (A) / Highly Favorable (B).\*\* In Version A, upon termination, the Provider could legally delete, hold hostage, or refuse to return the Customer's data, causing massive operational disruption and potential data loss. Version B guarantees the Customer gets their data back in a timely manner, which is critical for business continuity and mitigates vendor lock-in.

  

\#\#\# 4. Survival of Key Provisions

\*   \*\*Version A:\*\* Silent on which obligations continue after the agreement ends.

\*   \*\*Version B:\*\* Explicitly states that \*\*IP, Confidentiality, Limitation of Liability, and Governing Law\*\* survive termination.

\*   \*\*Impact on Customer:\*\* \*\*Unfavorable (A) / Favorable (B).\*\* Without a survival clause (Version A), there is legal ambiguity about whether the Provider must keep the Customer's information confidential after the contract ends, or who owns the intellectual property created during the term. Version B provides certainty that the Customer's IP and trade secrets remain protected post-termination, and that the liability cap continues to apply to any post-termination disputes.

  

\---

  

\#\#\# Overall Assessment

  

\*\*Version B is vastly superior for the Customer.\*\* 

  

Version A is a "hair-trigger" agreement that is highly defective and dangerous for the Customer. By allowing 48-hour termination for any reason, it completely undermines any commitment to a 6-month term. It heavily favors the Service Provider by allowing them to terminate the relationship instantly, with no obligation to return data, no cure period for minor issues, and no clear post-termination protections for the Customer's intellectual property or confidentiality. 

  

Version B introduces standard, commercially reasonable guardrails. It provides adequate transition time (90 days), cure rights for breaches, mandatory data return, and clear post-termination protections. A Customer should absolutely reject Version A and insist on language similar to Version B.

  
  

# B1  

Read the definitions section below. Extract every formally defined term and produce a two-column glossary: Term (exactly as defined) | Definition (verbatim, not paraphrased). Do not include terms that are used but not formally defined in this section.

 

MASTER SERVICES AGREEMENT — ARTICLE I DEFINITIONS

Kubient, Inc. / Sphere Digital — Effective June 1, 2018

 

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

# Claude Sonnet 4.6 

  

|  |  |
| :-: | :-: |
| \*\*Term\*\* | \*\*Definition\*\* |
| "Action" | Has the meaning set forth in Section 11.01. |
| "Affiliate" | Any other Person that directly or indirectly, through one or more intermediaries, controls, is controlled by, or is under common control with, such Person. |
| "Control" | The possession, directly or indirectly, of the power to direct or cause the direction of the management and policies of a Person, whether through ownership of voting securities, by contract or otherwise. |
| "Agreement" | Has the meaning set forth in the preamble. |
| "Change Order" | Has the meaning set forth in Section 5.02. |
| "Confidential Information" | Any information that is treated as confidential or proprietary by a party, including trade secrets, technology, information pertaining to business operations and strategies, and information pertaining to customers, pricing, and marketing. Confidential Information shall not include information that: (a) is already known to the Receiving Party without restriction; (b) is or becomes generally known by the public other than by breach of this Agreement; (c) is developed by the Receiving Party independently; or (d) is received from a third party not under any obligation to maintain confidentiality. |
| "Customer" | Has the meaning set forth in the preamble. |
| "Customer Contract Manager" | Has the meaning set forth in Section 4.01(a). |
| "Customer Equipment" | Any equipment, systems, cabling or facilities provided by Customer and used directly or indirectly in the provision of the Services. |
| "Customer Materials" | Any documents, data, know-how, methodologies, software and other materials provided to Service Provider by Customer, including computer programs, reports and specifications. |
| "Deliverables" | All documents, work product and other materials delivered to Customer or prepared by Service Provider in the course of performing the Services, including any items identified as such on Exhibit A. |
| "Disclosing Party" | A party that discloses Confidential Information under this Agreement. |
| "Force Majeure Event" | Has the meaning set forth in Section 15.01. |
| "Intellectual Property Rights" | All (a) patents, patent disclosures and inventions (whether patentable or not); (b) trademarks, service marks, trade dress, trade names, logos, corporate names and domain names; (c) copyrights and copyrightable works, and rights in data and databases; (d) trade secrets, know-how and other confidential information; and (e) all other intellectual property rights. |
| "Law" | Any statute, law, ordinance, regulation, rule, code, order, constitution, treaty, common law, judgment, decree, or other requirement or rule of law of any federal, state, local or foreign government or political subdivision. |
| "Losses" | All losses, damages, liabilities, deficiencies, actions, judgments, interest, awards, penalties, fines, costs or expenses of whatever kind that are actually incurred, including reasonable attorneys' fees and the cost of enforcing any right to indemnification. |
| "Permitted Subcontractor" | Has the meaning set forth in Section 3.01(h). |
| "Person" | An individual, corporation, partnership, joint venture, limited liability company, governmental authority, unincorporated organization, trust, association or other entity. |
| "Receiving Party" | A party that receives or acquires Confidential Information. |
| "Services" | Any professional or other services to be provided by Service Provider under this Agreement, as described in more detail on Exhibit A. |
| "Term" | Has the meaning set forth in Article VI. |

  

# Gemini 3.1 Flash 

  

|  |  |
| :-: | :-: |
| \*\*Term\*\* | \*\*Definition (Verbatim)\*\* |
| \*\*Action\*\* | has the meaning set forth in Section 11.01. |
| \*\*Affiliate\*\* | of a Person means any other Person that directly or indirectly, through one or more intermediaries, controls, is controlled by, or is under common control with, such Person. |
| \*\*Control\*\* | means the possession, directly or indirectly, of the power to direct or cause the direction of the management and policies of a Person, whether through ownership of voting securities, by contract or otherwise. |
| \*\*Agreement\*\* | has the meaning set forth in the preamble. |
| \*\*Change Order\*\* | has the meaning set forth in Section 5.02. |
| \*\*Confidential Information\*\* | means any information that is treated as confidential or proprietary by a party, including trade secrets, technology, information pertaining to business operations and strategies, and information pertaining to customers, pricing, and marketing. Confidential Information shall not include information that: (a) is already known to the Receiving Party without restriction; (b) is or becomes generally known by the public other than by breach of this Agreement; (c) is developed by the Receiving Party independently; or (d) is received from a third party not under any obligation to maintain confidentiality. |
| \*\*Customer\*\* | has the meaning set forth in the preamble. |
| \*\*Customer Contract Manager\*\* | has the meaning set forth in Section 4.01(a). |
| \*\*Customer Equipment\*\* | means any equipment, systems, cabling or facilities provided by Customer and used directly or indirectly in the provision of the Services. |
| \*\*Customer Materials\*\* | means any documents, data, know-how, methodologies, software and other materials provided to Service Provider by Customer, including computer programs, reports and specifications. |
| \*\*Deliverables\*\* | means all documents, work product and other materials delivered to Customer or prepared by Service Provider in the course of performing the Services, including any items identified as such on Exhibit A. |
| \*\*Disclosing Party\*\* | means a party that discloses Confidential Information under this Agreement. |
| \*\*Force Majeure Event\*\* | has the meaning set forth in Section 15.01. |
| \*\*Intellectual Property Rights\*\* | means all (a) patents, patent disclosures and inventions (whether patentable or not); (b) trademarks, service marks, trade dress, trade names, logos, corporate names and domain names; (c) copyrights and copyrightable works, and rights in data and databases; (d) trade secrets, know-how and other confidential information; and (e) all other intellectual property rights. |
| \*\*Law\*\* | means any statute, law, ordinance, regulation, rule, code, order, constitution, treaty, common law, judgment, decree, or other requirement or rule of law of any federal, state, local or foreign government or political subdivision. |
| \*\*Losses\*\* | mean all losses, damages, liabilities, deficiencies, actions, judgments, interest, awards, penalties, fines, costs or expenses of whatever kind that are actually incurred, including reasonable attorneys' fees and the cost of enforcing any right to indemnification. |
| \*\*Permitted Subcontractor\*\* | has the meaning set forth in Section 3.01(h). |
| \*\*Person\*\* | means an individual, corporation, partnership, joint venture, limited liability company, governmental authority, unincorporated organization, trust, association or other entity. |
| \*\*Receiving Party\*\* | means a party that receives or acquires Confidential Information. |
| \*\*Services\*\* | mean any professional or other services to be provided by Service Provider under this Agreement, as described in more detail on Exhibit A. |
| \*\*Term\*\* | has the meaning set forth in Article VI. |

  

# GPT 5.5 

  

|  |  |
| :-: | :-: |
| \*\*Term (exactly as defined)\*\* | \*\*Definition (verbatim)\*\* |
| \*\*Action\*\* | has the meaning set forth in Section 11.01. |
| \*\*Affiliate\*\* | of a Person means any other Person that directly or indirectly, through one or more intermediaries, controls, is controlled by, or is under common control with, such Person. "Control" means the possession, directly or indirectly, of the power to direct or cause the direction of the management and policies of a Person, whether through ownership of voting securities, by contract or otherwise. |
| \*\*Agreement\*\* | has the meaning set forth in the preamble. |
| \*\*Change Order\*\* | has the meaning set forth in Section 5.02. |
| \*\*Confidential Information\*\* | means any information that is treated as confidential or proprietary by a party, including trade secrets, technology, information pertaining to business operations and strategies, and information pertaining to customers, pricing, and marketing. Confidential Information shall not include information that: (a) is already known to the Receiving Party without restriction; (b) is or becomes generally known by the public other than by breach of this Agreement; (c) is developed by the Receiving Party independently; or (d) is received from a third party not under any obligation to maintain confidentiality. |
| \*\*Customer\*\* | has the meaning set forth in the preamble. |
| \*\*Customer Contract Manager\*\* | has the meaning set forth in Section 4.01(a). |
| \*\*Customer Equipment\*\* | means any equipment, systems, cabling or facilities provided by Customer and used directly or indirectly in the provision of the Services. |
| \*\*Customer Materials\*\* | means any documents, data, know-how, methodologies, software and other materials provided to Service Provider by Customer, including computer programs, reports and specifications. |
| \*\*Deliverables\*\* | means all documents, work product and other materials delivered to Customer or prepared by Service Provider in the course of performing the Services, including any items identified as such on Exhibit A. |
| \*\*Disclosing Party\*\* | means a party that discloses Confidential Information under this Agreement. |
| \*\*Force Majeure Event\*\* | has the meaning set forth in Section 15.01. |
| \*\*Intellectual Property Rights\*\* | means all (a) patents, patent disclosures and inventions (whether patentable or not); (b) trademarks, service marks, trade dress, trade names, logos, corporate names and domain names; (c) copyrights and copyrightable works, and rights in data and databases; (d) trade secrets, know-how and other confidential information; and (e) all other intellectual property rights. |
| \*\*Law\*\* | means any statute, law, ordinance, regulation, rule, code, order, constitution, treaty, common law, judgment, decree, or other requirement or rule of law of any federal, state, local or foreign government or political subdivision. |
| \*\*Losses\*\* | mean all losses, damages, liabilities, deficiencies, actions, judgments, interest, awards, penalties, fines, costs or expenses of whatever kind that are actually incurred, including reasonable attorneys' fees and the cost of enforcing any right to indemnification. |
| \*\*Permitted Subcontractor\*\* | has the meaning set forth in Section 3.01(h). |
| \*\*Person\*\* | means an individual, corporation, partnership, joint venture, limited liability company, governmental authority, unincorporated organization, trust, association or other entity. |
| \*\*Receiving Party\*\* | means a party that receives or acquires Confidential Information. |
| \*\*Services\*\* | mean any professional or other services to be provided by Service Provider under this Agreement, as described in more detail on Exhibit A. |
| \*\*Term\*\* | has the meaning set forth in Article VI. |

**Note:** The term **"Control"** appears within the definition of **Affiliate** and is itself expressly defined in that definition, but it is not presented as a standalone defined term in Article I. Since you requested only terms formally defined in this section, it is not listed separately.

  

# Muse Spark 

Here is the glossary extracted from Article I — only terms that are defined in full in this section (terms that just say "has the meaning set forth in..." are omitted):

  

| Term | Definition |

| --- | --- |

| Affiliate | any other Person that directly or indirectly, through one or more intermediaries, controls, is controlled by, or is under common control with, such Person. |

| Control | the possession, directly or indirectly, of the power to direct or cause the direction of the management and policies of a Person, whether through ownership of voting securities, by contract or otherwise. |

| Confidential Information | any information that is treated as confidential or proprietary by a party, including trade secrets, technology, information pertaining to business operations and strategies, and information pertaining to customers, pricing, and marketing. Confidential Information shall not include information that: (a) is already known to the Receiving Party without restriction; (b) is or becomes generally known by the public other than by breach of this Agreement; (c) is developed by the Receiving Party independently; or (d) is received from a third party not under any obligation to maintain confidentiality. |

| Customer Equipment | any equipment, systems, cabling or facilities provided by Customer and used directly or indirectly in the provision of the Services. |

| Customer Materials | any documents, data, know-how, methodologies, software and other materials provided to Service Provider by Customer, including computer programs, reports and specifications. |

| Deliverables | all documents, work product and other materials delivered to Customer or prepared by Service Provider in the course of performing the Services, including any items identified as such on Exhibit A. |

| Disclosing Party | a party that discloses Confidential Information under this Agreement. |

| Intellectual Property Rights | all (a) patents, patent disclosures and inventions (whether patentable or not); (b) trademarks, service marks, trade dress, trade names, logos, corporate names and domain names; (c) copyrights and copyrightable works, and rights in data and databases; (d) trade secrets, know-how and other confidential information; and (e) all other intellectual property rights. |

| Law | any statute, law, ordinance, regulation, rule, code, order, constitution, treaty, common law, judgment, decree, or other requirement or rule of law of any federal, state, local or foreign government or political subdivision. |

| Losses | all losses, damages, liabilities, deficiencies, actions, judgments, interest, awards, penalties, fines, costs or expenses of whatever kind that are actually incurred, including reasonable attorneys' fees and the cost of enforcing any right to indemnification. |

| Person | an individual, corporation, partnership, joint venture, limited liability company, governmental authority, unincorporated organization, trust, association or other entity. |

| Receiving Party | a party that receives or acquires Confidential Information. |

| Services | any professional or other services to be provided by Service Provider under this Agreement, as described in more detail on Exhibit A. |

  

# Qwen 3.7 Plus

| Term | Definition |

| :--- | :--- |

| "Action" | has the meaning set forth in Section 11.01. |

| "Affiliate" | any other Person that directly or indirectly, through one or more intermediaries, controls, is controlled by, or is under common control with, such Person. |

| "Agreement" | has the meaning set forth in the preamble. |

| "Change Order" | has the meaning set forth in Section 5.02. |

| "Confidential Information" | any information that is treated as confidential or proprietary by a party, including trade secrets, technology, information pertaining to business operations and strategies, and information pertaining to customers, pricing, and marketing. Confidential Information shall not include information that: (a) is already known to the Receiving Party without restriction; (b) is or becomes generally known by the public other than by breach of this Agreement; (c) is developed by the Receiving Party independently; or (d) is received from a third party not under any obligation to maintain confidentiality. |

| "Control" | the possession, directly or indirectly, of the power to direct or cause the direction of the management and policies of a Person, whether through ownership of voting securities, by contract or otherwise. |

| "Customer" | has the meaning set forth in the preamble. |

| "Customer Contract Manager" | has the meaning set forth in Section 4.01(a). |

| "Customer Equipment" | any equipment, systems, cabling or facilities provided by Customer and used directly or indirectly in the provision of the Services. |

| "Customer Materials" | any documents, data, know-how, methodologies, software and other materials provided to Service Provider by Customer, including computer programs, reports and specifications. |

| "Deliverables" | all documents, work product and other materials delivered to Customer or prepared by Service Provider in the course of performing the Services, including any items identified as such on Exhibit A. |

| "Disclosing Party" | a party that discloses Confidential Information under this Agreement. |

| "Force Majeure Event" | has the meaning set forth in Section 15.01. |

| "Intellectual Property Rights" | all (a) patents, patent disclosures and inventions (whether patentable or not); (b) trademarks, service marks, trade dress, trade names, logos, corporate names and domain names; (c) copyrights and copyrightable works, and rights in data and databases; (d) trade secrets, know-how and other confidential information; and (e) all other intellectual property rights. |

| "Law" | any statute, law, ordinance, regulation, rule, code, order, constitution, treaty, common law, judgment, decree, or other requirement or rule of law of any federal, state, local or foreign government or political subdivision. |

| "Losses" | all losses, damages, liabilities, deficiencies, actions, judgments, interest, awards, penalties, fines, costs or expenses of whatever kind that are actually incurred, including reasonable attorneys' fees and the cost of enforcing any right to indemnification. |

| "Permitted Subcontractor" | has the meaning set forth in Section 3.01(h). |

| "Person" | an individual, corporation, partnership, joint venture, limited liability company, governmental authority, unincorporated organization, trust, association or other entity. |

| "Receiving Party" | a party that receives or acquires Confidential Information. |

| "Services" | any professional or other services to be provided by Service Provider under this Agreement, as described in more detail on Exhibit A. |

| "Term" | has the meaning set forth in Article VI. |

  
  

# B2  

Read the obligations sections below. Produce a structured table with three columns: (1) Obligation/Right, (2) Party (Service Provider / Customer / Both), (3) Key condition or trigger. Be exhaustive - do not combine multiple obligations into one row.

 

MASTER SERVICES AGREEMENT — ARTICLES III AND IV

Kubient, Inc. ('Service Provider') and Sphere Digital ('Customer')

 

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

  
  

# Claude Sonnet 4.6 

  

|  |  |  |
| :-: | :-: | :-: |
| \*\*Obligation / Right\*\* | \*\*Party\*\* | \*\*Key Condition or Trigger\*\* |
| Appoint a Contract Manager with authority to act on behalf of Service Provider | Service Provider | Subject to Customer's prior written approval, not unreasonably withheld |
| Maintain the same Contract Manager throughout the Term | Service Provider | Continuous obligation; exception only for Customer request, resignation, or circumstances outside Service Provider's control |
| Replace the Contract Manager or any other Service Provider Personnel | Service Provider | Upon reasonable written request of Customer; must be done promptly |
| Obtain and maintain all necessary licenses and consents | Service Provider | Must be in place before Services start; ongoing thereafter |
| Comply with all relevant Laws applicable to provision of Services | Service Provider | Must be in place before Services start; ongoing thereafter |
| Ensure each Personnel member has legal right to work in the United States | Service Provider | Prior to any Personnel performing Services |
| Conduct background checks on Personnel (credit history, references, criminal record) at Service Provider's sole cost | Service Provider | Prior to any Personnel performing Services |
| Comply with Customer's written rules, regulations, and policies (including security and health and safety) | Service Provider | Triggered upon written communication of such rules by Customer |
| Ensure Personnel comply with Customer's written rules, regulations, and policies | Service Provider | Triggered upon written communication of such rules by Customer |
| Maintain complete and accurate records of time spent and materials used | Service Provider | Continuous obligation throughout the Term |
| Permit Customer to inspect and copy records | Service Provider | No more than once per year; Customer must provide ten (10) business days' advance notice |
| Permit Customer to interview Personnel | Service Provider | No more than once per year; Customer must provide ten (10) business days' advance notice |
| Obtain Customer's prior written approval before engaging any Permitted Subcontractor | Service Provider | Required before each subcontractor engagement; approval not to be unreasonably withheld |
| Remain fully responsible for all Permitted Subcontractor performance | Service Provider | Continuous obligation whenever a Permitted Subcontractor is engaged |
| Bear all responsibility for Personnel compensation, income tax withholding, payroll taxes, unemployment insurance, workers' compensation, and disability benefits | Service Provider | Continuous obligation for all Service Provider Personnel |
| Cooperate with Service Provider in all matters relating to the Services | Customer | Continuous obligation throughout the Term |
| Appoint a Customer Contract Manager with authority to act on behalf of Customer | Customer | Continuous obligation throughout the Term |
| Provide Service Provider with access to premises and facilities | Customer | Upon reasonable request by Service Provider; subject to Customer's security procedures; only to the extent necessary for performing the Services |
| Respond promptly to Service Provider requests for direction, information, approvals, authorizations, or decisions | Customer | Triggered by each Service Provider request; limited to matters reasonably necessary for Service Provider to perform Services |
| Provide complete and accurate information requested by Service Provider | Customer | Triggered by Service Provider request; must be provided in a timely manner |
| Obtain and maintain all necessary licenses and consents applicable to the Services | Customer | Must be in place before the date on which Services are to start; ongoing thereafter |
| Comply with all applicable Law in relation to the Services | Customer | Must be in place before the date on which Services are to start; ongoing thereafter |
| Service Provider is relieved of breach and liability for costs caused by Customer's act or omission | Service Provider | Triggered when Customer or its agents prevent or delay Service Provider's performance |

  

# Gemini 3.1 Flash 

Here is the exhaustive, row-by-row breakdown of all obligations, rights, and exemptions contained in Articles III and IV of the agreement.

|  |  |  |
| :-: | :-: | :-: |
| \*\*Obligation / Right\*\* | \*\*Party\*\* | \*\*Key Condition or Trigger\*\* |
| \*\*Appoint a Service Provider Contract Manager\*\* with authority to act on behalf of the company | Service Provider | Subject to Customer's prior written approval (which cannot be unreasonably withheld). |
| \*\*Maintain the same Service Provider Contract Manager\*\* throughout the duration of the agreement | Service Provider | Ongoing throughout the Term, except if replaced due to Customer's request, resignation, or circumstances outside Service Provider's control. |
| \*\*Promptly replace the Service Provider Contract Manager\*\* or any other Personnel | Service Provider | Upon the reasonable written request of the Customer. |
| \*\*Obtain and maintain all necessary licenses and consents\*\* | Service Provider | Before the Services officially start. |
| \*\*Comply with all relevant Laws\*\* applicable to the provision of the services | Service Provider | Before the Services officially start (and ongoing during performance). |
| \*\*Ensure all Personnel have the legal right to work\*\* in the United States | Service Provider | Prior to any specific Personnel performing any Services. |
| \*\*Conduct background checks\*\* (including credit history, references, and criminal records) at its sole cost | Service Provider | Prior to any specific Personnel performing any Services. |
| \*\*Comply with Customer rules, regulations, and policies\*\* (including security, health, and safety protocols) | Service Provider | When those rules, regulations, and policies have been communicated to the Service Provider in writing. |
| \*\*Ensure all Personnel comply with Customer rules\*\*, regulations, and policies | Service Provider | When those rules, regulations, and policies have been communicated to the Service Provider in writing. |
| \*\*Maintain complete and accurate records\*\* of time spent and materials used | Service Provider | Ongoing during the performance of the contract. |
| \*\*Permit Customer to inspect and copy records\*\* and interview Personnel | Service Provider | Triggered by Customer request; limited to no more than once per year, and requires ten (10) business days' advance notice. |
| \*\*Obtain written approval before engaging a subcontractor\*\* | Service Provider | Prior to engaging any Permitted Subcontractor (approval not to be unreasonably withheld). |
| \*\*Remain fully responsible for subcontractor performance\*\* as if they were own employees | Service Provider | Ongoing upon the engagement of any Permitted Subcontractor. |
| \*\*Pay all Service Provider Personnel compensation\*\* (including withholding income taxes, payroll taxes, unemployment insurance, workers' compensation, and disability benefits) | Service Provider | Ongoing during the employment and assignment of Personnel. |
| \*\*Cooperate with the Service Provider\*\* in all matters relating to the Services | Customer | Ongoing throughout the relationship. |
| \*\*Appoint a Customer Contract Manager\*\* with authority to act on behalf of the company | Customer | Established at the start of or during the contract. |
| \*\*Provide access to premises and facilities\*\* | Customer | When reasonably requested by the Service Provider to perform the work, and subject to Customer's security procedures. |
| \*\*Respond promptly to requests\*\* for direction, information, approvals, authorizations, or decisions | Customer | When reasonably necessary for the Service Provider to perform the Services. |
| \*\*Provide complete and accurate information\*\* in a timely manner | Customer | Whenever the Service Provider requests it. |
| \*\*Obtain and maintain all necessary licenses and consents\*\* in relation to the Services | Customer | Before the specific date on which the Services are scheduled to start. |
| \*\*Comply with all applicable Law\*\* in relation to the Services | Customer | Before the specific date on which the Services are scheduled to start. |
| \*\*Exemption from breach and liability\*\* for Customer's direct or indirect costs | Service Provider (Right) | Triggered if the Service Provider’s performance is prevented or delayed by an act or omission of the Customer or its agents. |

  

# GPT 5.5 

  

|  |  |  |
| :-: | :-: | :-: |
| \*\*Obligation/Right\*\* | \*\*Party\*\* | \*\*Key condition or trigger\*\* |
| Appoint a Service Provider Contract Manager with authority to act on behalf of Service Provider | Service Provider | Subject to Customer's prior written approval, not unreasonably withheld |
| Maintain the same Service Provider Contract Manager throughout the Term | Service Provider | Throughout the Term, except due to Customer request, resignation, or circumstances outside Service Provider's control |
| Promptly replace the Service Provider Contract Manager | Service Provider | Upon reasonable written request of Customer |
| Promptly replace any other Service Provider Personnel | Service Provider | Upon reasonable written request of Customer |
| Obtain all necessary licenses | Service Provider | Before Services start |
| Maintain all necessary licenses | Service Provider | During provision of the Services after Services start |
| Comply with all relevant Laws applicable to the provision of the Services | Service Provider | Before Services start and during provision of the Services |
| Ensure Personnel have the legal right to work in the United States | Service Provider | Prior to any Personnel performing Services |
| Conduct background checks on Personnel | Service Provider | Prior to any Personnel performing Services |
| Bear the sole cost of Personnel background checks | Service Provider | When conducting required background checks |
| Comply with Customer's written rules, regulations, and policies | Service Provider | When such rules, regulations, and policies are communicated in writing |
| Ensure Personnel comply with Customer's written rules, regulations, and policies | Service Provider | When such rules, regulations, and policies are communicated in writing |
| Comply with Customer security procedures | Service Provider | When communicated in writing by Customer |
| Ensure Personnel comply with Customer security procedures | Service Provider | When communicated in writing by Customer |
| Comply with Customer health and safety requirements | Service Provider | When communicated in writing by Customer |
| Ensure Personnel comply with Customer health and safety requirements | Service Provider | When communicated in writing by Customer |
| Maintain complete and accurate records of time spent | Service Provider | During performance of the Services |
| Maintain complete and accurate records of materials used | Service Provider | During performance of the Services |
| Permit Customer to inspect records | Service Provider | No more than once per year and upon ten (10) business days' advance notice |
| Permit Customer to copy records | Service Provider | No more than once per year and upon ten (10) business days' advance notice |
| Permit Customer to interview Personnel | Service Provider | No more than once per year and upon ten (10) business days' advance notice |
| Obtain Customer's written approval before engaging a Permitted Subcontractor | Service Provider | Prior to engaging any Permitted Subcontractor; approval not unreasonably withheld |
| Remain fully responsible for all Permitted Subcontractor performance | Service Provider | Whenever a Permitted Subcontractor is engaged |
| Pay and administer compensation for Service Provider Personnel | Service Provider | For all Service Provider Personnel |
| Withhold income taxes for Service Provider Personnel | Service Provider | For all Service Provider Personnel compensation |
| Withhold payroll taxes for Service Provider Personnel | Service Provider | For all Service Provider Personnel compensation |
| Provide unemployment insurance for Service Provider Personnel | Service Provider | For all Service Provider Personnel |
| Provide workers' compensation coverage for Service Provider Personnel | Service Provider | For all Service Provider Personnel |
| Provide disability benefits for Service Provider Personnel | Service Provider | For all Service Provider Personnel |
| Cooperate with Service Provider in all matters relating to the Services | Customer | During performance of the Services |
| Appoint a Customer Contract Manager with authority to act on behalf of Customer | Customer | During the term of the Services relationship |
| Provide access to premises reasonably requested by Service Provider | Customer | Subject to security procedures and for the purpose of performing the Services |
| Provide access to facilities reasonably requested by Service Provider | Customer | Subject to security procedures and for the purpose of performing the Services |
| Respond promptly to requests for direction | Customer | When reasonably necessary for Service Provider to perform Services |
| Respond promptly to requests for information | Customer | When reasonably necessary for Service Provider to perform Services |
| Respond promptly to requests for approvals | Customer | When reasonably necessary for Service Provider to perform Services |
| Respond promptly to requests for authorizations | Customer | When reasonably necessary for Service Provider to perform Services |
| Respond promptly to requests for decisions | Customer | When reasonably necessary for Service Provider to perform Services |
| Provide complete information requested by Service Provider | Customer | As Service Provider may request, in a timely manner |
| Provide accurate information requested by Service Provider | Customer | As Service Provider may request, in a timely manner |
| Provide requested information in a timely manner | Customer | As Service Provider may request |
| Obtain all necessary licenses and consents relating to the Services | Customer | Before the date on which Services are to start |
| Maintain all necessary licenses and consents relating to the Services | Customer | During the Services relationship |
| Comply with all applicable Law in relation to the Services | Customer | Before the date on which Services are to start and during the Services relationship |
| Not be deemed in breach due to prevention or delay caused by Customer or its agents | Service Provider (right/protection) | If Service Provider's performance is prevented or delayed by any act or omission of Customer or its agents |
| Not be liable for costs sustained by Customer arising from such prevention or delay | Service Provider (right/protection) | If Service Provider's performance is prevented or delayed by any act or omission of Customer or its agents |
| Inspect Service Provider records | Customer (right) | No more than once per year and upon ten (10) business days' advance notice |
| Copy Service Provider records | Customer (right) | No more than once per year and upon ten (10) business days' advance notice |
| Interview Service Provider Personnel | Customer (right) | No more than once per year and upon ten (10) business days' advance notice |
| Approve or reject proposed Permitted Subcontractors | Customer (right) | Prior to Service Provider engaging a Permitted Subcontractor; approval may not be unreasonably withheld |
| Approve or reject the Service Provider Contract Manager | Customer (right) | Prior written approval required; approval may not be unreasonably withheld |
| Request replacement of the Service Provider Contract Manager | Customer (right) | Upon reasonable written request |
| Request replacement of any other Service Provider Personnel | Customer (right) | Upon reasonable written request |

  

# Muse Spark 

Here is the exhaustive breakdown of Articles III and IV — each distinct duty or right is listed separately:

  

| Obligation / Right | Party | Key condition or trigger |

|---|---|---|

| Appoint a Service Provider Contract Manager with authority to act on behalf of Service Provider | Service Provider | Subject to Customer's prior written approval, not unreasonably withheld |

| Maintain the same Service Provider Contract Manager throughout the Term | Service Provider | Except due to Customer request, resignation, or circumstances outside Service Provider's control |

| Promptly replace the Service Provider Contract Manager or any other Service Provider Personnel | Service Provider | Upon reasonable written request of Customer |

| Obtain and maintain all necessary licenses and consents applicable to the provision of the Services | Service Provider | Before Services start |

| Comply with all relevant Laws applicable to the provision of the Services | Service Provider | Before Services start |

| Ensure Personnel have the legal right to work in the United States | Service Provider | Prior to any Personnel performing Services |

| Conduct background checks including credit history, references and criminal record at Service Provider's sole cost | Service Provider | Prior to any Personnel performing Services |

| Comply with all Customer rules, regulations and policies communicated in writing, including security procedures and health and safety | Service Provider | Only those communicated in writing by Customer |

| Ensure Personnel comply with all Customer rules, regulations and policies communicated in writing, including security procedures and health and safety | Service Provider | Only those communicated in writing by Customer |

| Maintain complete and accurate records of time spent and materials used | Service Provider | Ongoing during Term |

| Permit Customer to inspect and copy records and interview Personnel | Service Provider | No more than once per year, on ten (10) business days' advance notice |

| Obtain Customer's written approval before engaging any Permitted Subcontractor | Service Provider | Approval not unreasonably withheld; required before engagement |

| Remain fully responsible for all Permitted Subcontractor performance as if they were Service Provider's own employees | Service Provider | Upon engagement of any Permitted Subcontractor |

| Be responsible for all Service Provider Personnel compensation, including withholding income taxes, payroll taxes, unemployment insurance, workers' compensation, and disability benefits | Service Provider | Ongoing during Term |

| Cooperate with Service Provider in all matters relating to the Services | Customer | Ongoing during Term |

| Appoint a Customer Contract Manager with authority to act on behalf of Customer | Customer | Ongoing during Term |

| Provide access to premises and facilities reasonably requested by Service Provider | Customer | Subject to Customer security procedures; for purpose of performing Services |

| Respond promptly to Service Provider requests for direction, information, approvals, authorizations or decisions | Customer | When reasonably necessary for Service Provider to perform Services |

| Provide complete and accurate information as Service Provider may request | Customer | In a timely manner |

| Obtain and maintain all necessary licenses and consents in relation to the Services | Customer | Before date on which Services are to start |

| Comply with all applicable Law in relation to the Services | Customer | Before date on which Services are to start |

| Right not to be in breach of the Agreement | Service Provider | If performance is prevented or delayed by any act or omission of Customer or its agents |

| Right not to be liable for costs sustained by Customer arising from prevention or delay | Service Provider | If costs arise directly or indirectly from Customer act or omission that prevents or delays performance |

  

# Qwen 3.7 Plus

| Obligation / Right | Party | Key Condition or Trigger |

| :--- | :--- | :--- |

| Appoint a Service Provider Contract Manager with authority to act on behalf of Service Provider | Service Provider | Subject to Customer's prior written approval, not unreasonably withheld |

| Maintain the same Service Provider Contract Manager throughout the Term | Service Provider | Except due to Customer request, resignation, or circumstances outside Service Provider's control |

| Promptly replace the Service Provider Contract Manager or any other Service Provider Personnel | Service Provider | Upon reasonable written request of Customer |

| Obtain and maintain all necessary licenses and consents and comply with all relevant Laws applicable to the provision of the Services | Service Provider | Before Services start |

| Ensure Personnel have the legal right to work in the United States | Service Provider | Prior to any Personnel performing Services |

| Conduct background checks including credit history, references, and criminal record at Service Provider's sole cost | Service Provider | Prior to any Personnel performing Services |

| Comply with, and ensure Personnel comply with, all rules, regulations, and policies of Customer communicated in writing, including security procedures and health and safety | Service Provider | When communicated in writing by Customer |

| Maintain complete and accurate records of time spent and materials used | Service Provider | Ongoing during the performance of Services |

| Permit Customer to inspect and copy records and interview Personnel | Service Provider | No more than once per year on ten (10) business days' advance notice |

| Obtain Customer's written approval before engaging any Permitted Subcontractor | Service Provider | Before engaging any Permitted Subcontractor (approval not to be unreasonably withheld) |

| Remain fully responsible for all Permitted Subcontractor performance as if they were Service Provider's own employees | Service Provider | Upon engaging a Permitted Subcontractor |

| Pay all Service Provider Personnel compensation, including withholding of income taxes, payroll taxes, unemployment insurance, workers' compensation, and disability benefits | Service Provider | Ongoing for all Service Provider Personnel |

| Cooperate with Service Provider in all matters relating to the Services | Customer | Ongoing |

| Appoint a Customer Contract Manager with authority to act on behalf of Customer | Customer | Ongoing / At commencement of the Agreement |

| Provide access to premises and facilities reasonably requested by Service Provider for the purpose of performing the Services | Customer | Subject to security procedures and reasonable request by Service Provider |

| Respond promptly to any Service Provider request for direction, information, approvals, authorizations, or decisions | Customer | When reasonably necessary for Service Provider to perform Services |

| Provide complete and accurate information as Service Provider may request | Customer | In a timely manner upon request by Service Provider |

| Obtain and maintain all necessary licenses and consents and comply with all applicable Law in relation to the Services | Customer | Before the date on which Services are to start |

| Right to not be in breach and not be liable for costs sustained by Customer arising directly or indirectly from prevention or delay | Service Provider | If Service Provider's performance is prevented or delayed by any act or omission of Customer or its agents |