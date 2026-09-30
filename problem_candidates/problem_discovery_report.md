# Problem Discovery & Validation V2.1.1 Report

## 1. 변경 내용
V2.1.1 보정 작업은 AI 추론 문제(`ai_inferred`)가 실제 검증된 현장 문제로 오인되는 것을 방지하고, 근거가 탄탄한(`high`) 실제 문제(`source_derived`)가 단순한 발견 점수(PV)로 인해 불필요하게 탈락(`needs_review`)하는 현상을 교정했습니다.

## 2. ai_inferred 처리 규칙
* AI가 기술적으로 유추한 문제(`ai_inferred`)는 실무 가치(PV)가 아무리 높아도 자동 `keep` 하지 않습니다.
* 기본값으로 `needs_review`를 부여하여 실제 현장 사례 확인 단계로 이관합니다.

## 3. source_derived 승격 규칙
* 실제 전문 블로그, 공공기관 자료 등 현장 출처가 확인된 문제만이 `source_derived` 라벨을 얻을 수 있습니다.
* `ai_inferred` 문제라도 추후 실제 출처가 확인되면 `source_derived`로 승격되고 `keep` 가능해집니다.
* `taxonomy_fallback`은 여전히 실무성이 부족하므로 기본적으로 `reject`를 유지합니다.

## 4. evidence_confidence 처리 규칙
* `problem_origin`과 `evidence_confidence`는 독립적입니다. AI가 아무리 멋진 문제를 추론했어도 출처가 없으면 `low`이며, `high`는 실제 공공 기준(`legal`, `technical_standard` 등)과 전문 실무(`professional_field_blog`) 양쪽이 교차 검증될 때만 부여됩니다.

## 5. high evidence 문제의 decision 규칙
* 출처가 탄탄한(`high` evidence) 실제 현장 문제(`source_derived`)의 경우, 검색성 휴리스틱 점수(PV)가 애매한 55점 구간에 걸려 있더라도 무조건 `needs_review`로 강등하지 않고 `keep` 하여 실무 정보 제공을 우선시합니다.

## 6. 중복 Problem 처리 규칙
* 완전히 동일한 상황(예: "다짐도가 기준에 미달" / "다짐도가 안 나오는 경우")은 `merge` 합니다.
* 그러나 세부 맥락의 차이로 인해 Topic 다양성이 확보될 수 있는 경우(예: P-0013 "대규모 암반 발견" / P-0018 "암반층 노출")는 무조건 `merge`로 파괴하지 않고 `needs_review`를 부여하여 다중 Topic 파생을 열어둡니다.

## 7. 기존 20개 샘플의 변경 전/후 결과
* **P-0008** (연약지반 급격한 침하): `keep` → **`needs_review`** (ai_inferred 방어)
* **P-0014** (타워크레인 지지력 부족): `keep` → **`needs_review`** (ai_inferred 방어)
* **P-0020** (흙막이 배면 지표수 유입): `keep` → **`needs_review`** (ai_inferred 방어)
* **P-0019** (아스팔트 조기 포트홀): `needs_review` → **`keep`** (high evidence 구제)

## 8. Decision 분포 (20 샘플 기준)
* **Keep**: 8
* **Needs Review**: 7
* **Merge**: 1
* **Reject**: 4

## 9. Problem Origin 분포
* `source_derived`: 13
* `ai_inferred`: 3
* `taxonomy_fallback`: 4

## 10. Evidence Confidence 분포
* `high`: 4
* `medium`: 7
* `low`: 5
* `very_low`: 4

## 11. 테스트 결과
8개의 신규 단위 테스트 및 기존 로직 방어 테스트를 모두 통과하여(`OK`), 독립적인 계산과 분기 처리의 안전성을 입증했습니다.

## 12. 남은 한계
* **Topic 다양성 자동화 한계**: 현재 Heuristic Rule에 의해 P-0018이 `needs_review`로 분리되었으나, 이를 실제 서로 다른 유용한 Topic으로 매끄럽게 자동 분기시키기 위해서는 NLP 처리나 LLM의 개입이 요구됩니다.
* **Searchability**: 여전히 실제 검색량이 아닌 표현 적합성 휴리스틱입니다.
