import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topic_research_agent import TopicResearchAgentV2_1

def test_v2_1_agent():
    agent = TopicResearchAgentV2_1()

    # 1. Semantic Check
    res_good = agent.evaluate_quality("적산 및 공사비", "수량산출", "계산/산정")
    assert "intent_mismatch" not in res_good["flags"], "Failed to identify a good match"

    res_bad = agent.evaluate_quality("적산 및 공사비", "재료비", "시공 방법")
    assert "intent_mismatch" in res_bad["flags"], "Failed to flag bad combination"

    # 2. Too Generic Check
    res_gen = agent.evaluate_quality("구조물", "구조물", "설계")
    assert "too_generic" in res_gen["flags"], "Failed to flag too generic category"

    # 3. Duplicate concept check
    existing_concepts = set(["재료비_계산/산정"])
    is_dup, reason = agent.is_duplicate("재료비 산정", "계산/산정", "재료비", [], existing_concepts)
    assert is_dup == True and reason == "duplicate_concept", "Failed concept duplicate check"

    # 4. Near duplicate check with broad existing (should NOT be a duplicate)
    existing_posts = [{"title": "들밀도 시험"}]
    is_dup, reason = agent.is_duplicate("들밀도 시험 계산 방법", "계산/산정", "들밀도 시험", existing_posts, set())
    assert is_dup == False, "Wrongly flagged a narrow topic as a duplicate of a broad post"

    print("V2.1 tests passed successfully.")

if __name__ == '__main__':
    test_v2_1_agent()
