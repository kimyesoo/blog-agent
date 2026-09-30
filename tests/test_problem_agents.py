import unittest
import json
from problem_validation_agent import ProblemValidationAgent

class TestProblemValidation(unittest.TestCase):
    def setUp(self):
        self.agent = ProblemValidationAgent()

    def _test_case(self, title, subcategory, problem_type, origin, sources, expected_decisions, expected_confidence=None, mock_score=None):
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

        # We process manually to force scores if needed for testing logic branches
        p = self.agent.score_problem(problem)
        if mock_score is not None:
            p["practical_value"] = mock_score

        validated = self.agent.validate_problems([p])
        res = validated[0]
        self.assertIn(res["problem_decision"], expected_decisions, f"Failed on {title}: {res['problem_decision']}")

        if expected_confidence:
            if isinstance(expected_confidence, list):
                self.assertIn(res["evidence_confidence"], expected_confidence)
            else:
                self.assertEqual(res["evidence_confidence"], expected_confidence)

        return res

    def test_1_ai_inferred_needs_review(self):
        # Even with high practical value, ai_inferred must be needs_review
        self._test_case("연약지반 성토 중 원인 불명의 급격한 침하 발생", "침하", "construction_problem", "ai_inferred", [], ["needs_review"], ["low"])

    def test_2_source_derived_upgrade(self):
        # AI inferred upgraded to source_derived with medium/high evidence
        sources = [{"source_type": "professional_field_blog"}]
        self._test_case("연약지반 성토 중 원인 불명의 급격한 침하 발생", "침하", "construction_problem", "source_derived", sources, ["keep"], ["medium"])

    def test_3_taxonomy_fallback_reject(self):
        self._test_case("흙의 압밀 기본 원리", "침하", "theoretical", "taxonomy_fallback", [], ["reject"], ["very_low"])

    def test_4_high_evidence_keep(self):
        # source_derived + high evidence + practical value 55 -> keep instead of needs_review
        sources = [
            {"source_type": "professional_field_blog"},
            {"source_type": "technical_standard"}
        ]
        self._test_case("아스팔트 포장 후 조기 포트홀 발생", "포장", "quality_problem", "source_derived", sources, ["keep"], ["high"], mock_score=55)

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
                "problem": "현장 다짐도가 안 나오는 경우",
                "subcategory": "다짐",
                "problem_type": "quality_problem",
                "problem_origin": "source_derived",
                "discovery_sources": [{"source_type": "professional_field_blog"}]
            }
        ]
        validated = self.agent.validate_problems(problems)
        self.assertEqual(validated[1]["problem_decision"], "merge")

    def test_6_source_derived_medium_needs_review(self):
        # source_derived + medium evidence + low PV -> needs_review
        sources = [{"source_type": "professional_field_blog"}]
        self._test_case("반입된 철근에 심한 녹이 발생한 경우", "철근", "material_problem", "source_derived", sources, ["needs_review"], ["medium"], mock_score=55)

    def test_7_similar_nuance_needs_review(self):
        # P-0013 and P-0018
        problems = [
            {
                "problem": "굴착 중 설계에 없는 대규모 암반 발견",
                "subcategory": "굴착",
                "problem_type": "site_condition_change",
                "problem_origin": "source_derived",
                "discovery_sources": [{"source_type": "professional_field_blog"}]
            },
            {
                "problem": "터파기 중 설계와 다른 암반층 노출",
                "subcategory": "굴착",
                "problem_type": "site_condition_change",
                "problem_origin": "source_derived",
                "discovery_sources": [{"source_type": "professional_field_blog"}]
            }
        ]
        validated = self.agent.validate_problems(problems)
        # 2nd problem should be needs_review to retain topic diversity, not auto-merge
        self.assertEqual(validated[1]["problem_decision"], "needs_review")

    def test_8_confidence_independence(self):
        # problem_origin and evidence_confidence calculate independently
        res1 = self._test_case("테스트1", "테스트", "test", "source_derived", [{"source_type": "legal"}], ["needs_review", "keep"], ["medium"])
        res2 = self._test_case("테스트2", "테스트", "test", "ai_inferred", [], ["needs_review"], ["low"])
        res3 = self._test_case("테스트3", "테스트", "test", "taxonomy_fallback", [], ["reject"], ["very_low"])

        self.assertEqual(res1["problem_origin"], "source_derived")
        self.assertEqual(res2["problem_origin"], "ai_inferred")
        self.assertEqual(res3["problem_origin"], "taxonomy_fallback")

if __name__ == "__main__":
    unittest.main()
