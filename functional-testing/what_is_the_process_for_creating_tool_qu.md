# RAG Query Export

**Date:** 2026-06-16 16:25:16\
**Model:** `Ollama:ministral-3:14b`

---

## Query

What is the process for creating Tool Qualification Process according to ISO 26262?

---

## AI Response

Based on the provided context, **ISO/DIS 26262** outlines a structured tool qualification process that involves the creation of specific work products. Here’s the key process summarized:

1. **Tool Qualification Work Products (as per ISO/DIS 26262-8)**:
   The process requires generating the following documents:
   - **Software Tool Qualification Plan (STQP)**: A planning document created early in development, identifying the tool, version, configuration, operational environment, and applicant.
   - **Software Tool Documentation**: Comprehensive documentation of the tool’s functionality and behavior.
   - **Software Tool Classification Analysis**: An analysis to classify the tool based on its role in safety-related systems (e.g., TCL 1–3).
   - **Software Tool Qualification Report**: A final report summarizing the qualification process, results, and compliance with ISO 26262 requirements.

2. **Key Steps**:
   - **Selection of Tools/Tool Chains**: Decide whether to qualify individual tools or entire tool chains.
   - **Classification Analysis**: Determine the tool’s classification (TCL) based on its impact on safety.
   - **Plan Creation**: Develop an STQP outlining scope, objectives, and methodology for qualification.
   - **Documentation & Testing**: Gather evidence through testing, reviews, or vendor-provided kits to validate the tool’s compliance with ISO 26262.
   - **Reporting**: Compile findings in a qualification report.

3. **Responsibilities**:
   - Tool users are ultimately responsible for qualifying tools (vendors may provide support via certification kits).

For detailed methodology, refer to **ISO/DIS 26262-8** and its appendices. The process emphasizes traceability, evidence-based validation, and alignment with safety requirements.

---

*Note*: The context does not specify step-by-step procedural details beyond these work products; further guidance would require the full standard or supplementary guidelines.

---

## Retrieved Sources

### Source 1

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 10

practitioners with the necessary guidance to successfully utilize these tools in\
projects that need to comply with the requirements of ISO 26262. Until common best practices
have been established, the chosen qualification approach could be used as a reference for other
tool qualifications.
4 Summary and Conclusions\
With the advent of ISO 26262 automotive practitioners need to figure out how implement the
tool qualification requirements of this standard in practice.

### Source 2

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 5

the selecti on of the appropriate tool
qualification methods. Tool qualification can be carried out for individual tools as well as for
tool chains or sets of tools.
The ISO/DIS 26262 tool qualification process requires the creation of the following tool
qualification work products (ISO/DIS 26262-8, 11.5; see the appendix for a summary):
 Software Tool Qualification Plan
 Software Tool Documentation
 Software Tool Classification Analysis
 Software Tool Qualification Report
2.3 Software Tool Qualification Plan (STQP)
The software tool qualification plan is a planning document created in an early phase of the
development of the safety-related system.\
Besides stating the applicant, and the application under consideration, i t identifies the tool and
tool version to be qualified, the intended configuration and operational environment. In this
sense, the STQP shares conceptual similarities with tool qualification plans used in DO -178B
projects.
The tool

### Source 3

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 1

26262 in practice.
1 Tool Certification / Qualification Approaches in Standards and
Guidelines
This section is intended to provide an overview about the requirements in popular safety
standards and guidelines pertaining to qualifying or certifying software tools. The following
discussion should provide the context for a more detailed discussion of the ISO/DIS 26262 tool
qualification approach in sections 2 and 3.
So far, there is no single approach for tool qualification or certification across standards.
Rather, d ifferent standards attach different levels of importance to tool certification /
qualification and suggest different approaches to gain confidence in the tools used.\
Typically, tool users are responsible in the end for the certifying or qualifying the software
tools they are using. Tool vendors can support these efforts by providing certification or
qualification kits that ease the certification or qualification efforts on the user‘s side.\
The safety
