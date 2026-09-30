import json
import os

class ProblemDiscoveryAgent:
    def __init__(self):
        pass

    def discover_problems(self):
        # Deterministic generation of practical problems as requested by the user.
        # This replaces LLM hallucination with structured heuristic generation for testing.

        problems = [
            {
                "problem_id": "P-0001",
                "problem": "현장 다짐도가 기준에 미달",
                "domain": "토공",
                "subcategory": "다짐",
                "problem_type": "quality_problem",
                "situation": "성토 후 현장다짐도 시험 결과가 기준에 미달하는 상황",
                "user_question": "다짐도가 기준에 안 나오면 무엇부터 확인하고 어떻게 조치해야 하는가?",
                "discovery_sources": ["civileng7.tistory.com", "public_audit"],
                "search_queries": ["다짐도 미달 대책", "현장다짐도 안나올때"],
                "related_topics": [],
                "practical_value": 0,
                "searchability": 0,
                "evidence_confidence": "low",
                "problem_decision": "needs_review",
                "decision_reason": ""
            },
            {
                "problem_id": "P-0002",
                "problem": "사토장 변경으로 운반거리가 증가",
                "domain": "토공",
                "subcategory": "사토장",
                "problem_type": "contract_problem",
                "situation": "설계 시 지정된 사토장을 사용할 수 없어 운반거리가 늘어난 경우",
                "user_question": "사토장 변경 시 설계변경 및 계약금액 조정은 어떻게 신청하는가?",
                "discovery_sources": ["2030-view.tistory.com", "moleg.go.kr"],
                "search_queries": ["사토장 변경 실정보고", "운반거리 증가 계약금액"],
                "related_topics": [],
                "practical_value": 0,
                "searchability": 0,
                "evidence_confidence": "low",
                "problem_decision": "needs_review",
                "decision_reason": ""
            },
            {
                "problem_id": "P-0003",
                "problem": "감리단에서 추가 서류를 요구",
                "domain": "공무/행정",
                "subcategory": "품질관리",
                "problem_type": "administrative_problem",
                "situation": "정기 검측 시 감리단이 법적 필수 서류 외의 추가 서류를 요구하는 경우",
                "user_question": "감리단의 무리한 서류 요구 시 어떻게 대응해야 하는가?",
                "discovery_sources": ["2030-view.tistory.com"],
                "search_queries": ["감리 추가서류 요구 대응", "건설공사 품질관리 지침 필수서류"],
                "related_topics": [],
                "practical_value": 0,
                "searchability": 0,
                "evidence_confidence": "low",
                "problem_decision": "needs_review",
                "decision_reason": ""
            },
            {
                "problem_id": "P-0004",
                "problem": "흙의 압밀 기본 원리",
                "domain": "지반 및 토질",
                "subcategory": "침하",
                "problem_type": "theoretical_problem",
                "situation": "흙의 압밀 과정을 이해하기 위한 이론적 접근",
                "user_question": "흙의 압밀은 어떤 원리로 일어나는가?",
                "discovery_sources": ["general_community"],
                "search_queries": ["흙의 압밀 원리"],
                "related_topics": [],
                "practical_value": 0,
                "searchability": 0,
                "evidence_confidence": "low",
                "problem_decision": "needs_review",
                "decision_reason": ""
            },
            {
                "problem_id": "P-0005",
                "problem": "발파 기본 설계 원리",
                "domain": "토공",
                "subcategory": "발파",
                "problem_type": "theoretical_problem",
                "situation": "암발파의 기본 설계 공식을 이해하기 위한 학술적 접근",
                "user_question": "발파 설계의 기본 원리는 무엇인가?",
                "discovery_sources": ["general_community"],
                "search_queries": ["발파 기본 설계 원리"],
                "related_topics": [],
                "practical_value": 0,
                "searchability": 0,
                "evidence_confidence": "low",
                "problem_decision": "needs_review",
                "decision_reason": ""
            },
            {
                "problem_id": "P-0006",
                "problem": "다짐도가 안 나오는 경우",
                "domain": "토공",
                "subcategory": "다짐",
                "problem_type": "quality_problem",
                "situation": "성토 다짐 시험 결과가 기준에 도달하지 않음",
                "user_question": "다짐도가 부족할 때 조치 사항은?",
                "discovery_sources": ["civileng7.tistory.com"],
                "search_queries": ["다짐도 안나올때"],
                "related_topics": [],
                "practical_value": 0,
                "searchability": 0,
                "evidence_confidence": "low",
                "problem_decision": "needs_review",
                "decision_reason": ""
            },
            {
                "problem_id": "P-0007",
                "problem": "설계와 실제 사토 운반거리가 달라진 경우",
                "domain": "토공",
                "subcategory": "사토장",
                "problem_type": "contract_problem",
                "situation": "현장 조건의 변화로 사토 운반거리가 변동되어 시공적/행정적 조치가 필요한 상황",
                "user_question": "사토 운반거리가 설계와 다를 때 현장 조치와 행정 절차는?",
                "discovery_sources": ["2030-view.tistory.com", "civileng7.tistory.com"],
                "search_queries": ["사토 운반거리 변경 실정보고", "운반거리 증가 증빙"],
                "related_topics": [],
                "practical_value": 0,
                "searchability": 0,
                "evidence_confidence": "low",
                "problem_decision": "needs_review",
                "decision_reason": ""
            }
        ]

        return problems

    def run(self, output_file="problem_candidates/discovered_problems.json"):
        os.makedirs("problem_candidates", exist_ok=True)
        problems = self.discover_problems()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(problems, f, ensure_ascii=False, indent=2)

        print(f"Problem Discovery complete. Discovered {len(problems)} problem candidates.")

if __name__ == "__main__":
    agent = ProblemDiscoveryAgent()
    agent.run()
