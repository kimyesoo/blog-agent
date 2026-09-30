# Civil Engineering Blog Agent - Research/SERP Layer

## Overview
이 모듈은 Topic Research Agent (V2.2)가 생성한 논리적 토픽 후보들을 **실제 검색 엔진과 공식 기술 자료의 데이터**와 연결하여 해당 주제에 대한 실무적 콘텐츠 작성 가치(Research Readiness)를 검증합니다.

**핵심 철학: Evidence Balance Framework**
단순히 법령이나 기준을 나열하는 백과사전이 아니라, 대한민국 토목 실무자들이 현장에서 필요로 하는 실무 지식을 생산하기 위해 법령, 기술기준, 공공지침, 현장 실무 경험(블로그 등)을 주제의 성격(Archetype)에 따라 동적으로 가중치를 두어 수집합니다.

## Architecture

```
Taxonomy
   ↓
Topic Research V2.2
   ↓
Topic Candidate
   ↓
Archetype Classification (Regulatory, Technical Standard, Field Practice, Knowledge)
   ↓
Dynamic Query Generation
   ↓
Search Providers (Google, Naver, Bing, Mock)
   ↓
SERP Results & Cache
   ↓
Source Classification & Evidence Hierarchy Ranking
   ↓
Research Summary (Gap, Readiness, Evidence Matrix)
   ↓
Research-ready Topic
```

## Key Components
- **ArchetypeClassifier**: 토픽의 `technical_core`와 `search_intent`를 분석하여 4가지 콘텐츠 유형 중 하나로 분류하고 적절한 Evidence Weight를 결정합니다.
- **SearchProvider**: 추상화된 검색 엔진 인터페이스.
- **SourceClassifier**: 검색된 URL의 도메인을 기반으로 자료의 성격(법령, 기준, 실무 블로그 등)을 분류합니다.

## Setup
실제 API 연결 시 `.env`에 KEY 세팅 후 구동합니다.
```bash
python3 research_serp_agent.py --input topic_research/v2_2_test_candidates.json --provider mock
```
