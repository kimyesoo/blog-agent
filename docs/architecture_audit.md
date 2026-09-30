# Architecture Audit Report

## 1. Executive Summary
The system is currently composed of multiple agents in a data processing pipeline that progresses from discovering practical problems in civil engineering domains, to validating them, mapping them to topics, conducting research via simulated SERP APIs, and finally generating structured markdown posts using a Writer Agent. The pipeline emphasizes avoiding AI hallucinations by relying heavily on deterministic validation steps, clear structural schemas, configurable weightings (`weights.json`), and separating practical field data from official administrative data.

## 2. Entry Points
- `problem_discovery_agent.py` (`if __name__ == "__main__":`) - Entry point to discover initial problem objects (P-XXXX).
- `problem_validation_agent.py` (`if __name__ == "__main__":`) - Validates the discovered problems against existing topics and heuristics.
- `topic_agent.py` (`if __name__ == "__main__":`) - Maps valid problem candidates into topic structures.
- `research_serp_agent.py` (`if __name__ == '__main__':`) - Performs search via CLI or mock providers. Used directly to test search capabilities.
- `research_agent.py` (`if __name__ == "__main__":`) - Aggregates search sources into Research Packs (R-XXXX).
- `writer_agent.py` (`if __name__ == "__main__":`) - Drafts markdown posts from complete Research Packs.
- `topic_search_research_agent.py` (`if __name__ == "__main__":`) - (Legacy/Experimental) Conducts topic search/research using Tavily/mock provider.
- `topic_opportunity_scoring_agent.py`, `topic_prioritization_agent.py`, `topic_validation_report.py`, `topic_validation_agent.py`, `generate_weight_sensitivity_report.py`, `extract_v2_1_metrics.py` - Standalone/utility entry points for reporting, metrics extraction, and legacy agent pipelines.

## 3. Dependency Graph
```text
ProblemDiscoveryAgent
    ↓ (P-XXXX)
ProblemValidationAgent
    ↓ (Validated P-XXXX)
TopicAgent
    ↓ (Topic Candidates)
ResearchSerpAgent (Used by ResearchAgent)
    ↓ (Searched Sources)
ResearchAgent
    ↓ (Research Pack R-XXXX)
WriterAgent
    ↓ (P-XXXX.md Output)
```

## 4. Production Files
- `problem_discovery_agent.py`: Initial problem generation.
- `problem_validation_agent.py`: Validates problem definitions based on origin and confidence.
- `topic_agent.py`: Maps problems to SEO-friendly topics.
- `research_serp_agent.py`: Core SERP search interface and Source Classifier.
- `research_agent.py`: Converts topics/problems into structured research packs based on `research_serp_agent.py`.
- `writer_agent.py`: Final agent converting research packs into standard markdown articles.
- `weights.json` (inside `research/` directory): Drives evidence and practical scoring weight configurations.
- `taxonomy.json`: Outlines domains and subcategories for the civil engineering fields.
- `source_registry.json` & `legal_source_registry.json`: Registers domains mapping to specific tiers.

## 5. Legacy Files
- `topic_search_research_agent.py`: Used prior to separating concerns into the Problem-centric pipeline. Still available but mostly replaced by `research_agent.py` and `research_serp_agent.py`.
- `topic_opportunity_scoring_agent.py`: An old module to score topics.
- `topic_prioritization_agent.py`: Old prioritization logic.
- `topic_validation_agent.py`: Validates topics rather than problems (used in older V1/V1.2 topic-centric pipelines).

## 6. Experimental Files
- `extract_v2_1_metrics.py`: Utility to pull metrics out of experimental topic pipelines.
- `modify_packs.py`: Quick hack script to alter generated research pack JSONs during testing.
- `generate_audit_report.py` / `generate_weight_sensitivity_report.py`: Report generating scripts.
- `audit_test.py`, `audit_test2.py`, `audit_test3.py`: Temporary audit scripts.

## 7. Test Files
- `tests/test_problem_agents.py`: Validates problem AI inference, source derivation, taxonomy fallbacks, duplicate detection.
- `tests/test_research_agent_v2.py`: Huge test suite for verifying Research Pack schemas, decision filtering, source tier separation, conflict detection, completeness scoring, and writer readiness states.
- `tests/test_taxonomy.py`: Validates schema parsing of `taxonomy.json`.
- `tests/test_topic_research_agent_v2.py`, `test_topic_research_agent_v2_1.py`, `test_topic_research_agent_v2_2.py`: Validating legacy/older topic research agent logic.
- `tests/test_writer_agent_v1.py`: Validates the Writer Agent logic, including writer blocking, partial warnings, prohibited keywords, mandatory section checks, and conflict section generation.

## 8. Config Files
- `taxonomy.json`: Used by topic generators (`topic_research_agent.py`) to constrain domain areas.
- `research/weights.json`: Actively used by SERP/Research agents to define archetype-based weights for sources. Highly critical.
- `research/source_registry.json`: Lists the tiers and domains for standard construction resources.
- `research/legal_source_registry.json`: Domain mapping for legal, official, administrative resources.

## 9. Pipeline Contracts
### Problem Discovery Output
- fields: `problem_id`, `problem`, `domain`, `subcategory`, `problem_type`, `problem_origin`, `situation`, `existing_topics`

### Validation Output
- fields: `decision` ("keep", "reject", "needs_review", "merge"), `confidence` ("high", "medium", "low", "very_low"), `reason`, `duplicate_of`

### Research Pack Output
- fields: `research_pack_id`, `problem_id`, `problem`, `topic`, `status`, `metadata`, `sources` (list), `extracted_information` (dict including `actionable_procedures`, `diagnostic_checks`, `administrative_requirements`, `official_evidence`, `conflicts`), `analysis` (dict including `completeness`, `writer_readiness`)

### Writer Input
- fields: The exact `Research Pack Output` schema JSON.

### Writer Output
- fields: A full `.md` string matching the rigid 10-section blog structure format, which gets written to `writer_output/P-XXXX.md`.

## 10. Duplicate Logic
- **SourceClassifier**:
  - Defined in `research_serp_agent.py`.
  - Used by `research_agent.py`.
  - Older/legacy forms might exist in `topic_search_research_agent.py` mapping to `get_provider`.
- **JSON Loading**:
  - `load_json`, `load_candidates`, `load_existing_posts` functions duplicated across `topic_validation_agent.py`, `topic_validation_report.py`, `topic_search_research_agent.py`.
- **Problem Validation**:
  - Evaluated partly in `problem_validation_agent.py` (`evaluate_evidence_confidence`), but heavily tied to similar logic in `tests/test_problem_agents.py` and old `topic_validation_agent.py`.

## 11. Dead Code Candidates
- `topic_research_agent.py`, `topic_search_research_agent.py`, `topic_validation_agent.py`, `topic_opportunity_scoring_agent.py`, `topic_prioritization_agent.py`: High probability of being dead/legacy since the pipeline has pivoted to the `problem_discovery_agent` -> `problem_validation_agent` -> `topic_agent` -> `research_agent` -> `writer_agent` flow.
- `audit_test.py`, `audit_test2.py`, `audit_test3.py`: Obvious scratchpad dead code.

## 12. Test Coverage
- Overall coverage is very healthy for the critical new path (Problem Validation, Research, Writer).
- `test_research_agent_v2.py`: 15+ tests confirming research packing, grading, source handling.
- `test_writer_agent_v1.py`: 5 tests enforcing formatting constraints, block logic, and prohibited words.
- `test_problem_agents.py`: 8 tests validating origin and deduplication.
- Covers production files `problem_validation_agent.py`, `research_agent.py`, `writer_agent.py` effectively.

## 13. Risks
- **Legacy Clutter**: Dozens of `topic_*.py` files and `v2_1`, `v2_2` scripts pollute the namespace, causing confusion over what the actual production entry points are.
- **Shared Helpers**: JSON loading is manually written in almost every file rather than centralized.
- **Config Locality**: Configs like `taxonomy.json` are at the root, while `weights.json` and `source_registry.json` are inside the `research/` directory.

## 14. Recommended Cleanup Order
1. Consolidate shared utility functions (like `load_json`, `save_json`, `normalize_title`) into a `utils/` or `core/` package.
2. Remove scratchpad scripts (`audit_test*.py`, `modify_packs.py`).
3. Move old `topic_*.py` files into a `legacy/` or `archive/` folder to clarify that `problem_*.py` and `research_agent.py` are the new path.
4. Unify the configuration loading mechanism, possibly placing all `.json` configs into a `config/` directory.
