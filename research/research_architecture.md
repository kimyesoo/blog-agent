# Research Agent Architecture

이 문서는 Research Agent 단계에서 수집되는 데이터와 분석 기준을 정의합니다.

## 1. Source Classification (자료 출처 분류)
자료의 권위(Authority)를 동일 선상에 두지 않고 다음 4가지로 계층화합니다:
- **Official (very_high/high)**: 국가건설기준(KCS/KDS), 법령, 조달청, 국토부 지침 등
- **Academic (medium)**: 국책연구기관, 대학 논문, 연구보고서
- **Industry (medium)**: PDF 매뉴얼, 건설업계 실무 자료
- **Blog/Community (low)**: 티스토리, 네이버 블로그 등 개인 경험 자료

## 2. Research Readiness
`Research Readiness`는 해당 토픽이 '작성하기 좋은 상태인가'를 나타냅니다. 검색량이나 SEO 트래픽 점수가 아닙니다.
- **HIGH**: 실제 검색 결과가 존재하며, 공식 자료(Official)와 실무 자료(Blog)가 모두 확보되어 팩트체크가 용이한 상태.
- **MEDIUM**: 검색 결과는 존재하나 공식 기술 자료가 다소 부족한 상태.
- **LOW**: 검색 결과 자체가 부족하거나, 구체적인 실무 의도가 파악되지 않아 리서치가 어려운 상태.

## 3. Query Generation Strategy
V2.2에서 도출된 `Technical Core`와 `Search Intent`를 활용하여 검색어를 다각화합니다.
- 예: `토공장비` + `문제 해결` -> ["토공장비 문제점", "토공장비 시공 문제", "토공장비 대책"]
이 전략을 통해 하나의 제목으로 검색하는 것보다 입체적인 자료 수집이 가능해집니다.

## 4. Caching & Rate Limiting
- 동일 쿼리에 대한 반복적인 API 호출 방지를 위해 MD5 해싱 기반의 로컬 캐시(`research/cache/*.json`)를 사용합니다.
- `.gitignore`에 처리되어 원격 저장소에 캐시가 적재되는 것을 방지합니다.
