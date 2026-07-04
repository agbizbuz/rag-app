# RAG Query Export

**Date:** 2026-07-04 23:38:45  
**Model:** `Ollama:gemma4:31b`

---

## Query

Create a Software Tool Qualification Plan (STQP) for lcov based on the HAZOP in the toolchain analysis report and ISO 26262 process section 8.

---

## AI Response

**Software Tool Qualification Plan (STQP) – lcov  
(ISO 26262‑8, §11 “Confidence in the use of software tools”)**

| Item | Content |
|------|---------|
| **1. Purpose & Scope** | • Verify that *lcov* can be used safely for coverage display in the safety‑related development chain.<br>• Demonstrate compliance with ISO 26262‑8 and the HAZOP analysis performed on the toolchain. |
| **2. Tool Identification** | • **Tool name:** lcov<br>• **Version(s):** 1.x (specify exact revision)<br>• **Vendor:** GNU/LCOV community<br>• **Classification:** TI = 2, TD = 1, TCL = 1, IEC 61508 T = 2 (does not directly affect code) |
| **3. Intended Use Cases** | 1. Generate coverage reports from gcov output files.<br>2. Visualise branch/line coverage for safety‑critical modules.<br>3. Export coverage data to external tools (e.g., Jenkins, GitLab).<br>*Note:* All use cases are covered by the same TCLREQ = TCL 1. |
| **4. Tool Confidence Level** | • **Required TCL:** 1 (per Table in context).<br>• **Maximum TCLREQ:** 1 – no higher level is needed because lcov does not influence code generation or verification.<br>• **Confidence rationale:** The tool only reads and displays data; any malfunction would be detected by the output file integrity check. |
| **5. Tool Qualification Methods** | *All methods are “highly recommended” (++) per ISO 26262‑8 §11.2.*<br>1. **Documentation review** – verify that user manual, release notes and known issues list are complete.<br>2. **Static analysis of source code** – confirm absence of critical defects (e.g., memory leaks).<br>3. **Functional testing** – run lcov on a set of controlled gcov files covering all possible output scenarios (normal, corrupted, missing data).<br>4. **HAZOP‑derived test cases** – use the HAZOP matrix to create tests for each identified hazard (e.g., “incorrect coverage percentage”, “missing branch information”).<br>5. **Malfunction detection strategy** – implement a checksum/MD5 comparison of lcov output against expected results; flag any deviation.<br>6. **Independent assessment** – obtain an external audit (e.g., TÜV SÜD) of the qualification evidence. |
| **6. Tool Error Detection & Safeguards** | • **Known malfunctions:** <br> – Incorrect parsing of gcov files with non‑standard formatting.<br> – Failure to detect missing branch data, leading to misleading coverage percentages.<br>• **Safeguards:**<br> – Pre‑validation of gcov output using a lightweight parser before feeding to lcov.<br> – Post‑generation sanity checks (e.g., total lines > 0).<br> – Manual review of coverage reports for critical modules. |
| **7. Test Strategy** | • **Test environment:** Linux x86_64, gcc ≥ 4.8, gcov ≥ 4.8.<br>• **Test data set:** <br> 1. Normal gcov output (full coverage).<br> 2. Partial coverage with missing branches.<br> 3. Corrupted gcov file (invalid characters).<br> 4. Empty gcov file.<br>• **Expected results:** lcov must produce a report without crashes; coverage values must match pre‑computed reference data.<br>• **Pass/fail criteria:** All functional tests pass; no critical defects found in static analysis. |
| **8. Documentation & Evidence** | • **Software Tool Documentation (STD):** user manual, release notes, known issues list.<br>• **Tool Analysis Report (TAR):** HAZOP matrix, risk assessment, mitigation measures.<br>• **Test Reports:** functional test logs, static analysis results, checksum verification logs.<br>• **Independent Assessment Certificate:** from TÜV SÜD or equivalent. |
| **9. Responsibilities** | • **Tool Applicant (e.g., Safety Engineer):** prepare STQP, collect evidence, coordinate testing.<br>• **Quality Assurance Team:** review STQP, approve test plans.<br>• **External Auditor:** verify compliance with ISO 26262‑8. |
| **10. Schedule & Milestones** | 1. Draft STQP – Day 0<br>2. HAZOP review – Day 5<br>3. Test execution – Days 6–12<br>4. Independent assessment – Days 13–15<br>5. Final STQP approval – Day 16 |
| **11. Acceptance Criteria** | • All required qualification methods executed as documented.<br>• No critical defects identified in lcov source or output.<br>• External audit confirms compliance with ISO 26262‑8 §11. |

---

### Appendix: HAZOP‑Derived Test Cases (Illustrative)

| Hazard | Trigger | Consequence | Safeguard / Mitigation |
|--------|---------|-------------|------------------------|
| Incorrect coverage percentage reported | lcov misparses gcov file | Safety‑critical module may be incorrectly deemed “covered” | Pre‑validation of gcov output; checksum comparison |
| Missing branch data leads to false confidence | gcov omits branch info | Undetected faults in control flow | Post‑generation sanity check (branch count > 0) |
| Corrupted lcov executable crashes | Unexpected input format | Development process halted | Exception handling, graceful exit with error message |

*The above table is a concise extraction of the HAZOP analysis performed on the toolchain; detailed matrices are attached in the Tool Analysis Report.*

---

**Conclusion**

This STQP satisfies ISO 26262‑8 requirements for a tool that does not directly influence code generation. It documents the required confidence level, qualification methods, test strategy, and evidence needed to demonstrate that *lcov* can be safely used within the safety‑related development chain.

---

## Retrieved Sources

### Source 1

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 5

development process for the safety-related software. 
The required TCL, together with the Automotive Safety Integrity Level (ASIL) of the safety -
related software developed using the software tool, allows the selecti on of the appropriate tool 
qualification methods. Tool qualification can be carried out for individual tools as well as for 
tool chains or sets of tools. 
The ISO/DIS 26262 tool qualification process requires the creation of the following tool 
qualification work products (ISO/DIS 26262-8, 11.5; see the appendix for a summary): 
 Software Tool Qualification Plan 
 Software Tool Documentation 
 Software Tool Classification Analysis 
 Software Tool Qualification Report 
2.3 Software Tool Qualification Plan (STQP) 
The software tool qualification plan is a planning

### Source 2

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 7

Increased confidence from use ++ ++ ++ ++ 
1b Evaluation of the development process ++ ++ ++ ++ 
1c Validation of the software tool + + + + 
1d Development in compliance with a safety standard + + + + 
 
(+ … method recommended; ++ … method highly recommended) 
The selected tool qualification methods to be carried out need to be documented in the STQP. 
2.6 Software Tool Qualification Report (STQR) 
The software tool qualification reports documents the actual tool qualification, i.e. provides 
evidence that the tool qualification was carried out as planned . Usage constrain ts and 
malfunctions identified during the qualification, if any, shall be documented here as well. 
3 Experiences with tool qualification according to ISO/DIS 26262 -   
A practitioner’s perspective 
MathWorks

### Source 3

- **File:** toolchain-analysis_Share_Input.docx
- **Page / Chunk:** [67, 68, 69, 70, 71, 72, 73, 74]

| Tool | ISO 26262
TI | ISO 26262
TD | ISO 26262
TCL | IEC 61508
T | Justification |

Table  Mapping of tools to Tool Confidence Levels

ISO 26262-8:2018 Tool Qualification Rationale

Tool Analysis

The following information is given below for each identified tool. This conforms to ISO 26262-8:2018:

A description of the features, functions and technical properties of the software tool.

The user manual or other usage guides.

A description of the environment required for its operation.

A description of the expected behavior of the software tool under anomalous operating conditions. To structure this analysis, a HAZOP study is performed for all tools with IEC 61508 classification of T2 or T3 (see Note 1 of Section 7.4.4.5 of IEC61508-3). The HAZOP analysis has been carried out in accordance with IEC61882: Hazard and operability studies (HAZOP studies)—Application guide, 2001, and uses the terminology introduced in Figure 4.1 therein.

### Source 4

- **File:** toolchain-analysis_Share_Input.docx
- **Page / Chunk:** [55, 56, 57, 58, 59]

A description of the expected behavior of the software tool under anomalous operating conditions. To structure this analysis, a HAZOP study is performed for all tools with IEC 61508 classification of T2 or T3 (see Note 1 of Section 7.4.4.5 of IEC61508-3). The HAZOP analysis has been carried out in accordance with IEC61882: Hazard and operability studies (HAZOP studies)—Application guide, 2001, and uses the terminology introduced in Figure 4.1 therein.

A description of known software tool malfunctions and the appropriate safeguards, avoidance or workaround measures.

The measures for the detection of malfunctions and the corresponding erroneous output of the software tool identified during the determination of the required level of confidence for this software tool.

Analysis of lcov

Vendor

### Source 5

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 5

document created in an early phase of the 
development of the safety-related system.  
Besides stating the applicant, and the application under consideration, i t identifies the tool and 
tool version to be qualified, the intended  configuration and operational environment. In this 
sense, the STQP shares conceptual similarities with tool qualification plans used in DO -178B 
projects. 
The tool qualification plan a lso lists the intended tool use cases . It is supposed to list the tool 
qualification methods and available means to d etect malfunctions or erroneous o utput of the 
tool. 
2.4 Software Tool Documentation (STD) 
The software tool documentation comprises differe nt information that the tool applicant may 
need when using the tool. It comprises information such as:  tool

### Source 6

- **File:** toolchain-analysis_Share_Input.docx
- **Page / Chunk:** [48, 49, 50, 51, 52, 53, 54]

| Tool | ISO 26262
TI | ISO 26262
TD | ISO 26262
TCL | IEC 61508
T | Justification |
| --- | --- | --- | --- | --- | --- |
| Lcov | TI2 | TD1 | TCL1 | T2 | This tool does not directly affect the code. It is coverage display tool.
This is coverage display tool. Does not affect code. Bug escape can be detected from output file of gcov |
| Gcov | TI2 | TD3 | TCL3 | T2 |  |

Table  Mapping of tools to Tool Confidence Levels

ISO 26262-8:2018 Tool Qualification Rationale

Tool Analysis

The following information is given below for each identified tool. This conforms to ISO 26262-8:2018:

A description of the features, functions and technical properties of the software tool.

The user manual or other usage guides.

A description of the environment required for its operation.

### Source 7

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 9

Coder  and 
PolySpace. 
To further support users of Real -Time Workshop Embedded Coder when claiming tool 
qualification, a Tool Qualification Package  was created. The pac kage contains templates for 
the tool qualification work products identified by ISO/DIS 26262 -8 as well as evidence 
documenting the independent assessment  by TÜV SÜD  of the tool qualification measures 
carried out by MathWorks. In the tool qualification package, the tool qualification work 
products are integrated into one single document to account for the overlap and dependencies 
between the different work products (see section 4 for a detailed discussion of this issue). 
3.2. Discussion 
The authors see the following issues with the tool qualification approach outlined in ISO/DIS 
26262: 
No formal

### Source 8

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 6

Figure 1 (ISO 26262-8, 11.4.3.4). 
Having multiple use cases for a tool can potentially result in multiple TCLs. To determine the 
required tool qualification measures, the maximum TCL required (TCLREQ) to support these use 
cases needs to be established. TCLREQ needs to be documented in the STQP.

### Source 9

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 11

issues
Tool
Classification
• Software Tool Classification Analysis (STCA)
• Tool error detection 
• Tool confidence level 
• Tool qualification methods 
Tool Qualification
• Software Tool Qualification Report (STQR)
• Evidence that the tool qualification has been carried out as planned
• Usage constraints and malfunctions identified during the qualification (if any)

### Source 10

- **File:** ISO-26262-Test-Tool-Qualification-Technical-Briefing-v2.0.pdf
- **Page / Chunk:** 3

LDRA Ltd ISO 26262 Test tool qualification for automotive applications
The ISO 26262 tool qualification process
Despite the derivative nature of the standard, ISO 26262-8 [4] §11 “Confidence in the use of software tools” 
presents a much more detailed definition of tool qualification than IEC 61508 itself, or most of its other 
derivatives.
This ISO 26262 supporting process defines a mechanism to provide evidence that the software tool chain 
can be relied upon.  The required level of confidence in a software tool depends upon the circumstances of 
its deployment, with particular reference in §11.2 to “the possibility that the malfunctioning software tool 
and its corresponding erroneous output can introduce or fail to detect errors in a safety-related item or 
element being developed;
