# RAG Query Export

**Date:** 2026-06-30 20:59:56  
**Model:** `Ollama:gemma4:31b`

---

## Query

Create a Tool Qualification Process Report for lcov according to ISO 26262  based on the gcc toolchain analysis input.

---

## AI Response

Based on the provided context, a complete Software Tool Qualification Report (STQR) cannot be fully generated because the documents do not provide evidence that the qualification was carried out as planned, nor do they list identified malfunctions or usage constraints. 

However, using the "Analysis of lcov" section and the ISO 26262 requirements described in the text, the following information can be compiled:

### **Tool Qualification Information for lcov**

**1. Tool Identification**
*   **Tool Name:** lcov
*   **Version:** 1.14
*   **Vendor:** Open source (maintained using GPL 2 License)
*   **Function:** A graphical front-end used to display coverage data provided by gcov in HTML format.

**2. Functional Capabilities**
The tool provides measurement for the following:
*   Statement coverage
*   Function coverage
*   Branch coverage
*   Modified Condition/Decision Coverage (MC/DC)

**3. Specific Technical Requirements/Features**
*   **Branch Coverage:** Provides branch coverage information along with MC/DC, including total counts of branches in source code and the number of branches covered/executed.
*   **Function Coverage:** Indicates if a function has been executed, providing total counts of functions versus those covered/executed.
*   **ASIL Configuration:** Allows the configuration of legend ratings based on user requirements and ASIL requirements, if applicable.
*   **Error Identification:** Explicitly indicates uncovered statements in the code.
*   **Execution Tracking:** Provides the number of times each line in the code was executed.
*   **Navigation:** Includes overview pages for easy navigation within the file structure and across subdirectories for summary reports.

**4. Missing Information (Required for ISO 26262 STQR)**
According to section 2.6 of the provided text, a Software Tool Qualification Report must also include the following, which are **not found** in the documents:
*   Evidence that the tool qualification was carried out as planned.
*   Documentation of usage constraints.
*   Documentation of any malfunctions identified during the qualification process.

---

## Retrieved Sources

### Source 1

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 8

various standards , TÜV SÜD Automotive  GmbH was chosen for the tool qualification 
assessment.  
Due to their large customer base, MathWorks supports customers developing high -integrity 
systems according to different standards.  Tool certification packages for IEC 61508 and 
qualification kits for DO -178B were already productized when the ISO 26262 qualification 
activities were launched. So it was desirable to re -use certification  / qualification approaches 
and artifacts developed for these other standards wherever feasible.  
A suitable way to leverage existing certification approaches was to add the ISO 26262 tool 
qualification on top of the existing IEC 61508 in-context tool certifications. These existing 
certifications are based on specific workflows (reference workflows ) to be utilized by the 
applicant when using the tool for developing or verifying software for IEC 61508 applications. 
In the context of ISO 26262 tool qualification, these workflows can be re -used to

### Source 2

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 7

method recommended; ++ … method highly recommended) 
The selected tool qualification methods to be carried out need to be documented in the STQP. 
2.6 Software Tool Qualification Report (STQR) 
The software tool qualification reports documents the actual tool qualification, i.e. provides 
evidence that the tool qualification was carried out as planned . Usage constrain ts and 
malfunctions identified during the qualification, if any, shall be documented here as well. 
3 Experiences with tool qualification according to ISO/DIS 26262 -   
A practitioner’s perspective 
MathWorks automotive industry customers have expressed thei r need for compliance with the 
upcoming ISO 26262 standard [TMW09] and for tools qualified as per ISO 26262 in particular. 
In order to support this customer need, a practicable ISO 26262 tool qualification approach had 
to be developed and implemented.  
In this section the authors discuss their first hand experiences with the ISO/DIS 26262 tool 
qualification

### Source 3

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
development of the safety-related system.  
Besides stating the applicant, and the application under consideration, i t identifies the tool and 
tool version to be qualified, the intended  configuration and operational environment. In this 
sense, the STQP shares conceptual similarities with tool qualification plans used in DO -178B 
projects. 
The tool

### Source 4

- **File:** ISO-26262-Test-Tool-Qualification-Technical-Briefing-v2.0.pdf
- **Page / Chunk:** 7

LDRA Ltd ISO 26262 Test tool qualification for automotive applications
Conclusions
“Tool qualification” is a generic term to describe a process designed to ensure that the risk of a tool error 
impacting the safety of a system is acceptably low – either because the errors are few, or because they 
cannot impact safety. Most functional safety standards including ISO 26262 define processes to achieve 
tool qualification by considering the application of the tool, and the environment in which it is deployed. 
ISO 26262 states that for most ASILs using tools that evidence of acceptable assessment (usually 
TÜV certification) will be sufficient reassurance that they are fit for purpose. But the fact that the most 
critical automotive applications demand tool qualification in the context of the nominated development 
environment suggests that there is potential benefit to adopting a similar approach even for less critical 
applications.
Many vendors including LDRA provide a collection of

### Source 5

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
element being developed; and the confidence in preventing or detecting such errors in its corresponding 
output.” 
The LDRA tool suite is classified as a TI2 (Tool Impact - 2) category tool because although a verification tool

### Source 6

- **File:** ISO-26262-Test-Tool-Qualification-Technical-Briefing-v2.0.pdf
- **Page / Chunk:** 2

provides this level of confidence for some or all of its functionality. However the classification 
and qualification methods differ in some details.
Unlike other IEC 61508 [1] derived standards that also demand a similar level of qualification (Figure 1), the 
ISO 26262 “Road vehicles - Functional safety” standard [2] prescribes a detailed process for that purpose. 
This paper discusses that process as it relates to the automotive industry, and references the LDRA tool 
suite [3] as an example. The LDRA tool suite is an integrated collection of requirements traceability tools, 
and static and dynamic analysis tools for verification and validation. 
Figure 1: Most functional safety standards are direct derivatives of IEC 61508 –  
that is, part of the “IEC 61058 family”
With the shortfall in advice offered by other standards in mind, the LDRA paper “Test tool qualification for 
functional safety” discusses in more detail how the tool qualification processes laid out in ISO 26262

### Source 7

- **File:** ISO-26262 Tool-Qualification-Process.pdf
- **Page / Chunk:** 1

Qualifying Software Tools According to ISO 26262 
 
Mirko Conrad1, Patrick Munier2, Frank Rauch3 
 
1 The MathWorks, Inc.,  
Natick, MA, USA 
mirko.conrad@mathworks.com 
2 The MathWorks, SAS,  
Grenoble, France 
patrick.munier@mathworks.fr 
3 TÜV SÜD Automotive GmbH 
Munich, Germany 
frank.rauch@tuev-sued.de 
 
Abstract:  
The growing adoption of safety standards in the automotive industry results in an 
increasing interest in as well as an increasing uncertainty about software tool 
certification and qualification. With ISO 26262 on the horizon, new tool qualification 
requirements need to be understood and implemented by automotive software 
practitioners. 
This paper summarizes the tool qualification approach of ISO /DIS 26262 and 
contrasts it with tool certification and qualification requirements outlined  in other 
safety standards and guidelines. The authors also report about their first -hand 
experiences with qualifying development and verification tools according to ISO/DIS

### Source 8

- **File:** ISO-26262-Test-Tool-Qualification-Technical-Briefing-v2.0.pdf
- **Page / Chunk:** 4

that evidence can be provided that a suitable 
software development process has been applied (highly recommended for ASIL A-C only). 
• Development in accordance with a safety standard  where the development of the tool itself complies 
with a safety standard (highly recommended for ASIL D).
TÜV certification
The second of these alternatives, the evaluation of the tool development process, provides a path followed 
by many to dramatically reduce the overhead involved with the tool qualification process. 
 
Figure 4: TÜV certification for LDRA tools
LDRA Ltd ISO 26262 Test tool qualification for automotive applications
4

### Source 9

- **File:** toolchain-analysis_Share_Input.docx
- **Page / Chunk:** [76, 77, 78, 79, 80, 81]

lcov shall provide branch coverage information along with Modified Condition/Decision Coverage. The report gives total count of the number of branches in the source code under test and how many branches are covered/executed.

lcov shall provide function coverage information which indicates whether a function in the source code under test has been executed. The report gives the total count of the number of functions in the source code and the count of functions covered/executed.

lcov shall allow to configure the legend rating as per user requirements. The percentage levels shall be configured as per ASIL requirements if applicable.

Coverage report generated by lcov shall indicate the uncovered statements in the code explicitly.

lcov report shall provide that how many number of times each line in the code got executed.

lcov shall add overview pages for easy navigation within the file structure and shall easily navigate across the subdirectory for the summary report.

### Source 10

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
