# Research Agent Architecture

이 문서는 Research Agent 단계에서 수집되는 데이터와 분석 기준을 정의합니다.

## 1. 최우선 원칙: 법령 중심 Research
블로그 검색결과보다 **법적·기술적 근거 체계를 우선적으로 확인**합니다. 법령을 글의 마지막 참고자료로 붙이는 것이 아니라 Research의 출발점 중 하나로 사용합니다.
- 관련 법령 유무 조사 -> KDS/KCS 확인 -> 공공기관 자료 -> 일반 검색 순으로 진행합니다.

## 2. Evidence Hierarchy (자료 출처 분류)
자료의 권위를 하나의 점수로 뭉뚱그리지 않고 다음 계층으로 엄격히 분리하여 저장합니다.
1. **Legal Basis**: 현재 시행 법령 (법률, 시행령, 시행규칙, 고시)
2. **Technical Standards**: 공식 기술기준 (KDS, KCS 등)
3. **Official Guidelines**: 국토부, 조달청 등 공공기관 공식 지침/매뉴얼
4. **Academic/Research**: 국책연구기관, 학술 자료
5. **Industry**: 업계 실무 전문 자료
6. **Blog/Community**: 개인 경험 및 블로그

## 3. Legal Relevance (법적 관련성)
모든 토픽이 법령을 강제로 가지지 않습니다.
- `direct`: 법령이 해당 업무를 직접 규정.
- `indirect`: 법령과 관련되나 세부 기술사항은 KDS/KCS에 존재.
- `contextual`: 법적 배경은 있으나 기술적 내용이 핵심.
- `none`: 직접적인 법적 근거가 없음 (명확히 '없음'으로 기록).
- `unknown`: 확인 불가.

## 4. Query Generation Strategy
- **General Queries**: 일반적인 실무 검색어 ("토공장비 문제점")
- **Legal Queries**: 법령/기준 전용 검색어 ("토공장비 관련 법령", "산업안전보건법 흙막이")

## 5. Conflict Resolution
법령과 일반 검색 결과(블로그 등)의 내용이 충돌할 경우 `legal_conflict_detected = true`로 마킹하여, 후속 Fact Check Agent가 이를 해결하도록 위임합니다.
