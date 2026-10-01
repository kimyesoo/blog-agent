# Project Structure Report V2.2

## Production Files
Currently active pipeline files handling core generation, processing, and outputs:
- `problem_discovery_agent.py`
- `problem_validation_agent.py`
- `topic_agent.py`
- `research_serp_agent.py`
- `research_agent.py` (Now upgraded to V2.2)
- `writer_agent.py`
- `taxonomy.json`
- `research/weights.json`
- `research/source_registry.json`
- `research/legal_source_registry.json`

## Legacy Files & Archive Candidates
These files represent older implementations, superseded components, or V1/V1.2 logic. They should be considered for archival:
- `topic_search_research_agent.py` (Superseded by `research_agent.py` and `research_serp_agent.py`)
- `topic_validation_agent.py` (Superseded by problem validation and V2.2 research logic)
- `topic_validation_report.py`
- `topic_opportunity_scoring_agent.py`
- `topic_prioritization_agent.py`
- `topic_research_agent.py`

## Test Files
- `tests/test_problem_agents.py`
- `tests/test_taxonomy.py`
- `tests/test_writer_agent_v1.py`
- `tests/test_research_agent_v2.py` (Upgraded with V2.2 procedural extraction tests)
- Legacy Tests: `tests/test_topic_research_agent_v2.py`, `tests/test_topic_research_agent_v2_1.py`, `tests/test_topic_research_agent_v2_2.py`

## Patch / Debug / Utility Files
These files were created to fix bugs, test changes mid-pipeline, or report statuses. Many have been cleaned up, but those remaining include:
- `extract_v2_1_metrics.py`
- `generate_audit_report.py`
- `generate_weight_sensitivity_report.py`
- `modify_packs.py`
