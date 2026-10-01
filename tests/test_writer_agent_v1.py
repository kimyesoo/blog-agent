import unittest
from writer_agent import WriterAgentV1

class TestWriterAgentV1(unittest.TestCase):
    def setUp(self):
        self.agent = WriterAgentV1()
        self.base_pack = {
            "writer_readiness": "ready",
            "problem": "다짐도 미달",
            "topic": "현장 다짐도 미달 시 조치방법",
            "situation": "다짐도 85% 미달 발생",
            "practical_procedure": [{"step": 1, "action": "재다짐", "purpose": "밀도 확보"}],
            "seo_context": {"primary_keyword": "다짐도 미달", "secondary_keywords": ["시험"]}
        }

    def test_writer_blocked(self):
        pack = {"writer_readiness": "insufficient"}
        res = self.agent.write(pack)
        self.assertEqual(res.get("status"), "blocked")

    def test_writer_partial_warning(self):
        pack = self.base_pack.copy()
        pack["writer_readiness"] = "partial"
        res = self.agent.write(pack)
        self.assertIn("본 문서는 실무 근거가 일부 부족한 상태에서 작성", res["content_markdown"])

    def test_prohibited_keywords(self):
        pack = self.base_pack.copy()
        pack["topic"] = "다짐도의 정의와 원리"
        res = self.agent.write(pack)
        self.assertEqual(res["quality_score"], 0)
        self.assertFalse(res["validation_passed"])

    def test_mandatory_sections(self):
        res = self.agent.write(self.base_pack)
        md = res["content_markdown"]
        self.assertIn("## 1. 문제 상황", md)
        self.assertIn("## 4. 현장 실무 조치", md)
        self.assertIn("## 10. FAQ", md)
        self.assertIn("## 9. 결론", md)
        self.assertTrue(res["validation_passed"])

    def test_conflict_generation(self):
        pack = self.base_pack.copy()
        pack["conflicts"] = [{
            "official_view": "전체 재검증",
            "practical_view": "부분 재시공"
        }]
        res = self.agent.write(pack)
        md = res["content_markdown"]
        self.assertIn("## 현장 관행과 공식 기준 차이", md)
        self.assertIn("현장에서는 부분 재시공", md)
        self.assertIn("하지만 최신 기준은 전체 재검증", md)
        self.assertIn("감리단과 협의 후 판단", md) # Rule check

if __name__ == "__main__":
    unittest.main()
