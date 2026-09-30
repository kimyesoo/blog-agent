# Blog Agent V1

## 1. 프로젝트 개요
* **프로젝트명**: Blog Agent
* **목적**: 기존 작성된 콘텐츠를 기반으로 새로운 주제를 추천하고, 추천된 주제에 대해 리서치 및 문서 작성을 자동화하는 블로그 에이전트 시스템을 개발합니다.
* **현재 개발 단계**: 초기 구조 세팅 및 Topic Agent, Research Agent 구현 (Phase 2 진행 중)

## 2. 현재 구현 기능
* **Content Database**: 이전에 발행된 블로그 게시물(또는 작성된 문서)의 주제 목록을 저장하고 관리하는 데이터베이스(JSON 형태)입니다.
* **Topic Agent**: 기존 콘텐츠 데이터를 기반으로 관련 주제를 추천하는 기능입니다.
* **Topic Research Agent V2**: `taxonomy.json`을 기반으로 대한민국 토목산업 전반의 기술 분야를 균형 있게 탐색하여 콘텐츠 주제 후보를 생성합니다. 기술 분야(분류)와 콘텐츠 유형(검색 의도)을 분리하여 자연스럽고 확장 가능한 주제 조합을 생성하며, 기존 `posts.json` 데이터와 비교해 중복을 방지합니다.
* **Topic Validation Agent (V1.2.1)**: Topic Research Agent가 생성한 후보 주제를 검증합니다. V1.2.1에서는 KEEP / MERGE / REJECT / REVIEW 4단계 판정을 지원하며, `search_intent` 및 `content_type` 적합성 검증, `confidence` 수준 평가, 독립된 `merge_candidates`와 `related_topics` 분리 등 높은 정확도의 로컬 판정 로직을 적용합니다. 더불어 다중 `reason_codes` 로직과 엄격한 본문 중복 체크(content_gap)를 통해 기계적인 병합 방지 및 이상 패턴 분석이 강화되었습니다.
* **Topic Search Research Agent V1.1**: Validation이 완료된 topic 후보에 대해 실제 웹 검색 결과를 조사합니다. V1.1에서는 검색 결과를 구조화하여 관찰·분석하는 단계로 확장되었습니다. Tavily API의 SERP를 통해 휴리스틱하게 `observed_search_intent`를 파악하고, 상위 콘텐츠의 타입(블로그, 커뮤니티, 정부문서 등) 분포를 추출하며, `observed_related_queries`와 콘텐츠 공백(`content_gap`)을 분석합니다. 검색량/경쟁도는 실제 데이터 소스 부재 시 지속적으로 `null` 처리하여 AI의 임의 추정을 배제합니다.
* **Topic Opportunity Scoring Agent V1**: Topic Search Research Agent가 생성한 SERP 데이터(`search_results.json`)를 바탕으로, 주제의 콘텐츠 공백(Content Gap), 의도 명확성(Intent Clarity), 그리고 포화도(Saturation Score)를 산출하여 0~100점 척도의 최종 기회 점수(Opportunity Score)를 도출합니다. LLM을 전혀 사용하지 않는 규칙 기반 휴리스틱을 엄격히 적용합니다.
* **Topic Prioritization Agent V1**: 검증된 주제 데이터(`validated_topics.json`)와 검색 결과(`search_results.json`)를 취합하여 어떤 주제를 먼저 작성해야 할지 결정하는 우선순위 에이전트입니다. 제목 기반 실무 가치(Practical Value), 공백 분석(Content Gap), 검색 의도(Intent Clarity), 경쟁 강도(Competition)를 종합하여 우선순위를 0~100점으로 정량화하고 Critical부터 Ignore까지 5단계로 분류합니다.
* **Research Agent**: Topic Agent가 추천한 주제 중 하나를 선택하여 정해진 목차(시험 목적, 시험 원리 등 8개 항목)에 따라 기본 리서치 마크다운 템플릿 문서를 자동 생성하는 에이전트입니다.

## 3. 폴더 구조
```
.
├── README.md
├── content_db/
│   └── posts.json               # 기존 작성된 블로그 주제 데이터베이스
├── research/
│   └── 흙의_압밀_시험방법.md      # Research Agent가 생성한 리서치 문서
├── research_agent.py            # Research Agent 스크립트
├── topic_agent.py               # Topic Agent 스크립트
├── topic_candidates/
│   └── candidates.json          # Topic Agent가 생성한 추천 주제 목록
├── topic_research_agent.py      # Topic Research Agent 스크립트
├── topic_validation_agent.py    # Topic Validation Agent 스크립트
├── topic_validation_report.py   # Topic Validation Agent 결과 분석 리포트 생성 스크립트
├── topic_search_research_agent.py # Topic Search Research Agent 스크립트
├── topic_opportunity_scoring_agent.py # Topic Opportunity Scoring Agent 스크립트
├── topic_prioritization_agent.py # Topic Prioritization Agent 스크립트
├── topic_research/
│   ├── topic_candidates.json      # Topic Research Agent가 생성한 확장 콘텐츠 후보 목록
│   ├── validated_topics.json      # Topic Validation Agent가 검증 및 정리한 최종 후보 목록
│   ├── validation_summary.json    # Topic Validation Agent의 최종 처리 통계 요약
│   ├── validation_report.json     # Validation 데이터 분석 상세 결과
│   └── validation_report.md       # Validation 데이터 분석 사람이 읽기 쉬운 요약 리포트
└── topic_search/
    ├── search_results.json        # Topic Search Research Agent의 검색 원본 데이터
    ├── search_summary.json        # 검색 현황 통계 요약
    ├── search_report.md           # 검색 분석 리포트
    └── cache/                     # 검색 결과 임시 캐시 저장소
```

## 4. 환경 설정 및 실행 방법
* **필요한 환경**: Python 3.x
* **의존성 설치**:
  ```bash
  pip install tavily-python python-dotenv>=1.0.0
  ```
  *(Topic Search Research Agent에서 실제 검색 결과를 얻기 위해 필요합니다. 설치하지 않거나 `TAVILY_API_KEY`가 없을 경우 안전한 fallback 모드로 동작합니다.)*

* **환경 변수 설정**:
  ```bash
  cp .env.example .env
  ```
  이후 `.env` 파일에 `TAVILY_API_KEY=실제_발급받은_API_KEY` 를 입력합니다.

* **실행 명령어**:
  * Topic Agent 실행: `python3 topic_agent.py`
  * Topic Research Agent 실행: `python3 topic_research_agent.py` (또는 `python3 topic_research_agent.py "분야명"`)
  * Topic Validation Agent 실행: `python3 topic_validation_agent.py`
  * Topic Validation Report 생성: `python3 topic_validation_report.py`
  * Topic Search Research Agent 진단: `python3 topic_search_research_agent.py --diagnose`
  * Topic Search Research Agent 캐시 삭제: `python3 topic_search_research_agent.py --clear-cache`
  * Topic Search Research Agent 실행: `python3 topic_search_research_agent.py --decision KEEP --limit 5` (추가 플래그: `--topic`, `--refresh`, `--disable-cache`)
  * Topic Opportunity Scoring Agent 실행: `python3 topic_opportunity_scoring_agent.py`
  * Topic Prioritization Agent 실행: `python3 topic_prioritization_agent.py`
  * Research Agent 실행: `python3 research_agent.py`
* **입력 파일**:
  * `content_db/posts.json` (Topic Agent, Topic Research Agent, Topic Validation Agent, Topic Search Research Agent용)
  * `topic_candidates/candidates.json` (Research Agent용)
  * `topic_research/topic_candidates.json` (Topic Validation Agent용)
  * `topic_research/validated_topics.json` (Topic Validation Report, Topic Search Research Agent, Topic Prioritization Agent용)
  * `topic_research/validation_summary.json` (Topic Validation Report용)
  * `topic_search/search_results.json` (Topic Opportunity Scoring Agent, Topic Prioritization Agent용)
* **출력 파일**:
  * `topic_candidates/candidates.json` (Topic Agent 출력)
  * `topic_research/topic_candidates.json` (Topic Research Agent 출력)
  * `topic_research/validated_topics.json` (Topic Validation Agent 출력)
  * `topic_research/validation_report.json` (Topic Validation Report 상세 출력)
  * `topic_research/validation_report.md` (Topic Validation Report 마크다운 출력)
  * `topic_search/search_results.json` (Topic Search Research Agent 출력)
  * `topic_search/search_summary.json` (Topic Search Research Agent 요약)
  * `topic_search/search_report.md` (Topic Search Research Agent 마크다운 출력)
  * `topic_search/opportunity_scores.json` (Topic Opportunity Scoring Agent 출력)
  * `topic_search/opportunity_report.md` (Topic Opportunity Scoring Agent 마크다운 출력)
  * `topic_priority/topic_priority.json` (Topic Prioritization Agent 출력)
  * `topic_priority/topic_priority_report.md` (Topic Prioritization Agent 마크다운 출력)
  * `research/*.md` (Research Agent 출력)

## 5. 현재 데이터 구조
* **posts.json**: 기존 작성된 블로그 포스트의 데이터들이 객체 배열 구조(title, views, cluster, content_type 포함)로 저장됩니다.
* **candidates.json**: Topic Agent를 통해 추천받은 새로운 주제들이 리스트 형태의 문자열 배열로 저장됩니다.

## 6. 향후 개발 로드맵
* **Phase 1**: Content DB, Topic Agent 구현 (완료)
* **Phase 2**: Research Agent 구현 (진행 중 - 템플릿 생성 구현됨)
* **Phase 3**: Writer Agent 구현 (예정 - 리서치 문서를 바탕으로 실제 블로그 포스트 작성)
* **Phase 4**: Analytics (예정 - 발행된 게시물의 성과 분석 및 피드백 루프)

## 7. 개발 원칙
* 작은 기능 단위로 개발
* GitHub에 항상 반영
* 자동 발행 기능은 추후 검토
* 사람 검토 후 게시
