# Blog Agent V1

## 1. 프로젝트 개요
* **프로젝트명**: Blog Agent
* **목적**: 기존 작성된 콘텐츠를 기반으로 새로운 주제를 추천하고, 추천된 주제에 대해 리서치 및 문서 작성을 자동화하는 블로그 에이전트 시스템을 개발합니다.
* **현재 개발 단계**: 초기 구조 세팅 및 Topic Agent, Research Agent 구현 (Phase 2 진행 중)

## 2. 현재 구현 기능
* **Content Database**: 이전에 발행된 블로그 게시물(또는 작성된 문서)의 주제 목록을 저장하고 관리하는 데이터베이스(JSON 형태)입니다.
* **Topic Agent**: 기존 콘텐츠 데이터를 기반으로 관련 주제를 추천하는 기능입니다.
* **Topic Research Agent**: 특정 분야(예: 토질시험)의 콘텐츠 후보군을 조사/확장하여 체계적인 콘텐츠 구조를 생성하는 기능입니다.
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
└── topic_research/
    └── topic_candidates.json    # Topic Research Agent가 생성한 확장 콘텐츠 후보 목록
```

## 4. 실행 방법
* **필요한 환경**: Python 3.x
* **실행 명령어**:
  * Topic Agent 실행: `python3 topic_agent.py`
  * Topic Research Agent 실행: `python3 topic_research_agent.py` (또는 `python3 topic_research_agent.py "분야명"`)
  * Research Agent 실행: `python3 research_agent.py`
* **입력 파일**:
  * `content_db/posts.json` (Topic Agent 및 Topic Research Agent용)
  * `topic_candidates/candidates.json` (Research Agent용)
* **출력 파일**:
  * `topic_candidates/candidates.json` (Topic Agent 출력)
  * `topic_research/topic_candidates.json` (Topic Research Agent 출력)
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
