import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topic_research_agent import TopicResearchAgentV2_2

def test_v2_2_agent():
    agent = TopicResearchAgentV2_2()

    with open('taxonomy.json', 'r') as f:
        taxonomy = json.load(f)

    # 1. Parent-child integrity test
    assert agent.verify_taxonomy_integrity("토공", "펌프장", taxonomy) == False, "Failed to catch invalid child (토공 + 펌프장)"
    assert agent.verify_taxonomy_integrity("상하수도", "펌프장", taxonomy) == True, "Failed to validate correct child (상하수도 + 펌프장)"

    # 2. Compatibility mapping (LOW -> discard, MEDIUM/HIGH -> keep)
    eval_bad = agent.evaluate_quality("적산 및 공사비", "재료비", "시공 방법")
    assert eval_bad["decision"] == "discard", "Failed to discard LOW compatibility"
    assert eval_bad["metrics"]["intent_level"] == "LOW", "재료비 + 시공 방법 must be LOW"

    eval_ok = agent.evaluate_quality("건설안전", "가설구조물안전", "시험/측정")
    assert eval_ok["decision"] == "keep", "Failed to keep MEDIUM compatibility"
    assert eval_ok["metrics"]["intent_level"] == "MEDIUM", "Generic intent should be MEDIUM"

    eval_great = agent.evaluate_quality("토공", "발파", "시험/측정")
    assert eval_great["decision"] == "keep", "Failed to keep HIGH compatibility"
    assert eval_great["metrics"]["intent_level"] == "HIGH", "발파 + 시험/측정 must be HIGH"

    # 3. Duplicate False Positive check
    # They should NOT be duplicates just because they have filler words.
    generated_concepts = set()
    generated_concepts.add("굴착안전_점검/검사")

    # "계약 관련 기준" vs "굴착안전" => sub_cat + intent check
    is_dup, reason = agent.is_duplicate("계약 관련 기준", "현장 적용", [], generated_concepts)
    assert is_dup == False, "Wrongly flagged distinct technical core as duplicate (False Positive)"

    # 4. Valid different-intent topics
    generated_concepts.add("들밀도 시험_시공 방법")
    is_dup2, reason2 = agent.is_duplicate("들밀도 시험", "계산/산정", [], generated_concepts)
    assert is_dup2 == False, "Wrongly flagged different intent on same core as duplicate"

    # 5. Invalid generic topics
    eval_gen = agent.evaluate_quality("구조물", "구조물", "설계")
    assert eval_gen["decision"] == "regenerate", "Failed to force regeneration on generic topic"

    print("V2.2 tests passed successfully.")

if __name__ == '__main__':
    test_v2_2_agent()
