# Civil Engineering Blog Agent

## 1. 프로젝트 개요
* **프로젝트명**: Civil Engineering Blog Agent
* **목적**: 기존에 발행된 토목 공학 관련 콘텐츠를 기반으로 현장 실무의 문제(Problem)를 발굴하고 검증하여, 실무 중심의 검색 최적화된 주제(Topic)를 추출한 뒤, SERP API를 통해 증거(Evidence)를 수집 및 구조화하고 최종 블로그 포스트를 자동으로 작성하는 AI 에이전트 파이프라인입니다.
* **현재 진행 상태**: **Research Agent V2.2 개발 완료** (16개 테스트 전체 통과, Completeness 스코어 기반 `writer_readiness` 평가 로직 및 실무 절차/행정 문서/관점 충돌 추출 엔진 완비)
* **시스템 철학 (핵심 원칙)**:
  * **LLM Hallucination 원천 차단**: 데이터베이스 로드, 텍스트 파싱, 주제 유사도 검증, 리서치 수집 및 분류 과정에서 거대 언어 모델(LLM)의 생성 능력을 배제하고, 결정론적(Deterministic)이고 재현 가능한 룰(Rule-based) 엔진을 사용합니다.
  * **현장 실무 우선(Practical Value First)**: 교과서적인 원리나 학술적 정의가 아닌, 현장 다짐도 미달, 실정보고 서류, 기준 상충 등 실무자의 문제 해결 중심 콘텐츠에 최우선 가중치를 부여합니다.

## 2. 핵심 데이터 파이프라인 아키텍처
본 프로젝트는 단일 에이전트가 아닌, **핵심 데이터의 순차적 흐름**을 기반으로 구동되는 다중 에이전트 시스템입니다.

**흐름 요약**: `problem_candidates` ➔ `Topic Validation` ➔ `Research Agent (JSON 구조화)` ➔ `Writer Agent (Markdown 생성)`

1. **Problem Discovery Agent** (`problem_discovery_agent.py`)
   - 기존 발행 포스트(`content_db/posts.json`)를 스캔하여 현장 실무 기반 문제 상황 후보(`problem_candidates`)를 발굴합니다.
2. **Problem Validation Agent** (`problem_validation_agent.py`)
   - 발견된 문제들의 출처(Source), AI 추론 여부 등을 휴리스틱으로 검증(Topic Validation)하여 승인, 반려, 병합 처리합니다.
3. **Topic Agent** (`topic_agent.py`)
   - 엄격한 템플릿(Heuristics)을 바탕으로 검증된 실무 문제를 검색 친화적인 SEO 주제(Topic)로 자동 변환합니다.
4. **Research SERP Agent** (`research_serp_agent.py`)
   - 실무 블로그, 공식 법령 사이트, 기술 표준원 등을 분리하여 검색하는 인터페이스 및 `SourceClassifier` 모듈입니다.
5. **Research Agent V2.2** (`research_agent.py`)
   - **(핵심 엔진)** 주제에 대한 검색 스니펫을 수집 후, LLM 없이 정규식과 키워드 매칭만으로 절차, 행정 문서, 진단 요소를 추출하여 구조화된 **Research Pack JSON**을 생성합니다.
   - V2.2의 Completeness Engine(0~100점)을 통해 **Writer Readiness**(ready, partial, insufficient)를 결정하여 빈약한 리서치 기반 작성을 방지합니다.
6. **Writer Agent V1** (`writer_agent.py`)
   - 완성도 높은 Research Pack JSON을 입력받아 **10단계 고정 마크다운 템플릿**(문제 상황, 원인, 확인사항, 실무조치, 행정절차, 관련기준, 빈출 실수, 결론, FAQ) 기반의 **최종 Markdown 블로그 글**을 생성합니다.

## 3. 핵심 설정 파일 (Configuration)
* **`research/weights.json`**: 프로필별(실무 블로그 중심, 기술 표준 중심 등) 수집 증거물의 가중치 배점을 하드코딩 없이 동적 조절.
* **`taxonomy.json`**: 대한민국 토목산업 전반의 카테고리(토공, 구조물, 도로, 품질관리 등)와 범위 제한을 규정.
* **`research/source_registry.json` & `legal_source_registry.json`**: 신뢰도 판정을 위해 허용된 공식(Law, KCS) 및 실무(전문 블로그) 도메인의 티어(Tier A~D) 맵핑 정보.

## 4. 환경 설정 및 실행 방법

### 환경 설정
* **필요 환경**: Python 3.10+
* **의존성 설치**:
  ```bash
  pip install -r requirements.txt
  ```
* **환경 변수**:
  루트 디렉토리의 `.env.example`을 복사해 `.env`를 생성하고 필요한 API Key를 기입하세요. (예: `TAVILY_API_KEY`)

### 테스트 구동
전체 시스템 무결성 및 엔진(추출, 가중치 산정, Writer 차단 로직)을 검증하기 위한 pytest가 구성되어 있습니다.
```bash
python -m pytest tests/ -v
```

### 파이프라인 수동 실행 흐름
순차적인 실행을 통해 `content_db/` -> `problem_candidates/` -> `topic_candidates/` -> `research/research_packs/` -> `writer_output/` 로 데이터가 이동합니다.
```bash
python problem_discovery_agent.py
python problem_validation_agent.py
python topic_agent.py
python research_agent.py
python writer_agent.py
```

## 5. 레거시(Legacy) 및 아카이브 컴포넌트
V1.x 시절 `taxonomy.json`에 의존하여 단순히 주제를 무작위 조합하던 낡은 Topic 중심 방식의 에이전트들은 `PROJECT_STRUCTURE_REPORT_V2_2.md`에 분류되어 유지되고 있으나 운영 파이프라인에서 제외되었습니다.
* `topic_research_agent.py`
* `topic_validation_agent.py`
* `topic_opportunity_scoring_agent.py` 등


## 6. 향후 로드맵 (To-Do)
* **통합 테스트 진행**: 현재 독립적으로 작성된 `writer_agent.py`와 업데이트된 `Research Agent V2.2` 간의 통합(E2E) 테스트를 수행합니다.
* **Writer 에이전트 내부 매핑 업데이트**: V2.2에서 도입된 최신 Research Pack 스키마(예: `practical_view`, `official_view` 등 충돌 분석 데이터)를 Writer 에이전트 템플릿에 온전히 렌더링하도록 매핑 로직을 고도화합니다.
* **최종 자동화 파이프라인 구축**: 문제 발굴부터 마크다운 파일 출력까지 끊김없이 이어지는 완전한 최종 블로그 글 생성 파이프라인(CLI 툴 혹은 메인 오케스트레이터 스크립트)을 구축합니다.
