# Research Agent Architecture

이 문서는 Research Agent 단계에서 수집되는 데이터와 분석 기준을 정의합니다.

## 1. 최우선 원칙: Practical Value First (실무적 가치 최우선)
콘텐츠는 단순히 법적 근거만을 찾는 것이 아니라, **실제 현장에서 어떻게 적용되고 어떤 문제를 해결하는가(Field Practice & Problem Solving)**에 맞추어 자료의 중요도를 동적으로 평가합니다.

엔지니어의 실제 탐색 흐름 (원인 -> 해결책 -> 기준 -> 법적 근거)을 모방하도록 시스템을 설계합니다.

## 2. Topic-Based Evidence Prioritization (4대 Archetypes)

### A. Field Problem Solving Topics (현장 문제 해결)
- **대상**: 함수비 시험, 들밀도 시험, 관부설, 흙막이, 발파, 실정보고 등
- **Evidence Weight**: Field Practice(50) / Technical Standard(30) / Public Guidance(15) / Law(5)

### B. Construction Methods & Execution (시공 방법 및 수행)
- **대상**: 시공순서, 공법 비교, 장비 선정, 품질 문제, 현장 문제 해결 등
- **Evidence Weight**: Field Practice(45) / Technical Standard(35) / Public Guidance(15) / Law(5)

### C. Technical Standard Topics (기술 기준 중심)
- **대상**: KDS 적용, KCS 적용, 설계 기준, 구조 기준 등
- **Evidence Weight**: Technical Standard(50) / Field Practice(30) / Public Guidance(10) / Law(10)

### D. Regulatory Topics (규제/법령 중심)
- **대상**: 산업안전보건관리비, 하도급, 품질관리계획, 건설기술진흥법 등
- **Evidence Weight**: Law(50) / Public Guidance(25) / Technical Standard(15) / Field Practice(10)

## 3. Evidence Hierarchy (자료 출처 분류)
자료의 권위를 Archetype 가중치와 결합하여 다음 요소들로 평가합니다.
1. **Field Practice**: 업계 실무 전문 자료, 개인 경험, 시공 사례 및 블로그 (대다수 토픽의 최우선 근거)
2. **Technical Standards**: 공식 기술기준 (KDS, KCS 등)
3. **Public Guidance**: 공공기관 지침/매뉴얼
4. **Law / Legal Basis**: 현재 시행 법령 (필요한 경우에 한정)

## 4. Query Generation Strategy
- 주제의 Archetype이 `Field Problem Solving`이나 `Construction Methods`인 경우 실무 문제 해결, 장비 조합, 하자 원인 등의 검색 비중을 높입니다. 억지로 모든 주제에 법령 쿼리를 생성하지 않습니다.

## 5. Caching & Rate Limiting
- 동일 쿼리에 대한 반복적인 API 호출 방지를 위해 MD5 해싱 기반의 로컬 캐시(`research/cache/*.json`)를 사용합니다.
