# RAG Query Export

**Date:** 2026-07-01 14:52:58  
**Model:** `Ollama:ministral-3:14b`

---

## Query

What is the process for creating Tool Qualification Process according to ISO 26262 section 8? How can this be applied to lcov based on toolchain analysis?

---

## AI Response

Based on **ISO 26262-8:2018**, the **Tool Qualification Process** involves several key steps (as outlined in **Section 11**). Below is a structured breakdown of the process and its application to **lcov**:

---

### **Process for Tool Qualification (ISO 26262-8, Section 11)**
The qualification process includes:

#### **1. Planning of Tool Usage (Clause 11.4.4)**
   - Define the intended use of the tool in the development lifecycle.
   - Identify safety-critical phases where the tool is applied.

#### **2. Evaluation by Analysis (Clause 11.4.5)**
   - **Tool Impact (TI)**:
     Determine how errors from the tool could affect the final product (e.g., code generation, verification).
     For **lcov**, TI = **TI2** (as per provided table), meaning it does not directly modify code but provides coverage analysis.
   - **Tool Error Detection (TD)**:
     Assess whether errors in the tool’s output can be detected (e.g., via manual review or other tools like `gcov`).
     For **lcov**, TD = **TD1** (low detection capability for its own errors), but since it relies on `gcov`, some safeguards exist.
   - **HAZOP Analysis**:
     Conduct a HAZOP study if the tool is classified as **IEC 61508 T2 or T3**. Since **lcov = T2**, this applies:
     - Identify potential malfunctions (e.g., incorrect coverage reporting).
     - Define safeguards (e.g., cross-checking with `gcov` output).

#### **3. Qualification of the Tool (Clause 11.4.6)**
   - For **TCL ≥ TCL2**, formal qualification may be required:
     - Review vendor documentation, version history, and change logs.
     - Verify compliance with ISO 26262-8 requirements for tool confidence.

#### **4. Increased Confidence from Use (Clause 11.4.7)**
   - Monitor tool behavior in production to detect anomalies over time.

---

### **Application to lcov**
From the provided context:
| Tool | TI | TD | TCL | IEC 61508 T |
|------|----|----|-----|------------|
| **lcov** | **TI2** (no direct code modification) | **TD1** (limited error detection) | **TCL1** | **T2** |

#### **Key Actions for lcov Qualification**
1. **Tool Impact Justification**:
   - Since `lcov` only displays coverage data and does not alter code, its impact is low (**TI2**).
   - Safeguard: Cross-validate with `gcov` output to detect discrepancies.

2. **HAZOP Analysis (T2 Classification)**:
   - Identify risks like incorrect coverage reporting or parsing errors.
   - Mitigation: Use manual review of critical reports and automated checks in the build process.

3. **Tool Confidence Level (TCL1)**:
   - Since `lcov` is open-source with a stable version history, its TCL remains low (**TCL1**).
   - No formal qualification is required for TCL1 tools unless higher confidence is needed.

4. **Documentation & Safeguards**:
   - Maintain records of tool versions and usage.
   - Define procedures to handle malfunctions (e.g., fallback to manual coverage checks).

---

### **Summary**
- **lcov** qualifies as a low-risk tool (**TCL1**) due to its non-code-modifying nature.
- A HAZOP study is required for T2 tools like `lcov` to assess anomalous behavior.
- Safeguards (e.g., cross-checking with `gcov`) ensure robustness.

For higher confidence, consider **formal qualification** or upgrading the tool’s classification.

---

## Retrieved Sources

### Source 1

- **File:** toolchain-analysis_Share_Input.docx
- **Page / Chunk:** [48, 49, 50, 51, 52, 53, 54, 55, 56]

Table  Mapping of tools to Tool Confidence Levels

ISO 26262-8:2018 Tool Qualification Rationale

Tool Analysis

The following information is given below for each identified tool. This conforms to ISO 26262-8:2018:

A description of the features, functions and technical properties of the software tool.

The user manual or other usage guides.

A description of the environment required for its operation.

A description of the expected behavior of the software tool under anomalous operating conditions. To structure this analysis, a HAZOP study is performed for all tools with IEC 61508 classification of T2 or T3 (see Note 1 of Section 7.4.4.5 of IEC61508-3). The HAZOP analysis has been carried out in accordance with IEC61882: Hazard and operability studies (HAZOP studies)—Application guide, 2001, and uses the terminology introduced in Figure 4.1 therein.

A description of known software tool malfunctions and the appropriate safeguards, avoidance or workaround measures.

### Source 2

- **File:** toolchain-analysis_Share_Input.docx
- **Page / Chunk:** 46

To assign a Tool Confidence Level (TCL), it is necessary to assign a Tool Impact (TI) and a Tool Error Detection (TD) level in accordance with paragraph 11.4.5.2 of ISO 26262-8:2018 and then use Table 3 of that document to determine the TCL. Table 4 summarizes the allocation of these values to the tools used in the development and verification of AV SW. The IEC 61508 Tool Class (T) is also provided so that, per IEC 61508-3 recommendations, a HAZOP is developed for tools whose IEC 61508 Tool Class is either T2 or T3 to further analyze tool behavior under anomalous conditions.

| Tool | ISO 26262
TI | ISO 26262
TD | ISO 26262
TCL | IEC 61508
T | Justification |
| --- | --- | --- | --- | --- | --- |
| Lcov | TI2 | TD1 | TCL1 | T2 | This tool does not directly affect the code. It is coverage display tool.
This is coverage display tool. Does not affect code. Bug escape can be detected from output file of gcov |
| Gcov | TI2 | TD3 | TCL3 | T2 |  |

### Source 3

- **File:** iso26262_wp-e.pdf
- **Page / Chunk:** 8

and implementing the standard requires a great deal of time and effort, and proving that all 
requirements have been met can be a daunting task. For this reason, it is much more efficient to 
undergo an audit and receive certification from a 3rd party organization rather than explain and 
show compliance to individual clients. 
 
5-3 ROHM has received process certification 
ROHM began building an ISO 26262 process in 2015 and was able to receive ISO 26262 
Process Certification from third-party certification authority TÜV Rheinland in Germany two and 
a half years later , in March of 2018 (Fig. 4). In other words, ROHM’s ISO 26262 process is 
recognized to be compliant with the ISO 26262 standard. And while it is common to build a 
process by receiving advice from consultants, ROHM attended a number of workshops to better 
understand and study the standard and successfully achieve a compliant process. 
 
 
Figure 4. ROHM's ISO 26262 Process Certificate 
 
5-4 Functional Safety

### Source 4

- **File:** ISO-26262-8-2018.pdf
- **Page / Chunk:** 4

compliance with its evaluation criteria or its qualification ..................27
11.4.4 Planning of usage of a software tool ............................................................................................................27
11.4.5 Evaluation of a software tool by analysis .................................................................................................28
11.4.6 Qualification of a software tool ........................................................................................................................30
11.4.7 Increased confidence from use .........................................................................................................................30
11.4.8 Evaluation of the tool development process .........................................................................................31
11.4.9 Validation of the software tool

### Source 5

- **File:** toolchain-analysis_Share_Input.docx
- **Page / Chunk:** [57, 58, 59, 60, 61, 62, 63, 64, 65, 66]

The measures for the detection of malfunctions and the corresponding erroneous output of the software tool identified during the determination of the required level of confidence for this software tool.

Analysis of lcov

Vendor

lcov is an open source tool maintained using GPL 2 License

Version: 1.14

https://github.com/linux-test-project/lcov/blob/master/COPYING

Features and Functions

lcov is a graphical front-end to display the coverage data provided by gcov. It displays the coverage report in HTML format. lcov supports statement, function, and branch along with Modified Condition/Decision Coverage measurement. It provides information about what parts of a program are executed (i.e. "covered") while running the program and test case.

Sample output of lcov:

The above image represents the top-level result of the entire directory from which user can navigate to various sub directories.

### Source 6

- **File:** ISO-26262-8-2018.pdf
- **Page / Chunk:** 15

ISO 26262-8:2018(E)
5.3.2 Further supporting information
The following information can be considered:
— any applicable supporting information of the relevant phases of the safety lifecycle for which a 
distributed development is planned and carried out; and
— the supplier’s tender based on a request for quotation (RFQ) (from an external source).
5.4 Requirements and recommendations
5.4.1 Application of requirements
5.4.1.1 The requirements of this clause shall apply to each item and element developed in accordance 
with the ISO 26262 series of standards, except for off-the-shelf elements not built-to-order to fulfil 
specific safety requirements, if one of the following applies:
a) the off-the-shelf hardware element is qualified according to well-established procedures based on 
quality standards (e.g. AEC standards for electronic components), and is evaluated according to 
Clause 13,
b) the off-the-shelf software component is qualified according to Clause 12, or
c) the off-the-shelf

### Source 7

- **File:** ISO-26262-8-2018.pdf
- **Page / Chunk:** 8

technologies (e.g. mechanical, hydraulic and pneumatic) can be 
considered.
The achievement of functional safety is influenced by the development process (including such 
activities as requirements specification, design, implementation, integration, verification, validation 
and configuration), the production and service processes and the management processes.
Safety is intertwined with common function-oriented and quality-oriented activities and work 
products. The ISO 26262 series of standards addresses the safety-related aspects of these activities and 
work products.
Figure 1  shows the overall structure of the ISO 26262 series of standards. The ISO 26262 series of 
standards is based upon a V-model as a reference process model for the different phases of product 
development. Within the figure: 
— the shaded “V”s represent the interconnection among ISO 26262-3, ISO 26262-4, ISO 26262-5, 
ISO 26262-6 and ISO 26262-7;
— for motorcycles:
— ISO 26262-12:2018, Clause 8 supports ISO

### Source 8

- **File:** toolchain-analysis_Share_Input.docx
- **Page / Chunk:** [24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45]

Table  Tools Deployed

C Language Tools: Preprocessor, C Compiler, Assembler, Archiver and Linker

C++ Language Tools: Preprocessor, C++ Compiler, Assembler, Archiver and Linker

IDL generation tools

Build Environment

List the tools used in the build environment. Describe the build process here.

Bitbucket

GNU make

Cmake

Jenkins

Security tool

Test Tools

VectorCAST

Helix QAC

Miscellaneous

Doxygen

Various Text Editors

Tool Analysis

Introduction

This chapter contains information about specific tools used in the development and validation of the AV SW.

This chapter classifies each of the tools associated with the development or use of the AV SW in accordance with ISO 26262-8:2018, Section 11 (“Confidence in the use of software tools”).

Tool Confidence Level Classification
