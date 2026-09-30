# Civil Engineering Blog Agent - Research/SERP Layer

## Overview
이 모듈은 Topic Research Agent (V2.2)가 생성한 논리적 토픽 후보들을 **실제 검색 엔진과 공식/실무 기술 자료**와 연결하여 해당 주제에 대한 실무적 콘텐츠 작성 가치(Research Readiness)를 검증합니다.

**핵심 철학: Practical Value First (실무적 가치 최우선)**
본 플랫폼은 단순한 법률 백과사전이나 기준 보관소가 아닙니다. 현업의 시공사 기술자, 현장 공무, 품질/안전 관리자, 발주처 담당자들이 **현장에서 직면하는 실제 문제를 해결하는 데 도움을 주는 지식 시스템**을 지향합니다. 법령은 뒷받침 근거로 작용할 뿐, 절대다수의 토픽에서는 현장 실무 경험과 공학적 문제 해결 방식이 최우선으로 수집됩니다.

## Architecture

```
Taxonomy
   ↓
Topic Research V2.2
   ↓
Topic Candidate
   ↓
Archetype Classification (Field Problem Solving, Construction Methods, Technical Standard, Regulatory)
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
- **ArchetypeClassifier**: 토픽의 `technical_core`와 `search_intent`를 분석하여 4가지 실무 콘텐츠 유형 중 하나로 분류하고 적절한 Evidence Weight를 결정합니다.
- **SearchProvider**: 추상화된 검색 엔진 인터페이스.
- **SourceClassifier**: 검색된 URL의 도메인을 기반으로 자료의 성격(법령, 기준, 실무 블로그 등)을 분류합니다.

## Setup
실제 API 연결 시 `.env`에 KEY 세팅 후 구동합니다.
```bash
python3 research_serp_agent.py --input topic_research/v2_2_test_candidates.json --provider mock
```
