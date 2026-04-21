# FairSight — Problem Statement

## Hackathon: Solution Challenge 2026 India — Build with AI
## Theme: Unbiased AI Decision
## Team: FairSight

---

## Problem Title

**Ensuring Fairness and Detecting Bias in Automated AI Decisions**

---

## Problem Description

Computer programs now make life-changing decisions about who gets a job, a bank loan, or even
medical care. These systems learn patterns from historical data — but historical data reflects
decades of human prejudice. The result: AI that systematically discriminates against people
based on race, gender, age, or socioeconomic status, often invisibly and at scale.

### Concrete Examples of the Crisis

**Criminal Justice:** The COMPAS recidivism algorithm, used in US courts to predict likelihood of
reoffending, was found to falsely flag Black defendants as future criminals at nearly twice the
rate of White defendants (ProPublica, 2016). Judges used these scores to set bail and sentence
lengths — real people lost their freedom due to a biased algorithm.

**Employment:** A 2024 University of Washington study found AI résumé screening tools favored
White-associated names 85% of the time. Black male-associated names were never preferred over
their White counterparts — even for identical qualifications.

**Healthcare:** AI algorithms used to allocate healthcare resources used "historical cost" as a
proxy for medical need. Because Black patients historically received less care (due to systemic
barriers), the algorithm interpreted them as "lower need" — denying care to those who needed
it most.

**Lending:** AI credit scoring models trained on historical data have been shown to deny loans
to qualified minority applicants at significantly higher rates, deepening generational wealth gaps.

---

## Why This Problem Is Hard

### 1. Bias is invisible without measurement
A model can have 90% accuracy overall while systematically failing one demographic group.
Without explicit fairness metrics computed per group, organizations never see the problem.

### 2. Historical data encodes discrimination
Data collected over decades reflects human bias — who got hired, who got approved, who got
surveilled. Training on this data without correction teaches the model to replicate that bias.

### 3. There is no single definition of fairness
Demographic Parity (equal outcome rates), Equalized Odds (equal error rates), and Individual
Fairness (similar people treated similarly) can mathematically conflict with each other.
Organizations need guidance on which metric applies to their context.

### 4. Mitigation is not straightforward
Simply removing race or gender from the dataset doesn't work — other features (zip code,
school name, income history) act as proxies. True debiasing requires systematic intervention
at the data, model, and decision threshold levels.

### 5. No accessible tooling for non-ML teams
Existing fairness libraries (AIF360, Fairlearn) require deep ML expertise. Legal, HR, and
product teams who make deployment decisions cannot use them — creating a critical gap between
those who understand bias and those who control deployment.

---

## Scale of Impact

- 98.4% of Fortune 500 companies use AI in hiring (Brookings, 2024)
- 36% of companies reported direct negative impacts from AI bias in 2024 (DataRobot)
- AI bias disproportionately affects 4+ billion people in protected demographic categories globally
- The EU AI Act (2024) now legally requires bias audits for high-risk AI systems

---

## The Gap We Are Filling

There is currently no **accessible, end-to-end platform** that allows organizations to:
1. Upload a dataset or model predictions
2. Automatically detect bias across multiple demographic attributes
3. Receive plain-English explanations of what is wrong and why
4. Apply and compare mitigation strategies
5. Generate an audit report suitable for legal, executive, and regulatory review

FairSight fills this gap.

---

## Target Users

| User | Need |
|------|------|
| HR departments | Audit hiring algorithms before deployment |
| Banks & lenders | Comply with ECOA and fair lending laws |
| Hospitals | Ensure medical AI doesn't discriminate by race/SES |
| Governments | Audit criminal justice and benefits algorithms |
| AI developers | Test models for fairness during development |
| Regulators | Independent audit trail for AI systems |
