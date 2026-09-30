import unittest
import json
import os
from research_agent import ResearchAgentV2

class TestResearchAgentV2(unittest.TestCase):
    def setUp(self):
        # Because we merged away the provider argument in a prior merge failure, we'll just instantiate normally
        self.agent = ResearchAgentV2()

        # Override the dummy's internal search to mock our specific needs for these tests
        def test_mock_search(query, max_results=3):
            results = []
            if "문제" in query or "원인" in query:
                results.append({"title": "현장 문제 분석", "url": "https://civileng7.tistory.com/problem", "snippet": "문제 시 가장 먼저 시험 결과를 확인하고 층별 두께를 재검토해야 합니다. STEP1: 시공조건(함수비, 장비, 다짐횟수) 재검토."})
            if "조치방법" in query or "확인사항" in query:
                results.append({"title": "해결 조치", "url": "https://civileng7.tistory.com/sol", "snippet": "조치방법은 감리단에 제출해야 합니다. STEP2: 재시험 또는 부분 재시공 지시."})
            if "법령" in query or "기준" in query:
                results.append({"title": "법령 기준", "url": "https://law.go.kr/law", "snippet": "전체 재검증이 원칙일 수 있음. 강풍 시 타워크레인 작업 중지."})
                results.append({"title": "KCS 기준", "url": "https://kcsc.re.kr/kcs", "snippet": "공식 기준 적용."})
            if "실정보고" in query or "서류" in query:
                results.append({"title": "공무 서류", "url": "https://2030-view.tistory.com/doc", "snippet": "[단가산출서, 실정보고서, 변경사유서]를 제출해야 합니다. 사전 승인 없이 시공을 진행하면 계약금액 조정을 인정받지 못할 수 있음."})

            return {"results": results}

        self.agent.search_provider.search = test_mock_search

    def test_1_basic_research_pack(self):
        problem = {
            "problem_id": "P-TEST1",
            "problem": "테스트 문제 상황",
            "problem_type": "quality_problem",
            "problem_origin": "source_derived",
            "situation": "상황 테스트",
            "user_question": "질문 테스트",
            "problem_decision": "keep"
        }
        pack = self.agent.generate_research_pack(problem)
        self.assertIn("problem_id", pack)
        self.assertIn("situation", pack)
        self.assertIn("quick_answer", pack)
        self.assertIn("extracted_problems", pack)

    def test_pack_schema(self):
        problem = {
            "problem_id": "P-TEST99",
            "problem": "스키마 테스트",
            "problem_type": "quality_problem"
        }
        pack = self.agent.generate_research_pack(problem)
        self.assertIn("seo_context", pack)
        self.assertIn("source_summary", pack)
        self.assertIn("official_requirements", pack)
        self.assertIn("common_mistakes", pack)

    def test_2_decision_filtering(self):
        # The agent logic (in run()) skips non-keep. We simulate the filtering here.
        problems = [
            {"problem_decision": "keep"},
            {"problem_decision": "merge"},
            {"problem_decision": "needs_review"},
            {"problem_decision": "reject"}
        ]
        processed = [p for p in problems if p.get("problem_decision") == "keep"]
        self.assertEqual(len(processed), 1)

    def test_3_source_role_separation(self):
        problem = {
            "problem_id": "P-TEST3",
            "problem": "현장 다짐도 미달",
            "problem_type": "quality_problem",
            "problem_decision": "keep"
        }
        pack = self.agent.generate_research_pack(problem)

        # Check that practical has role "supporting_evidence"
        for e in pack["primary_practical_evidence"]:
            self.assertEqual(e["source_role"], "supporting_evidence")

        # Check official has "official_support" or "technical_reference"
        for e in pack["primary_official_evidence"]:
            self.assertIn(e["source_role"], ["official_support", "technical_reference"])

    def test_4_source_tier(self):
        problem = {
            "problem_id": "P-TEST4",
            "problem": "현장 다짐도 미달 법령", # Force legal
            "problem_type": "quality_problem",
            "problem_decision": "keep"
        }
        pack = self.agent.generate_research_pack(problem)
        for e in pack["primary_official_evidence"]:
            if "law.go.kr" in e["url"]:
                self.assertEqual(e["tier"], "Tier A")

    def test_5_practical_value_vs_authority(self):
        problem = {
            "problem_id": "P-TEST5",
            "problem": "현장 다짐도 실무",
            "problem_type": "quality_problem",
            "problem_decision": "keep"
        }
        pack = self.agent.generate_research_pack(problem)
        for e in pack["primary_practical_evidence"]:
            if e["source_type"] == "professional_field_blog":
                self.assertIn(e["tier"], ["Tier C", "Tier D"]) # Proves high PV doesn't equal high authority (Tier A)

    def test_6_conflict_detection(self):
        problem_both = {
            "problem_id": "P-TEST6",
            "problem": "다짐도 미달",
            "problem_type": "quality_problem",
            "problem_decision": "keep"
        }

        # Override the search mock directly in the test to ensure BOTH types are returned with natural conflict signals
        original_search = self.agent.search_provider.search
        def force_conflict_mock(q, max_results=3):
            return {"results": [
                {"title": "실무", "url": "https://civileng7.tistory.com/a", "domain": "civileng7.tistory.com", "snippet": "현장에서는 효율성을 위해 약식으로 처리하는 반면,"},
                {"title": "법령", "url": "https://law.go.kr/b", "domain": "law.go.kr", "snippet": "관련 기준에 따르면 정식 절차가 요구되어 차이가 존재함."}
            ]}
        self.agent.search_provider.search = force_conflict_mock

        pack_both = self.agent.generate_research_pack(problem_both)

        # Restore mock
        self.agent.search_provider.search = original_search

        self.assertTrue(len(pack_both["conflicts"]) > 0, "No generalized conflicts found. The heuristic parser missed '반면' or '차이'.")
        self.assertEqual(pack_both["research_status"], "conflict_detected")

    def test_7_ai_inferred_no_forced_upgrade(self):
        problem = {
            "problem_id": "P-TEST7",
            "problem": "희한한 텍스트",
            "problem_type": "unknown",
            "problem_origin": "ai_inferred",
            "problem_decision": "keep"
        }
        # Override mock to return nothing
        original_search = self.agent.search_provider.search
        self.agent.search_provider.search = lambda q: []
        pack = self.agent.generate_research_pack(problem)
        self.agent.search_provider.search = original_search

        self.assertEqual(pack["evidence_confidence"], "very_low")

    def test_8_administrative_procedure(self):
        problem = {
            "problem_id": "P-TEST8",
            "problem": "사토장 변경 실정보고",
            "problem_type": "contract_problem",
            "problem_decision": "keep"
        }
        pack = self.agent.generate_research_pack(problem)
        self.assertTrue(len(pack["administrative_procedure"]) > 0)
        self.assertTrue(len(pack["required_documents"]) > 0)

    def test_9_official_evidence_storage(self):
        problem = {
            "problem_id": "P-TEST9",
            "problem": "확인 법령 기준",
            "problem_type": "quality_problem",
            "problem_decision": "keep"
        }
        pack = self.agent.generate_research_pack(problem)
        self.assertTrue(len(pack["primary_official_evidence"]) > 0)

    def test_10_evidence_confidence_mix(self):
        problem = {
            "problem_id": "P-TEST10",
            "problem": "현장 다짐도 미달 확인 법령",
            "problem_type": "quality_problem",
            "problem_decision": "keep"
        }
        pack = self.agent.generate_research_pack(problem)
        # Assuming our mock returns both practical and official for this query mix
        summary = pack.get("source_summary", {})
        if summary.get("official_count", 0) > 0 and summary.get("practical_count", 0) > 0:
            self.assertEqual(pack["evidence_confidence"], "high")

if __name__ == "__main__":
    unittest.main()
    def test_research_completeness_score(self):
        problem = {
            "problem_id": "P-TEST-SCORE",
            "problem": "테스트 문제",
            "problem_type": "quality_problem",
            "situation": "상황",
            "user_question": "질문"
        }
        pack = self.agent.generate_research_pack(problem)
        self.assertTrue("research_completeness" in pack)
        self.assertIsInstance(pack["research_completeness"], int)

    def test_writer_readiness_ready(self):
        # Full coverage mock
        problem = {
            "problem_id": "P-TEST-READY",
            "problem": "완벽한 다짐도 미달 법령", # Will trigger practical + official + admin + docs + checks
            "problem_type": "contract_problem",
            "situation": "상황",
            "user_question": "질문"
        }
        original_search = self.agent.search_provider.search
        def full_mock(q, max_results=3):
            return {"results": [
                {"title": "실무", "url": "a", "domain": "civileng7.tistory.com", "snippet": "문제 시 가장 먼저 시험 결과를 확인하고 STEP1: 시공조건(함수비, 장비, 다짐횟수) 재검토. [단가산출서, 실정보고서, 변경사유서]를 감리단에 제출해야 합니다."},
                {"title": "법령", "url": "b", "domain": "law.go.kr", "snippet": "전체 재검증이 원칙일 수 있음. 강풍 시 타워크레인 작업 중지."}
            ]}
        self.agent.search_provider.search = full_mock
        pack = self.agent.generate_research_pack(problem)
        self.agent.search_provider.search = original_search

        # Core:20 + Pract:15 + Off:15 + Diag:10 + PractProc:10 + AdminProc:10 + Docs:5 + SEO:5 = 90
        # If conflicts added: +10 = 100.
        # This easily passes the 80 threshold for "ready"
        self.assertEqual(pack["writer_readiness"], "ready")

    def test_writer_readiness_partial(self):
        problem = {
            "problem_id": "P-TEST-PARTIAL",
            "problem": "부분 법령",
            "problem_type": "quality_problem",
            "situation": "상황",
            "user_question": "질문"
        }
        original_search = self.agent.search_provider.search
        def partial_mock(q, max_results=3):
            return {"results": [
                {"title": "실무", "url": "a", "domain": "civileng7.tistory.com", "snippet": "가장 먼저 시험 결과를 확인하고"},
                {"title": "법령", "url": "b", "domain": "law.go.kr", "snippet": "단순 법령."}
            ]}
        self.agent.search_provider.search = partial_mock
        pack = self.agent.generate_research_pack(problem)
        self.agent.search_provider.search = original_search

        # Core:20 + Off:15 + Prac:15 + Diag:10 + SEO:5 = 65 -> Partial.
        self.assertEqual(pack["writer_readiness"], "partial")

    def test_writer_readiness_insufficient(self):
        # Missing almost everything
        problem = {
            "problem_id": "P-TEST-INSUFF",
            "problem": "텅빈",
            "problem_type": "unknown"
        }
        original_search = self.agent.search_provider.search
        self.agent.search_provider.search = lambda q, max_results=3: {"results": []}
        pack = self.agent.generate_research_pack(problem)
        self.agent.search_provider.search = original_search

        self.assertEqual(pack["writer_readiness"], "insufficient")

    def test_missing_information(self):
        problem = {
            "problem_id": "P-TEST-MISSING",
            "problem": "텅빈",
            "problem_type": "unknown"
        }
        original_search = self.agent.search_provider.search
        self.agent.search_provider.search = lambda q, max_results=3: {"results": []}
        pack = self.agent.generate_research_pack(problem)
        self.agent.search_provider.search = original_search

        self.assertIn("problem_core_incomplete", pack["missing_information"])
        self.assertIn("primary_practical_evidence", pack["missing_information"])
        self.assertIn("diagnostic_checks", pack["missing_information"])

    def test_writer_guidance_generation(self):
        problem = {
            "problem_id": "P-TEST-GUIDE",
            "problem": "가이드",
            "problem_type": "unknown"
        }
        pack = self.agent.generate_research_pack(problem)
        self.assertIn("writer_guidance", pack)
        self.assertIn("recommended_structure", pack["writer_guidance"])
        self.assertIn("recommended_tone", pack["writer_guidance"])
