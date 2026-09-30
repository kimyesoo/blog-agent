import unittest
import json
from problem_validation_agent import ProblemValidationAgent

class TestProblemValidation(unittest.TestCase):
    def setUp(self):
        self.agent = ProblemValidationAgent()

    def _test_case(self, title, subcategory, problem_type, expected_decisions):
        problem = {
            "problem_id": "T-001",
            "problem": title,
            "domain": "test",
            "subcategory": subcategory,
            "problem_type": problem_type,
            "situation": "test",
            "user_question": "test",
            "discovery_sources": ["civileng7.tistory.com"]
        }
        # Run validation
        validated = self.agent.validate_problems([problem])
        self.assertIn(validated[0]["problem_decision"], expected_decisions)
        return validated[0]

    def test_1_field_problem(self):
        self._test_case("현장 다짐도가 기준에 미달", "다짐", "quality_problem", ["keep"])

    def test_2_admin_problem(self):
        self._test_case("사토장 변경으로 운반거리가 증가", "사토장", "contract_problem", ["keep"])

    def test_3_supervision_problem(self):
        self._test_case("감리단에서 추가 서류를 요구", "품질관리", "administrative_problem", ["keep", "needs_review"])

    def test_4_educational_topic(self):
        self._test_case("흙의 압밀 기본 원리", "침하", "theoretical_problem", ["reject", "needs_review"])

    def test_5_deep_technical_topic(self):
        self._test_case("발파 기본 설계 원리", "발파", "theoretical_problem", ["reject", "needs_review"])

    def test_6_duplicate_merge(self):
        problems = [
            {
                "problem_id": "T-100",
                "problem": "현장 다짐도가 기준에 미달인 경우",
                "domain": "토공",
                "subcategory": "다짐",
                "problem_type": "quality_problem",
                "discovery_sources": ["civileng7.tistory.com"]
            },
            {
                "problem_id": "T-101",
                "problem": "다짐도가 안 나오는 경우",
                "domain": "토공",
                "subcategory": "다짐",
                "problem_type": "quality_problem",
                "discovery_sources": ["civileng7.tistory.com"]
            }
        ]
        validated = self.agent.validate_problems(problems)
        self.assertEqual(validated[1]["problem_decision"], "merge")

    def test_7_practical_and_admin(self):
        self._test_case("설계와 실제 사토 운반거리가 달라진 경우", "사토장", "contract_problem", ["keep"])


if __name__ == "__main__":
    unittest.main()
