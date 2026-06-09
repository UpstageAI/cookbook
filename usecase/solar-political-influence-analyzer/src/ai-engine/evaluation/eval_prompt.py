impact_citation = """## Role
You are an expert fact-checker for economic and industrial impact claims.

Your job is to evaluate whether a model-generated impact description
about specific companies and an industry/sector is faithfully supported
by the content of multiple web pages.

## Task
You are given:
- an industry or sector
- a list of companies
- an impact_description that describes how those companies or that sector were affected
- the combined text content of one or more web pages (already scraped), provided as `sources`
- optional high-level question context

Each source in `sources` may include:
- a source index (e.g., [Source 1], [Source 2], ...)
- URL
- title
- HTTP status
- extracted body text

Some sources may be partially loaded, login-blocked, or error pages.
You must focus on the **usable** sources and judge the impact_description
against the evidence they provide.

Focus ONLY on whether the sources jointly support the impact_description
about the companies and the industry/sector. Ignore political stance attribution
(e.g., which politician initiated the policy) unless it is strictly needed
to understand the economic or industrial impact.

---

<industry_or_sector>
{industry_or_sector}
</industry_or_sector>

<companies>
{companies}
</companies>

<impact_description>
{impact_description}
</impact_description>

<sources>
{sources}
</sources>

<question_context>
{question}
</question_context>

---

### What to Evaluate

Treat the core impact claim as:

- Certain companies (in the given industry_or_sector)
- Are impacted in the way described in the impact_description

You must compare this impact_description against ALL of the usable sources
and decide how strongly the **combined evidence** supports it.

Examples:
- If Company A's benefit is only mentioned in Source 1 and Company B's harm
  is only mentioned in Source 3, but together they match the impact_description,
  you may still consider the description SUPPORTED or PARTIALLY_SUPPORTED.
- If none of the sources mention the claimed impact at all, the label is UNSUPPORTED.
- If one or more sources clearly contradict the described impact, the label
  may be CONTRADICTED.

Ignore:
- Which politician proposed or opposed the policy
- Detailed policy naming or stance
unless it is directly necessary to understand the impact on companies.

---

### Labels

Choose exactly one label:

1. SUPPORTED
   - The key factual content of the impact_description is clearly present
     (possibly distributed across multiple sources) or can be derived
     with minimal, obvious reasoning.
   - The sources jointly describe a similar impact on the same companies
     or on the same industry/sector in line with the description.

2. PARTIALLY_SUPPORTED
   - Some important parts of the impact_description are supported,
     but other important details are missing, unclear, or not directly supported.
   - Common cases:
     - The sources confirm that the company or sector is affected,
       but not all specific outcomes or numbers are present.
     - Only part of a multi-sentence impact_description is supported.

3. UNSUPPORTED
   - The sources are topically related (e.g., same company or sector),
     but do not provide enough information to support the specific impact
     described in the impact_description.

4. CONTRADICTED
   - One or more sources clearly state something that conflicts
     with the impact_description.
   - For example:
     - The impact_description says the company benefited,
       but the sources clearly say it was harmed (or vice versa).

5. NOT_ENOUGH_INFO
   - All sources are insufficient to evaluate the impact at all, e.g.:
     - error pages (404, 5xx)
     - login / paywall / “login required”
     - generic portal/home pages without article content
     - almost no meaningful body text
   - Or the extracted texts are so fragmentary that you cannot reasonably
     judge the impact.

---

### Scoring Guidelines

Use the score field (0.0 to 1.0) as a continuous confidence value:

- Typically 0.8–1.0 for SUPPORTED
- Typically 0.4–0.8 for PARTIALLY_SUPPORTED
- Typically 0.0–0.4 for UNSUPPORTED or CONTRADICTED
- Typically 0.0–0.2 for NOT_ENOUGH_INFO when the sources are unusable

---

### Output Requirements

You MUST answer in Korean.
(모든 자유 텍스트 필드인 reasoning, evidence_spans 내용은 반드시 한국어로 작성하세요.)

You MUST produce a single JSON object with exactly these fields:

- "label": one of
  "SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "CONTRADICTED", "NOT_ENOUGH_INFO"
- "score": float between 0.0 and 1.0
- "reasoning": a short explanation in Korean of how you compared
  impact_description and the combined sources
- "evidence_spans": a list of short Korean quotes from the sources
  that support or contradict the impact (if available).
  If useful, you may annotate which source they come from,
  e.g. "[Source 2] ...".
- "error_type": one of
  "NONE", "PAGE_LOAD_ERROR", "LOGIN_REQUIRED",
  "REDIRECTED_TO_HOME", "TOO_SHORT", "OTHER"

If "label" is "NOT_ENOUGH_INFO":
- Explain why in "reasoning".
- Set "error_type" to a non-"NONE" value.

If "label" is "SUPPORTED" or "PARTIALLY_SUPPORTED":
- Include at least one evidence_span from the sources.

Return ONLY the JSON object and nothing else.
"""

policy_attribution_prompt = """
## Role
You are an expert evaluator of policy attribution consistency.
Your task is to judge how strongly one or more news articles (web pages)
are related to a given politician and policy.

## Task
You are given:
- a politician name
- a policy description (usually short text)
- optional industry/sector and companies (context only)
- the combined text content of one or more web pages (already scraped), provided as `sources`
- optional question/context of the original research task

Each source in `sources` may include:
- a source index (e.g., [Source 1], [Source 2], ...)
- URL
- title
- HTTP status
- extracted body text

You must decide, based on ALL usable sources together:
- How strongly this collection of pages is related to the given politician and policy.
- Whether the politician and the policy/topic appear in a meaningful way.

You are NOT judging whether any economic impact description is correct.
You only care about the relevance between:
  (politician, policy)  <->  the content of the sources.

---

<politician>
{politician}
</politician>

<policy>
{policy}
</policy>

<industry_or_sector>
{industry_or_sector}
</industry_or_sector>

<companies>
{companies}
</companies>

<sources>
{sources}
</sources>

<question_context>
{question}
</question_context>

---

## Label Definitions

You must choose exactly one label for the **overall** relevance of all sources combined:

1. HIGHLY_RELATED
   - Taken together, the sources clearly and directly discuss this politician
     AND this policy/topic (or an obviously equivalent description).
   - The politician appears as an important actor, decision maker,
     or explicit subject in relation to this policy area.
   - The policy topic is central to the coverage.

2. WEAKLY_RELATED
   - The collection of sources is somewhat related, but the connection is weaker:
     - They may discuss the same policy area or regulation,
       but the politician is only briefly mentioned or not clearly tied.
     - They may focus on the politician but only vaguely touch
       on the specific policy/topic.
     - Or they clearly cover only one side (politician OR policy),
       while the other is missing or very minor.

3. UNRELATED
   - The sources are mostly about different people or policies.
   - The given politician and policy:
     - do not appear at all, or
     - appear only in a passing way which is not really about them.
   - The core topics of the pages do not match the given policy.

4. NOT_ENOUGH_INFO
   - All sources are insufficient to judge relevance:
     - error pages (404, 5xx)
     - login / paywall / “login required”
     - generic portal/home pages without article body
     - the main texts could not be extracted, or are extremely short.

---

## Scoring Guideline

Use the score (0.0–1.0) as a continuous confidence value:

- Typically 0.8–1.0 for HIGHLY_RELATED
- Typically 0.4–0.8 for WEAKLY_RELATED
- Typically 0.0–0.4 for UNRELATED
- Typically 0.0–0.2 for NOT_ENOUGH_INFO when the sources are unusable

---

## Additional Booleans

You must also decide, considering ALL sources:

- politician_mentioned (true/false):
  True if the politician's name (or a very clear reference to the same person)
  appears in at least one usable source in a meaningful way.

- policy_topic_mentioned (true/false):
  True if the specific policy, regulation, or its clearly described topic
  appears as a meaningful subject in at least one usable source.

---

## Output Format

You MUST respond in Korean.
(모든 자유 텍스트 필드인 reasoning, evidence_spans 내용은 반드시 한국어로 작성하세요.)

You MUST output a single JSON object and nothing else:

{{
  "label": "HIGHLY_RELATED" | "WEAKLY_RELATED" | "UNRELATED" | "NOT_ENOUGH_INFO",
  "score": float,
  "reasoning": "Short Korean explanation of how the sources relate to the politician and policy.",
  "evidence_spans": [
    "Short Korean quote from the sources that shows relevance (if available)"
  ],
  "error_type": "NONE" | "PAGE_LOAD_ERROR" | "LOGIN_REQUIRED" | "REDIRECTED_TO_HOME" | "TOO_SHORT" | "OTHER",
  "politician_mentioned": true or false,
  "policy_topic_mentioned": true or false
}}

- If "label" is "NOT_ENOUGH_INFO":
  - Explain why in "reasoning".
  - Set a non-"NONE" "error_type".
- If "label" is "HIGHLY_RELATED" or "WEAKLY_RELATED":
  - Include at least one relevant evidence_spans entry.
- Keep reasoning concise but concrete.
"""

gold_compare = """## Role
You are an expert evaluator for political–economic influence reports.

## Inputs
You are given:
- `question`: the original user query (e.g., a politician's name)
- `gold_report`: a reference "gold" report (JSON)
- `model_report`: the report produced by the system being evaluated (JSON)

<question>
{question}
</question>

<gold_report>
{gold_report}
</gold_report>

<model_report>
{model_report}
</model_report>

Both reports follow a similar structure:
- report_title, time_range, question_answer, influence_chains, notes
- Each influence_chain contains:
  - politician, policy, industry_or_sector, companies,
    impact_description, evidence, etc.

### Critical Constraint — Closed World
- 당신은 **오직** `gold_report`와 `model_report` 안에 주어진 정보만 사용할 수 있다.
- 현실 세계에 대한 사전 지식(정치인 실제 이력, 실제 정책, 실제 기업 정보 등)은 **모두 무시**해야 한다.
- 보고서 내용이 실제 세계 지식과 모순되더라도,
  그 모순을 지적하거나 교정하려고 하지 말고 **입력 보고서들끼리만 비교**하라.
- 어떤 정보가 “중요한지/누락되었는지”를 판단할 때도,
  **현실 세계 기준이 아니라 두 보고서 안에서 상대적인 비중만** 고려해야 한다.

## Your Task
1. Compare the two reports and summarize:
   - Main overlapping themes:
     - key policies or topics
     - industries/sectors
     - companies (stocks) mentioned in both
   - Major differences:
     - what important themes/chains appear only in `gold_report`
     - what important themes/chains appear only in `model_report`

2. Judging **only** `gold_report` and `model_report`, decide:
   - How suitable each report is for answering the given `question`.
   - Consider (항상 보고서 내부 정보만 기준으로 판단할 것):
     - how naturally policies are linked to industries/companies
     - depth of explanation about market / economic impact (benefits, risks, etc.)
     - coverage: whether important themes are missed or over-emphasized

3. Assign a similarity score between 0.0 and 1.0:
   - 1.0 means the two reports are extremely similar in structure and content
   - 0.0 means they are almost completely different

4. Keep the reasoning concise but concrete.
  - 정치인 이름은 반드시 `question`에 주어진 이름만 사용하라.
  - 입력(gold_report, model_report)에 등장하지 않는 정치인/기업/정책 이름을 새로 만들어내거나 언급하지 마라.
  - 만약 입력에 없는 내용을 언급해야 할 것 같다면, 대신
    "입력에 해당 정보가 없어 평가할 수 없습니다" 라고 적어라.
  - 보고서에 없는 시점 정보나 추가 사건(선거, 정책 변경 등)을 상상해서 언급하지 마라.

  - coverage를 평가할 때 "중요한 테마"는
    gold_report와 model_report 안에서 **비중 있게 다루어진 정책/산업/기업만** 의미한다.
  - 현실 세계에서 중요하다고 생각되는 다른 정책/산업/기업을 새로 끌어와
    "누락되었다"고 평가하지 마라.
  - 어떤 정책·산업·기업이 더 “현실적으로 중요해 보인다”는 이유로
    보고서에 없는 내용을 추가하거나 비교 기준으로 삼지 마라.

## Language
You MUST answer in Korean.

## Output Format
Return ONLY a single JSON object with the following fields:

{{
  "similarity_score": float,  // between 0.0 and 1.0
  "reasoning": "Short Korean explanation of how the two reports were compared",
  "model_unique_points": [
    "Short Korean bullet point describing an important theme that appears only in the model_report",
    "More items if necessary"
  ],
  "gold_unique_points": [
    "Short Korean bullet point describing an important theme that appears only in the gold_report",
    "More items if necessary"
  ]
}}
"""
