# Blog Agent 실무 블로그 벤치마크 분석

## 1. Executive Summary
본 분석은 실제 현장 토목기술자가 참고하는 두 전문 블로그(`civileng7.tistory.com`, `2030-view.tistory.com`)의 구조적 장점을 추출하여, 우리 Blog Agent의 Content/Research 설계 원칙을 도출하기 위함입니다. 핵심은 "무엇을 베낄 것인가"가 아니라 **"왜 현장 기술자가 이 자료들을 찾는가(Practical Problem Solving)"**를 이해하고, 이를 우리 시스템의 Evidence Pipeline과 Content Architecture에 반영하는 것입니다.

## 2. civileng7 구조 분석
civileng7은 전통적인 "토목기술사" 및 "현장 공학" 중심의 지식 베이스입니다.
* **Category**: 토공사, 구조물공사, 지반공학, 터널, 교량, 시방서/기준 요약.
* **Content Type**: 공법 비교, 시공순서, 시험방법, 발생 가능한 문제점 및 대책.
* **Typical Search Intent**: "A공법과 B공법의 차이가 무엇인가?", "다짐불량 발생 시 대책은 무엇인가?", "이 시험의 정확한 순서와 계산법은 무엇인가?"
* **Field Usefulness**: 기술사 시험 준비 및 현장에서 시공 계획서(Method Statement) 작성 시 이론적 배경과 발생 가능한 문제를 사전에 검토하기 좋음.

## 3. 2030-view 구조 분석
2030-view는 "건설공무", "품질/안전 서류", "계약/설계변경" 등 현장 관리 및 행정 실무 중심의 블로그입니다.
* **Category**: 품질관리(Q), 안전관리(S), 건설공무(계약/하도급/설계변경), 관련 법규 해석.
* **Content Type**: 각종 체크리스트, 서식(양식) 다운로드, 법규 해석 사례, 공무 처리 절차, 실무 Q&A.
* **Typical Search Intent**: "이 검측을 받을 때 필요한 서류 양식은 무엇인가?", "설계변경 사유서 작성 예시는?", "산업안전보건관리비 정산 기준은 어떻게 되는가?"
* **Field Usefulness**: 현장 공무/품질 담당자가 당장 서류를 꾸미거나, 발주처/감리와의 분쟁에서 법적 근거를 찾고 방어 논리를 세우는 데 극도로 유용함.

## 4. 콘텐츠 유형 비교
| 콘텐츠 유형 | civileng7 비중(추정) | 2030-view 비중(추정) | 실무 활용도 |
|---|---|---|---|
| 공학이론/공법 | 60% | 10% | 시공계획, 기술검토서 작성 (Medium/High) |
| 시험/측정방법 | 20% | 20% | 품질검사, 현장시험 수행 (High) |
| 원인과 대책 | 15% | 5% | 하자 보수, 현장 문제 해결 (Very High) |
| 공무/법규해석 | 5% | 40% | 기성청구, 설계변경, 감리 대응 (Very High) |
| 서식/체크리스트 | 0% | 25% | 당일 현장 서류 업무 (Very High) |

## 5. 검색 의도 비교
* **civileng7 검색자**: "지식을 잊어버렸거나 모를 때", "보고서에 쓸 그럴싸한 공학적 이유가 필요할 때", "기술사 시험을 준비할 때". (Informational & Procedural)
* **2030-view 검색자**: "감리가 당장 서류를 내라고 할 때", "하도급 업체와 정산 문제로 싸울 때", "정확한 최신 법규나 양식이 필요할 때". (Actionable & Regulatory)

## 6. 현장 문제 유형 비교
```json
// civileng7 샘플 구조 (현장 문제: 콘크리트 타설 후 균열 발생)
{
  "practical_problem": "콘크리트 구조물에 예상치 못한 균열이 발생하여 감리가 조치를 요구함.",
  "search_intent": "콘크리트 균열 원인과 보수보강 대책",
  "expected_answer": "재료적/시공적 원인 분석 리스트 및 수지주입 공법 등 해결책",
  "solution_type": "기술적 대책 (공학적 원리 기반)",
  "supporting_evidence": "KCS, 기술사 서적, 논문",
  "field_usefulness": "원인 분석 보고서 작성 및 보수 계획 수립에 유용."
}

// 2030-view 샘플 구조 (현장 문제: 레미콘 반입 시 품질검사 서류 누락)
{
  "practical_problem": "레미콘 반입을 해야 하는데 감리가 요구하는 품질검사 체크리스트 양식이 없음.",
  "search_intent": "레미콘 반입 검사 체크리스트 양식 HWP",
  "expected_answer": "최신 건설공사 품질관리 지침에 맞는 다운로드 가능한 빈 양식과 작성 요령",
  "solution_type": "행정적 해결 (서류/절차 기반)",
  "supporting_evidence": "건설기술진흥법, 국토부 품질관리 지침",
  "field_usefulness": "당일 서류 작업 시간을 즉시 단축시켜줌."
}
```

## 7. Practical Value 비교
* **civileng7**: 깊이 있는 기술적 통찰을 제공하나, 당장 현장에서 다운받아 쓸 "양식"은 부족함. 하지만 시공 문제 발생 시 원인을 파악하는 데는 필수적임.
* **2030-view**: 기술적 깊이는 얕을 수 있으나, 당장의 행정적/법적 문제를 해결하고 서류 작업을 끝내주는 실무적 가치(Time-saving)가 압도적임.

## 8. Source Quality / Authority 비교
* 두 블로그 모두 개인이 운영하므로 **Authority(법적 구속력)는 없음**.
* 그러나 **Source Quality(정보의 정돈 상태, 가독성, 실무 적합성)**는 매우 높음. 현장 기술자는 KCS 원문을 읽기 어려워 블로그의 요약본을 신뢰하고 차용함.
* 즉, `Authority = Low`, `Practical Value = High`의 전형적인 Tier C (Industry Pro) 사례.

## 9. 각 블로그의 강점
* **civileng7**: 공법의 모식도, 비교표, 장단점 정리가 훌륭함. 기술사 답안지 포맷을 차용하여 보고서에 그대로 복사해 넣기 좋음.
* **2030-view**: 최신 법령 개정 사항을 빠르게 반영함. 딱딱한 법령을 "현장에서 감리와 대화할 때 쓸 수 있는 해석"으로 번역해줌. 실제 HWP/Excel 양식 제공.

## 10. 각 블로그의 개선 가능 영역 (단점)
* **정보 최신성/검증 불가**: 블로그 글이 5년 전 KCS 기준을 따르고 있어도 독자가 알기 어려움. (우리 시스템이 최신 KCS와 교차 검증해야 할 부분).
* **파편화**: 내가 원하는 양식과 기술적 설명이 서로 다른 블로그에 흩어져 있음.

## 11. 두 블로그에서 공통적으로 발견되는 실무 가치
* **문제 지향적(Problem-Oriented)**: 단순 사전적 정의가 아니라, 현장에서 부딪히는 '상황(Situation)'을 전제로 글이 시작됨.
* **구조화된 요약(Structured Summary)**: 긴 서술형보다 표, 불릿 포인트, 번호 매기기를 통해 빠르게 읽히도록 구성됨.

## 12. 우리 블로그가 가져올 요소
* 표를 활용한 공법/장비 장단점 비교 구조.
* 법령/기준을 그대로 복붙하지 않고 실무적 의미로 해석하는 접근 방식.
* 발생 가능한 문제점과 그에 대한 '원인-대책' 매핑.
* 관련된 서식/체크리스트가 필요하다는 사실을 명시(또는 제공).

## 13. 우리 블로그가 가져오지 않을 요소
* 부정확하거나 오래된 개인적 뇌피셜(공식 근거 없는 주장).
* 블로그 운영자의 일상 이야기나 서론.
* 권위 없이 결론을 단정 짓는 태도.

## 14. 권장 콘텐츠 구조 (가설 검증 및 수정)
벤치마크 결과, 기존 가설은 대체로 맞으나 "공무/행정/양식" 측면이 보강되어야 합니다.
수정된 공식:
```text
현장 문제 상황(상황 부여)
↓
핵심 답변 (10초 내 파악 가능)
↓
원인 분석 또는 적용 기준 (이유)
↓
현장 조치 방법 (시공적 대책 OR 행정적 서류 절차)
↓
공식 근거 (KCS, KDS, 법령 원문 인용)
↓
필수 체크리스트 및 실무 주의사항 (감리 지적사항 예방)
```

## 15. 권장 Research Pack 구조
Writer Agent가 위 구조로 글을 쓰기 위해 Research Agent가 넘겨줘야 할 데이터:
```json
{
  "topic": "...",
  "archetype": "...",
  "primary_official_evidence": [...], // KCS/법령 (Authority)
  "primary_practical_evidence": [...], // civileng7/2030-view (Practicality)
  "extracted_problems": [...],
  "extracted_solutions": [...],
  "required_documents_or_checklists": [...],
  "conflicts": [], // 공식 기준과 실무 관행의 차이
  "evidence_confidence": "high"
}
```

## 16. Source Registry 제안
특정 도메인을 하드코딩하지 않고, `source_registry.json`을 통해 관리합니다.
```json
{
  "civileng7.tistory.com": {
    "organization": "개인(토목기술사)",
    "source_type": "industry_pro",
    "authority_level": "medium",
    "practical_value": "high",
    "recommended_archetypes": ["field_problem_solving", "construction_methods"]
  },
  "2030-view.tistory.com": {
    "organization": "개인(건설공무)",
    "source_type": "industry_pro",
    "authority_level": "medium",
    "practical_value": "high",
    "recommended_archetypes": ["regulatory", "field_problem_solving"]
  }
}
```

## 17. Evidence Pool 설계
Search → Gather A/B/C/D → Rank by Weights (Current System)은 올바릅니다.
이 Evidence Pool을 Writer Agent에게 넘길 때, 하나로 뭉치지 않고 `Official(A/B)`과 `Practical(C/D)`로 분리해서 제공하여 Writer가 역할을 나누어 쓰도록 해야 합니다.

## 18. Weighting과의 연결점
* **Q1. 전문 실무 블로그는 어떤 Archetype에서 가장 유용한가?**
  * `field_problem_solving` (기술적 문제 해결)
  * `regulatory` 내의 '현장 적용/공무' 측면 (법을 현장에 어떻게 적용하는가)
* **Q2/Q3. Practical Value와 Source Quality의 분리:**
  * Source Quality(티어)는 낮아도 `weights.json`에서 `field_practice` 비중이 높으면 Practical Value가 높은 것으로 평가됩니다. 이 아키텍처는 완벽하게 유지됩니다.
* **Q4. 공식 자료 부족 시:**
  * weights가 `field_practice`에 점수를 주기 때문에 자연스럽게 실무 블로그가 최상위로 랭크됩니다.
* **Q5. 법령 필요 시:**
  * `regulatory` 아키텍처에서 `law` 비중을 50~70%로 주어 공식 근거를 1위로 올립니다.
* **Q6/Q7. 충돌 시 처리:** (다음 섹션 참조)

## 19. Conflict Handling
전문 블로그(오래된 기준)와 공식 자료(KCS 최신판)가 충돌할 수 있습니다.
Research Agent는 두 주장을 무조건 병합하지 않고, `official_basis`와 `professional_practice`를 분리합니다.
Writer Agent는 다음과 같이 서술하도록 프롬프트를 설계해야 합니다:
> "현장 실무에서는 A방법을 자주 사용하나(출처: 전문 블로그), 2023년 개정된 KCS 기준에 따르면 B방법을 원칙으로 합니다."

## 20. Blog Agent 설계 변경 제안
1. **Taxonomy 유지**: 기존 Taxonomy(토공, 지반 등)는 물리적 분류이므로 수정 불필요. 단, 콘텐츠 생성 시 '공무/서류' 관련 Content Type이 Writer에게 잘 전달되도록 해야 함.
2. **Research Agent 변경**: 현재 Research Agent는 단순히 랭킹만 해서 List를 넘깁니다. 향후 Writer를 위해서는 List를 `official`과 `practical`로 분류하여 전달하는 포맷(`Research Pack`) 도입이 필요합니다.
3. **Conflict Detection**: 서로 다른 티어 간 정보 충돌을 감지(또는 Writer가 감지하도록 지시)하는 장치가 프롬프트에 포함되어야 합니다.
