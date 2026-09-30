# Civil Engineering Blog Agent - Research/SERP Layer

## Overview
이 모듈은 Topic Research Agent (V2.2)가 생성한 논리적 토픽 후보들을 **실제 검색 엔진과 공식/실무 기술 자료**와 연결하여 해당 주제에 대한 실무적 콘텐츠 작성 가치(Research Readiness)를 검증합니다.

**핵심 철학: Practical Blog Framework + Configurable Evidence Weighting**
이 플랫폼은 법률 백과사전이나 단순 아카이브가 아닙니다. 건설 현업 기술자들이 현장에서 직면하는 **실제 문제를 빠르고 실용적으로 해결할 수 있도록 돕는 실무 지식 시스템**입니다. 법령, 기술기준, 공공지침, 블로그 등의 자료는 이 "문제 해결"을 뒷받침하는 증거(Evidence)로서만 기능합니다. 더불어, 프로젝트의 방향성에 따라 증거 가중치를 코드 수정 없이 동적으로 변경할 수 있는 시스템 구조를 채택하고 있습니다.

## Architecture

```
Taxonomy
   ↓
Topic Research V2.2
   ↓
Topic Candidate
   ↓
Configuration Layer (weights.json - Profile Selection)
   ↓
Archetype Classification & Dynamic Weighting
   ↓
Dynamic Query Generation
   ↓
Search Providers (Google, Naver, Bing, Mock)
   ↓
Source Classification & Evidence Ranking (Tiers A, B, C, D)
   ↓
Research Summary (Gap, Readiness, Evidence Matrix)
   ↓
Research-ready Topic
```

## Key Components
- **weights.json**: 코드 하드코딩 없이 `practical_blog`, `balanced`, `technical_reference`, `regulation_focus` 등의 프로필별로 증거 수집 가중치를 동적으로 조절하는 핵심 설정 파일입니다.
- **ArchetypeClassifier**: 토픽의 `technical_core`와 `search_intent`를 4가지 유형으로 분류하되, `weights.json`에 정의된 가중치를 맵핑합니다.
- **SourceClassifier**: 검색된 URL의 권위를 Tier A (국가기관/기준), Tier B (공공기관), Tier C (기술사/전문 블로그), Tier D (일반 커뮤니티)로 계층화하여 분류합니다.

## Setup
실제 API 연결 시 `.env`에 KEY 세팅 후 구동합니다.
```bash
python3 research_serp_agent.py --input topic_research/v2_2_test_candidates.json --provider mock --profile practical_blog
```
