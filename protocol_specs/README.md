# Protocol spec pages

Interactive, executable specifications built from a clinical study protocol alone, with no SAP and no study results. Each page is a single self-contained HTML file; open it in a browser.

| Page | Study | Therapeutic area |
|---|---|---|
| `dapa-hf.html` | DAPA-HF, NCT03036124 (protocol v2.0) | Heart failure, event-driven outcome trial |
| `destiny-breast03.html` | DESTINY-Breast03, NCT03529110 (protocol v6.0) | HER2+ metastatic breast cancer, RECIST 1.1 |

## What each page contains

- **Estimands** structured per ICH E9(R1), linked to source data, ADaM parameters, derivation rules and output table shells.
- **Derivation rules as code** (censoring, recurrent events, RECIST 1.1 timepoint and confirmed best response, PFS, DoR, OS), each with unit tests that run in the page.
- **Randomized stress tests** of the derivation rules (thousands of generated cases per rule, checked against invariants).
- **Design simulator** that recomputes sample size, power, alpha spending and analysis timing from the protocol's assumptions.
- **Dry run** on mock data generated from design assumptions: derives ADTTE from the spec's own rules and fits the protocol's model. Used to build and validate programs before unblinding.
- **Dependency graph** from protocol objective to output, with impact computed by walking the links.
- **CDISC Biomedical Concepts** (oncology page): concepts, data element concepts and SDTM dataset specializations from CDISC COSMoS, with library coverage gaps listed.
- **Open decisions** (DAPA-HF page): every rule the protocol leaves undecided is a numbered decision with alternatives. Decisions marked "drives code" feed the derivations, so changing one updates the tests, dry run and checks.

## Running the checks headlessly

```bash
npm install jsdom@24
node protocol_specs/tests/run_checks.js protocol_specs/dapa-hf.html
node protocol_specs/tests/run_checks.js protocol_specs/destiny-breast03.html
```

The runner exits non-zero if any spec check fails or a page script throws.

## Sources and data

- Protocols: ClinicalTrials.gov large documents for NCT03036124 and NCT03529110.
- `data/cdisc_bc_destiny_breast03.json`: subset of the CDISC COSMoS Biomedical Concepts export (MIT License, Copyright (c) 2022 CDISC), https://github.com/cdisc-org/COSMoS. The same data is embedded in `destiny-breast03.html`.
- Rules not stated in a protocol are labelled as assumptions on the page; they follow common practice and must be confirmed in the study SAP.
- Code snippets are illustrative and are not any sponsor's programs.
