import unittest
import json
from problem_validation_agent import ProblemValidationAgent

class TestProblemValidation(unittest.TestCase):
    def setUp(self):
        self.agent = ProblemValidationAgent()

    def _test_case(self, title, subcategory, problem_type, origin, sources, expected_decisions, expected_confidence=None):
        problem = {
            "problem_id": "T-TEST",
            "problem": title,
            "domain": "test",
            "subcategory": subcategory,
            "problem_type": problem_type,
            "problem_origin": origin,
            "situation": "test",
            "user_question": "test",
            "discovery_sources": sources
        }
        validated = self.agent.validate_problems([problem])
        res = validated[0]
        self.assertIn(res["problem_decision"], expected_decisions)

        if expected_confidence:
            if isinstance(expected_confidence, list):
                self.assertIn(res["evidence_confidence"], expected_confidence)
            else:
                self.assertEqual(res["evidence_confidence"], expected_confidence)

        return res

    def test_1_source_derived(self):
        # 출처: civileng7 + public audit -> high or medium confidence
        sources = [
            {"source_type": "professional_field_blog"},
            {"source_type": "public_agency"}
        ]
        self._test_case("현장 다짐도가 기준에 미달", "다짐", "quality_problem", "source_derived", sources, ["keep"], ["high", "medium"])

    def test_2_official_and_practical(self):
        sources = [
            {"source_type": "professional_field_blog"},
            {"source_type": "legal"}
        ]
        self._test_case("사토장 변경으로 운반거리가 증가", "사토장", "contract_problem", "source_derived", sources, ["keep"], ["high", "medium"])

    def test_3_administrative_problem(self):
        sources = [{"source_type": "professional_field_blog"}]
        self._test_case("감리단에서 추가 서류를 요구", "품질관리", "supervision_response", "source_derived", sources, ["keep", "needs_review"])

    def test_4_theoretical_topic(self):
        # Should be rejected and not source derived natively
        self._test_case("흙의 압밀 기본 원리", "침하", "theoretical", "taxonomy_fallback", [], ["reject"])

    def test_5_duplicate_problem(self):
        # 0001 and 0006
        problems = [
            {
                "problem": "현장 다짐도가 기준에 미달",
                "subcategory": "다짐",
                "problem_type": "quality_problem",
                "problem_origin": "source_derived",
                "discovery_sources": [{"source_type": "professional_field_blog"}]
            },
            {
                "problem": "다짐도가 안 나오는 경우",
                "subcategory": "다짐",
                "problem_type": "quality_problem",
                "problem_origin": "source_derived",
                "discovery_sources": [{"source_type": "professional_field_blog"}]
            }
        ]
        validated = self.agent.validate_problems(problems)
        self.assertEqual(validated[1]["problem_decision"], "merge")

    def test_6_similar_but_not_identical(self):
        # 0002 and 0007
        problems = [
            {
                "problem": "사토장 변경으로 운반거리가 증가",
                "subcategory": "사토장",
                "problem_type": "contract_problem",
                "problem_origin": "source_derived",
                "discovery_sources": [{"source_type": "professional_field_blog"}]
            },
            {
                "problem": "설계와 실제 사토 운반거리가 달라진 경우",
                "subcategory": "사토장",
                "problem_type": "contract_problem",
                "problem_origin": "source_derived",
                "discovery_sources": [{"source_type": "professional_field_blog"}]
            }
        ]
        validated = self.agent.validate_problems(problems)
        self.assertIn(validated[1]["problem_decision"], ["needs_review", "merge"])

    def test_7_taxonomy_fallback(self):
        res = self._test_case("발파 기본 설계 원리", "발파", "theoretical", "taxonomy_fallback", [], ["reject"])
        self.assertEqual(res["problem_origin"], "taxonomy_fallback")
        self.assertEqual(res["evidence_confidence"], "very_low")

    def test_8_ai_inferred(self):
        res = self._test_case("연약지반 성토 중 원인 불명의 급격한 침하 발생", "침하", "construction_problem", "ai_inferred", [], ["keep", "needs_review"])
        self.assertEqual(res["problem_origin"], "ai_inferred")
        self.assertIn(res["evidence_confidence"], ["low", "very_low"])


if __name__ == "__main__":
    unittest.main()
