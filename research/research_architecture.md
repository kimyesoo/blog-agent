# Research Agent Architecture

이 문서는 Research Agent 단계에서 수집되는 데이터와 분석 기준을 정의합니다.

## 1. 최우선 원칙: Practical Value First (실무 문제 해결 최우선)
콘텐츠는 "정의 -> 이론 -> 규정 -> 결론"과 같은 학술적 순서를 지양합니다. 엔지니어의 실제 탐색 흐름인 **"문제 -> 즉각적 답변 -> 실무 해결책 -> 현장 적용 -> 뒷받침되는 기준 -> 주의사항"**의 순서로 콘텐츠가 조립될 수 있도록 Data를 수집하고 가중치를 부여합니다.

## 2. Configurable Evidence Weighting (동적 가중치 시스템)
Evidence Weight는 코드에 하드코딩되지 않고 `weights.json`을 통해 관리됩니다. 이를 통해 운영자는 코드 변경 없이 시스템 성격을 바꿀 수 있습니다.

- **practical_blog (기본)**: 실무 문제 해결(40%), 현장 적용(30%) 중심. 법률/기준은 보조적.
- **balanced**: 실무(30%)와 기술/법률(40%)의 균형.
- **technical_reference**: 기술/설계 기준(40%)과 법률(30%) 중심.
- **regulation_focus**: 법률(50%)과 기술기준(30%) 등 규제 중심.

## 3. Topic Archetypes (4대 토픽 유형)
토픽의 성격 자체는 변하지 않으나, 어떤 프로필(`weights.json`)이 선택되느냐에 따라 최우선으로 수집해야 할 자료의 비율이 변경됩니다.
- **A. Field Problem Solving**: 함수비 시험, 들밀도, 관부설 등 현장 트러블슈팅.
- **B. Construction Methods**: 시공순서, 공법 비교, 장비 선정 등.
- **C. Technical Standard**: KDS/KCS 적용, 구조 기준 등.
- **D. Regulatory**: 산업안전보건비, 하도급 등 법률/행정 요소.

## 4. Source Quality Framework (출처 신뢰도 계층)
"실무 최우선"이 "아무 블로그나 믿는다"는 뜻은 아닙니다. 수집된 자료는 다음 Tier에 따라 신뢰도를 판별합니다.
- **Tier A (Highest Trust)**: 국가법령정보센터, KCS/KDS, 국토부, 환경부 등 국가 공식자료.
- **Tier B (Public Tech)**: LH, 도로공사, K-water 등 공공기관 기술자료.
- **Tier C (Industry Pro)**: 전문 토목 블로그(civileng7 등), 기술사 블로그, 업계 기술자료. (중요한 실무 참고서지만 Tier A를 이길 수는 없음)
- **Tier D (Community)**: 일반 카페, 커뮤니티 등의 단순 개인 경험담.

이후 Writer Agent는 이 Tier 정보를 바탕으로 **가장 높은 신뢰도의 증거를 기반으로 실무적 결론을 작성**하게 됩니다.
