# Problem Discovery & Validation V2.1 Report

## IMPLEMENTATION_STATUS
**PASS**

## CHANGES
1. **Problem Origin Tracking**: Introduced `problem_origin` (`source_derived`, `ai_inferred`, `taxonomy_fallback`) to explicitly separate actual field problems from AI extrapolations and theoretical fallbacks.
2. **Evidence Confidence Logic**: Re-engineered `evidence_confidence` to calculate mathematically based on the mix of `professional_field_blog`, `legal`, `technical_standard`, and `public_agency` sources, scaling from `high` to `very_low`.
3. **Source Structure Revamp**: Shifted `discovery_sources` from a simple string list to an array of objects detailing `source`, `source_type`, `source_role` (e.g., `problem_discovery` vs `official_support`), and `relevance`.
4. **Theoretical Problem Rejection**: Stripped `theoretical` from being a valid field problem type, moving it directly to the rejection pipeline to maintain practical blog value.
5. **Deduplication Refinement**: Differentiated duplicate logic to output `merge` for identical concepts (e.g. 다짐도 미달 / 다짐도 안 나옴) and `needs_review` for highly similar but nuanced administrative differences (e.g. P-0002 / P-0007).

## PROBLEM_ORIGIN_RULE
* `source_derived`: Actively extracted from real-world documents or blogs (e.g., civileng7.tistory.com).
* `ai_inferred`: Extrapolated field situations without explicit source backing, flagged with `low` confidence.
* `taxonomy_fallback`: Generic theoretical generation strictly used when no field problem exists, typically flagged for `reject`.

## EVIDENCE_CONFIDENCE_RULE
* **high**: Supported by both practical field sources (`professional_field_blog`) AND official/legal sources (`legal`, `technical_standard`, `public_agency`).
* **medium**: Supported by either practical field sources OR official sources, but not both.
* **low**: AI inferred or lacks concrete documentation.
* **very_low**: Purely taxonomical fallback or unsupported theoretical question.

## PROBLEM_TYPE_RULE
Valid types reflect situational contexts: `quality_problem`, `contract_problem`, `supervision_response`, `material_problem`, `test_result_problem`, `site_condition_change`, `complaint_problem`, `equipment_problem`, `administrative_problem`, `safety_problem`, `construction_problem`.
`theoretical` is explicitly used as a flag to reject generic educational content.

## PROBLEM_VS_TOPIC_RULE
The Problem Validation Agent exclusively deals with situational definitions (the Problem). The Topic Agent independently converts these situations into search-friendly content titles using heuristic formatting to enforce a 1:N relationship (e.g., "다짐도 미달" becomes "다짐도 미달 시 원인 분석 및 현장 조치방법").

## SCORING_RULE
* `practical_value`: Evaluates the urgency and applicability of the field situation based on situational keywords ("미달", "변경", "요구" = +10).
* `searchability`: A heuristic score representing the *suitability of the expression as a search term*, **NOT** an actual search volume metric.
* `recurrence_signal`: Boosted if supported by public audits or broad official guidelines implying widespread occurrence.

## VALIDATION_RULE
* `keep`: PV >= 60, clear practical value and distinct situational context.
* `needs_review`: 45 <= PV < 60, or highly similar to an existing concept requiring nuanced administrative differentiation.
* `merge`: Conceptually identical field situation to a previously kept problem.
* `reject`: PV < 45, or origin is a `taxonomy_fallback` tagged as `theoretical`.

## TEST_RESULTS
All 8 rigorous unit tests passed successfully, correctly identifying source-derived problems, mixing official+practical sources for `high` confidence, parsing administrative issues, rejecting theoretical topics, merging duplicates, flagging similar nuances, and strictly separating taxonomy fallback / AI inference.

## 20_30_CASE_SAMPLE_RESULTS
Ran against a sample of 20 deterministic scenarios:
* **Processed**: 20 candidates
* **Kept**: 9
* **Needs Review**: 5
* **Merged**: 2
* **Rejected**: 4 (Theoretical/Taxonomy fallbacks)

## MERGE_RESULTS
* `P-0006 (다짐도가 안 나오는 경우)` successfully merged into `P-0001 (현장 다짐도가 기준에 미달)`.
* `P-0018 (터파기 중 설계와 다른 암반층 노출)` successfully merged into `P-0013 (굴착 중 설계에 없는 대규모 암반 발견)`.

## SOURCE_DERIVED_EXAMPLES
* `P-0010 (콘크리트 압축강도 시험 결과 기준 미달)`: Sourced from `civileng7` and `kcsc.re.kr`. CONF: `high`.
* `P-0016 (강풍 시 타워크레인 작업 중지 기준)`: Sourced from `law.go.kr`. CONF: `medium`.

## AI_INFERRED_EXAMPLES
* `P-0008 (연약지반 성토 중 원인 불명의 급격한 침하 발생)`: Plausible field situation but lacks direct sourcing. PV: `60`, CONF: `low`.
* `P-0020 (우기 시 흙막이 배면 지표수 유입으로 인한 토압 증가)`: Plausible. PV: `60`, CONF: `low`.

## TAXONOMY_FALLBACK_EXAMPLES
* `P-0004 (흙의 압밀 기본 원리)`: Fallback generation.
* `P-0017 (흙의 종류)`: Fallback generation.

## REJECTED_THEORETICAL_EXAMPLES
* `P-0005 (발파 기본 설계 원리)`: Penalized by educational keyword detection. PV: `0`, CONF: `very_low`, DECISION: `reject`.
* `P-0009 (토공의 기본 개념)`: Penalized by educational keyword detection. PV: `0`, CONF: `very_low`, DECISION: `reject`.

## LIMITATIONS
* **Searchability**: Still purely a heuristic keyword fit score. It is not actual SERP search volume.
* **Semantic Deduplication**: The AI inference duplicate check (e.g. distinguishing P-0002 from P-0007) is currently mocked via string inclusion logic. True semantic distinction requires an LLM pass to fully realize the "Canonical Problem vs Variant" architecture.

## NEXT_STEP
Transition to designing the Research Pack system. This system will ingest a `kept` Problem, consume its `discovery_sources`, run targeted SERP queries if confidence is below `high`, and explicitly map `official_support` against `professional_field_blog` sources to expose conflicts and procedural gaps for the Writer Agent.
