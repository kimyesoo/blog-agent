# Research Agent Architecture

이 문서는 Research Agent 단계에서 수집되는 데이터와 분석 기준을 정의합니다.

## 1. 최우선 원칙: Evidence Balance
콘텐츠는 단순히 법적 근거만을 찾는 것이 아니라, **실제 현장에서 어떻게 적용되는가(Field Practice)**에 맞추어 자료의 중요도를 동적으로 평가합니다. 이를 위해 모든 주제는 4가지 Archetype으로 분류됩니다.

### A. Regulatory Topics (규제/법령 중심)
- **대상**: 산업안전보건관리비, 하도급 규정, 품질관리계획 등
- **Evidence Weight**: Law(70) / Technical Standard(20) / Field Practice(10)

### B. Technical Standard Topics (설계/기술기준 중심)
- **대상**: 교량 설계, 흙막이, 포장공사 등
- **Evidence Weight**: Law(20) / Technical Standard(50) / Field Practice(30)

### C. Field Practice Topics (현장 실무 중심)
- **대상**: 들밀도 시험, 장비조합, 잔토처리 등
- **Evidence Weight**: Law(10) / Technical Standard(20) / Field Practice(70)

### D. Knowledge & Productivity Topics (지식/생산성 중심)
- **대상**: 공무 업무, 현장 문서 작성 등
- **Evidence Weight**: Law(0) / Technical Standard(10) / Field Practice(90)

## 2. Evidence Hierarchy (자료 출처 분류)
자료의 권위를 Archetype 가중치와 결합하여 다음 요소들로 평가합니다.
1. **Law / Legal Basis**: 현재 시행 법령
2. **Technical Standards**: 공식 기술기준 (KDS, KCS 등)
3. **Public Guidance**: 공공기관 지침/매뉴얼
4. **Field Practice**: 업계 실무 전문 자료, 개인 경험 및 블로그

## 3. Query Generation Strategy
- 주제의 Archetype이 `Regulatory`인 경우 법령 검색 비중을 높이고, `Field Practice`인 경우 실무 문제 해결 및 사례 검색 비중을 높입니다. 억지로 모든 주제에 법령 쿼리를 생성하지 않습니다.

## 4. Caching & Rate Limiting
- 동일 쿼리에 대한 반복적인 API 호출 방지를 위해 MD5 해싱 기반의 로컬 캐시(`research/cache/*.json`)를 사용합니다.
