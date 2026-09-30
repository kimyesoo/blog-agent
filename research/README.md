# Civil Engineering Blog Agent - Research/SERP Layer

## Overview
이 모듈은 Topic Research Agent (V2.2)가 생성한 논리적 토픽 후보들을 **실제 검색 엔진과 공식 기술 자료의 데이터**와 연결하여, 해당 주제에 대한 콘텐츠 작성 가치(Research Readiness)와 자료 수급 가능성을 검증합니다. 단순히 검색량을 조회하는 것을 넘어 출처의 신뢰성, 쿼리 인텐트, 공식 문서(PDF 등)의 존재 여부를 입체적으로 분석합니다.

## Architecture

```
Taxonomy
   ↓
Topic Research V2.2
   ↓
Topic Candidate
   ↓
Research Query Generation (Query Generator)
   ↓
Search Providers (Google, Naver, Bing, Mock)
   ↓
SERP Results & Cache
   ↓
Source Classification (Official, Academic, Industry, Community, Blog)
   ↓
Research Summary (Gap, Readiness, Evidence)
   ↓
Research-ready Topic
```

## Key Components
- **SearchProvider**: 추상화된 검색 엔진 인터페이스입니다. API 미연결 시 `MockSearchProvider`를 통해 테스트가 가능합니다.
- **SourceClassifier**: 검색된 URL의 도메인과 `is_pdf` 등의 메타데이터를 기반으로 자료의 신뢰도를 판별합니다 (예: `.go.kr` -> official).
- **source_registry.json**: 하드코딩된 휴리스틱 외에도 특정 도메인(e.g., KCSC, CODIL)을 명시적으로 매핑하는 화이트리스트입니다.

## Setup
실제 검색 API(Tavily, Google, Naver) 연결을 원할 경우 루트의 `.env` 파일에 발급받은 KEY를 세팅하고 Provider를 전환할 수 있습니다. 현재는 안전한 구조적 테스트를 위해 `MockSearchProvider`가 기본 동작합니다.

```bash
python3 research_serp_agent.py --input topic_research/v2_2_test_candidates.json --provider mock
```
