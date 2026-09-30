# Topic Research Agent V2.1 Test Report

## 1. 실행 정보
- taxonomy version: 1.0
- generation date: 2026-09-30 00:53:40
- total categories: 16
- total subcategories: 143
- target candidates: 160

## 2. 생성 결과 (Quality-First)
- total generated: 273
- total accepted: 160
- total regenerated (duplicates): 3
- total discarded (quality filter): 110

## 3. 대분류별 분포
| Category | Candidates |
|---|---:|
| 토공 | 10 |
| 지반 및 토질 | 10 |
| 상하수도 | 10 |
| 도로 | 10 |
| 구조물 | 10 |
| 교량 | 10 |
| 터널 | 10 |
| 측량 | 10 |
| 품질관리 | 10 |
| 건설안전 | 10 |
| 건설공무 | 10 |
| 적산 및 공사비 | 10 |
| 건설기준 및 법규 | 10 |
| 환경 | 10 |
| 건설기계 및 장비 | 10 |
| 유지관리 | 10 |

## 4. Search Intent 분포
- 기준/규정: 25
- 사례: 18
- 현장 적용: 16
- 검토: 16
- 개념 이해: 14
- 점검/검사: 14
- 원인과 대책: 10
- 설계: 9
- 시공 방법: 9
- 문제 해결: 9
- 장비/자재: 7
- 비교: 5
- 계산/산정: 3
- 품질관리: 2
- 유지관리: 2
- 시험/측정: 1

## 5. Content Type 분포
- 기준 정리: 25
- 설계 검토: 25
- 실무 가이드: 23
- 문제 해결: 19
- 사례: 18
- 기초 설명: 14
- 체크리스트: 14
- 시공 가이드: 9
- 비교: 5
- 계산/산정: 3
- 품질관리: 2
- 유지관리: 2
- 시험/검사: 1

## 6. 품질 필터(Failures) 통계
- intent_mismatch: 110
- too_generic: 4
- duplicate_concept: 3

## 7. 대표 개선 사례 (Before vs After)
| Before | Problem | After |
|---|---|---|
| 재료비 현장 시공방법 및 실무 가이드 | intent_mismatch | 재료비 주요 수량 및 단가 산정 방법 |
| 교량형식 공사 중 주요 문제점 및 대책 | intent_mismatch | 교량형식 기본 설계 원리 및 검토사항 |
| 흙막이안전 핵심 품질관리 및 검사 기준 | intent_mismatch | 흙막이안전 현장 안전 및 시공 점검 체크리스트 |
| 발파 시험 방법 및 결과 해석 | intent_mismatch | 발파 주요 수량 및 단가 산정 방법 |
| 기초 시험 방법 및 결과 해석 | intent_mismatch | 기초 시공을 위한 주요 장비 조합 및 자재 기준 |
| 우수 시험 방법 및 결과 해석 | intent_mismatch | 우수 공법 비교 및 현장 선정 기준 |
| 관로시험 시설물 유지관리 및 보수보강 가이드 | intent_mismatch | 관로시험 기본 설계 원리 및 검토사항 |
| 도로 부속물 시설물 유지관리 및 보수보강 가이드 | intent_mismatch | 도로 부속물 주요 하자의 원인과 실무 대책 |

## 8. 대표 채택/거절 주제 샘플
### Accepted (자연스러운 주제)
- 잔토처리 최신 시공 및 설계 기준 정리 (Intent: 기준/규정, Score: 100)
- 성토 최신 시공 및 설계 기준 정리 (Intent: 기준/규정, Score: 100)
- 토공장비 기본 설계 원리 및 검토사항 (Intent: 설계, Score: 100)
- 다짐 최신 시공 및 설계 기준 정리 (Intent: 기준/규정, Score: 100)
- 흙막이 최신 시공 및 설계 기준 정리 (Intent: 기준/규정, Score: 100)
- 사토장 실무 현장 적용 가이드 (Intent: 현장 적용, Score: 100)
- 사면 시공 시공 전 필수 설계 검토사항 (Intent: 검토, Score: 100)
- 굴착 기초 개념과 실무 적용 이해 (Intent: 개념 이해, Score: 100)
- 잔토처리 현장 안전 및 시공 점검 체크리스트 (Intent: 점검/검사, Score: 100)
- 성토 현장 시공방법 및 실무 가이드 (Intent: 시공 방법, Score: 100)

### Known Issues & Next Steps
- **문제점**: 템플릿의 문장 구조가 여전히 약간 딱딱할 수 있으나, 의미적(Semantic) 충돌은 V2.1 로직으로 완벽히 통제됨.
- **개선사항 (V3.0)**: LLM을 도입하여 채택된 Concept (예: `흙막이 계산/산정`)를 바탕으로 동적으로 문장형 제목을 생성.
