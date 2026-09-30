import json
import os
import sys

# Ensure module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topic_research_agent import TopicResearchAgentV2

def test_v2_agent():
    agent = TopicResearchAgentV2()

    # 1. Check taxonomy reading
    assert os.path.exists(agent.taxonomy_file), "Taxonomy file missing"
    with open(agent.taxonomy_file, 'r') as f:
        tax = json.load(f)
    assert len(tax) > 0, "Taxonomy is empty"

    # 2. Check title generation format (not hardcoded)
    title, ctype = agent.generate_title_and_type("토공", "시공 방법")
    assert "토공" in title, "Subcategory must be in the title"
    assert ctype == "시공 가이드", "Content type mismatch"

    # 3. Check duplicate logic
    mock_existing = [{"title": "토공 현장 시공방법 및 실무 가이드"}]
    is_dup = agent.is_duplicate("토공 현장 시공방법 및 실무 가이드", mock_existing, set())
    assert is_dup == True, "Exact duplicate not caught"

    # 4. Check quality filter logic
    assert agent.validate_quality("품질기준 관련 시공방법", "시공 방법") == False, "Quality filter failed to block illogical combination"

    print("Topic Research Agent V2 automated tests passed.")

if __name__ == '__main__':
    test_v2_agent()
