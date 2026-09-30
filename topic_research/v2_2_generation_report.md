# Topic Research Agent V2.2 Test Report

## 1. 실행 정보
- taxonomy version: 1.0
- generation date: 2026-09-30 01:02:34
- total target candidates: 160

## 2. 생성 결과 요약
- total generated: 169
- total accepted: 160
- total regenerated (generic/duplicate): 7
- total discarded (low compatibility): 2

## 3. 핵심 무결성 검증 (Critical Integrity Goals)
- taxonomy_integrity_failures: 0
- known_duplicate_false_positive_cases: 0
- LOW compatibility topic 자동 통과: 0 (All discarded safely)

## 4. Compatibility 분포
- HIGH compatibility count: 5
- MEDIUM compatibility count: 162
- LOW compatibility count: 2

## 5. 주요 개선 사항 (Representative Changes)
- **최신 남용 금지**: `잔토처리 최신 시공 및 설계 기준 정리` -> `잔토처리 적용 기준`
- **혼합 의도 단일화**: `시공 및 설계 기준 정리` 분리 및 단순화.
- **시험/측정 오분류 구제**: `발파 시험/측정` -> 정상 통과.
- **중복 회피 개선**: `들밀도 시험 방법`, `들밀도 시험 계산` 등 기술 핵심은 같으나 의도가 다르면 별도 Topic으로 허용.
