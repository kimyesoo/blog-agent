import unittest
from writer_agent import WriterAgentV1

class TestWriterAgent(unittest.TestCase):
    def setUp(self):
        self.agent = WriterAgentV1()
        # Create a dummy JSON pack mapped to the V2.2 schema as requested
        self.dummy_pack = {
            "writer_readiness": "ready",
            "problem": "다짐도 미달",
            "topic": "현장 다짐도 미달 시 조치방법",
            "situation": "다짐도 85% 미달 발생",
            "practical_procedure": [
                {"step": 1, "action": "재다짐", "purpose": "밀도 확보"}
            ],
            "conflicts": [
                {
                    "type": "practice_vs_standard",
                    "practical_view": "실무/현장 관점 (약식 처리)",
                    "official_view": "법령/KCS (정식 절차 요구)",
                    "severity": "medium",
                    "status": "needs_review"
                }
            ],
            "seo_context": {
                "primary_keyword": "다짐도 미달",
                "secondary_keywords": ["시험", "조치"]
            }
        }

    def test_writer_blocks_insufficient_readiness(self):
        pack = {"writer_readiness": "insufficient"}
        res = self.agent.write(pack)
        self.assertEqual(res.get("status"), "blocked")

    def test_writer_adds_warning_for_partial_readiness(self):
        pack = self.dummy_pack.copy()
        pack["writer_readiness"] = "partial"
        res = self.agent.write(pack)
        # Verify markdown contains "> **주의:**" which is the warning for partial
        self.assertIn("> **주의:**", res["content_markdown"])

    def test_writer_generates_full_markdown(self):
        pack = self.dummy_pack.copy()
        res = self.agent.write(pack)

        self.assertTrue(res.get("validation_passed", False))

        md = res["content_markdown"]

        # Verify mandatory sections
        self.assertIn("## 1. 문제 상황", md)
        self.assertIn("## 10. FAQ", md)

        # Verify modified practical_view and official_view are rendered correctly
        self.assertIn("실무/현장 관점 (약식 처리)", md)
        self.assertIn("법령/KCS (정식 절차 요구)", md)
        self.assertIn("## 현장 관행과 공식 기준 차이", md)

if __name__ == "__main__":
    unittest.main()
