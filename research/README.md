# Civil Engineering Blog Agent - Research/SERP Layer

## Overview
이 모듈은 Topic Research Agent (V2.2)가 생성한 논리적 토픽 후보들을 **실제 검색 엔진과 공식 기술/법령 자료의 데이터**와 연결하여, 해당 주제에 대한 콘텐츠 작성 가치(Research Readiness)와 자료 수급 가능성을 검증합니다. 단순히 검색량을 조회하는 것을 넘어 출처의 신뢰성, 쿼리 인텐트, 공식 문서(PDF 등)의 존재 여부를 입체적으로 분석합니다.

특히 **모든 콘텐츠는 법령/규정 체계를 우선 검토하는 것**을 최우선 원칙으로 삼습니다. 검색 결과에 의존하기 전에 법적, 기술적 근거 체계를 먼저 조사합니다.

## Architecture

```
Taxonomy
   ↓
Topic Research V2.2
   ↓
Topic Candidate
   ↓
Research Query Generation (Query Generator - General, Legal, Standard)
   ↓
Search Providers (Google, Naver, Bing, Mock)
   ↓
SERP Results & Cache
   ↓
Source Classification (Legal, Official, Academic, Industry, Community, Blog)
   ↓
Legal Coverage Report / Technical Standard Research
   ↓
Research Summary (Gap, Readiness, Evidence Matrix)
   ↓
Research-ready Topic
```

## Key Components
- **SearchProvider**: 추상화된 검색 엔진 인터페이스입니다. API 미연결 시 `MockSearchProvider`를 통해 테스트가 가능합니다.
- **SourceClassifier**: 검색된 URL의 도메인과 `is_pdf` 등의 메타데이터를 기반으로 법령, 기준, 일반 공식자료 등을 판별합니다.
- **source_registry.json / legal_source_registry.json**: 하드코딩된 휴리스틱 외에도 특정 도메인(e.g., KCSC, law.go.kr)을 명시적으로 매핑하는 화이트리스트입니다.

## Setup
실제 검색 API 연결 시 `.env`에 KEY를 세팅합니다.
```bash
python3 research_serp_agent.py --input topic_research/v2_2_test_candidates.json --provider mock
```
