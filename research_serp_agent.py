
import json
import os
import argparse
import hashlib
from datetime import datetime

# --- PROVIDERS ---
class SearchProvider:
    def search(self, query, limit=10):
        raise NotImplementedError

class MockSearchProvider(SearchProvider):
    def search(self, query, limit=10):
        results = []

        # Legal
        if "법령" in query or "규정" in query or "법률" in query or "산업안전" in query or "계약" in query:
            if "원리" not in query and "시험" not in query:
                results.append({
                    "title": f"국가법령정보센터 - {query} 관련 법령",
                    "url": "https://www.law.go.kr/법령/test",
                    "domain": "law.go.kr",
                    "snippet": f"{query}에 관한 조항입니다.",
                    "is_pdf": False,
                    "effective_date": "2023-01-01",
                    "status": "active"
                })

        # Technical Standard
        if "기준" in query or "KCS" in query or "KDS" in query or "설계" in query:
            results.append({
                "title": f"국가건설기준센터 - {query} 공식 기준",
                "url": "https://www.kcsc.re.kr/some_standard.pdf",
                "domain": "kcsc.re.kr",
                "snippet": f"{query}에 대한 국가건설기준(KCS/KDS).",
                "is_pdf": True
            })

        # Official Guidelines / Public Guidance
        if "지침" in query or "매뉴얼" in query:
            results.append({
                "title": f"{query} 현장 실무 지침서",
                "url": "https://www.codil.or.kr/report_123.pdf",
                "domain": "codil.or.kr",
                "snippet": f"현장 시공 중 발생하는 {query} 현황 및 지침 분석.",
                "is_pdf": True
            })

        # Field Practice (Blogs, Industry) - Emphasizing problem solving and practical experience
        if "문제점" in query or "대책" in query or "시공" in query or "장비" in query or "사례" in query or "계산" in query or "시험" in query:
            for i in range(2):
                results.append({
                    "title": f"[토목 실무] {query} 현장 적용 노하우 및 해결책",
                    "url": f"https://civileng7.tistory.com/post{i}",
                    "domain": "tistory.com",
                    "snippet": f"현장에서 직접 겪은 {query} 사례 및 실무 팁, 해결책.",
                    "is_pdf": False
                })

        # Catch-all generic blogs if empty
        if not results:
            results.append({
                "title": f"[토목 실무] {query} 완벽 정리",
                "url": f"https://civileng7.tistory.com/generic",
                "domain": "tistory.com",
                "snippet": f"실무자를 위한 {query} 개념 이해.",
                "is_pdf": False
            })

        return results[:limit]

# --- CLASSIFIERS ---
class SourceClassifier:
    def __init__(self, registry_file='research/source_registry.json', legal_registry_file='research/legal_source_registry.json'):
        self.registry = {}
        if os.path.exists(registry_file):
            with open(registry_file, 'r') as f:
                self.registry = json.load(f)

        if os.path.exists(legal_registry_file):
            with open(legal_registry_file, 'r') as f:
                self.registry.update(json.load(f))

        self.official_domains = ["go.kr", "or.kr", "re.kr"]
        self.academic_domains = ["ac.kr"]

    def classify(self, domain, is_pdf):
        if domain in self.registry:
            reg = self.registry[domain]
            return reg.get("source_type", "unknown"), reg.get("authority_level", "unknown"), reg.get("organization", "unknown")

        for suffix in self.official_domains:
            if domain.endswith(suffix):
                return "official_guideline", "high", "Public Institution"

        for suffix in self.academic_domains:
            if domain.endswith(suffix):
                return "academic", "medium", "University/Research"

        if domain.endswith("tistory.com") or domain.endswith("naver.com"):
            return "field_practice", "medium", "Field Blog"

        if is_pdf:
            return "field_practice", "medium", "Industry Document"

        return "unknown", "unknown", "unknown"

class QueryIntentClassifier:
    def __init__(self):
        self.mapping = {
            "시공 방법": "procedural",
            "계산/산정": "calculation",
            "문제 해결": "troubleshooting",
            "원인과 대책": "troubleshooting",
            "기준/규정": "regulation",
            "시험/측정": "procedural",
            "품질관리": "quality",
            "설계": "design",
            "점검/검사": "inspection",
            "현장 적용": "procedural",
            "검토": "informational",
            "비교": "comparison",
            "사례": "case",
            "장비/자재": "informational",
            "유지관리": "maintenance",
            "개념 이해": "informational"
        }

    def classify_query(self, original_topic_intent):
        return self.mapping.get(original_topic_intent, "informational")

class ArchetypeClassifier:
    def classify(self, topic_data):
        main_cat = topic_data.get("topic_cluster", "")
        intent = topic_data.get("search_intent", "")

        # 1. Regulatory
        if main_cat in ["건설안전", "건설공무", "건설기준 및 법규"] or intent in ["기준/규정"]:
            if intent not in ["시공 방법", "장비/자재", "문제 해결"]:
                return "regulatory", {"law": 50, "public_guidance": 25, "technical_standard": 15, "field_practice": 10}

        # 2. Construction Methods & Execution
        if intent in ["시공 방법", "비교", "장비/자재", "품질관리", "문제 해결", "원인과 대책"]:
            return "construction_methods", {"field_practice": 45, "technical_standard": 35, "public_guidance": 15, "law": 5}

        # 3. Technical Standard
        if main_cat in ["구조물", "교량", "도로", "터널"] and intent in ["설계", "검토"]:
            return "technical_standard", {"technical_standard": 50, "field_practice": 30, "public_guidance": 10, "law": 10}

        # 4. Field Problem Solving (Default for physical operations, testing, field work)
        return "field_problem_solving", {"field_practice": 50, "technical_standard": 30, "public_guidance": 15, "law": 5}


# --- AGENT ---
class ResearchSerpAgent:
    def __init__(self, provider_name="mock"):
        self.cache_dir = "research/cache"
        os.makedirs(self.cache_dir, exist_ok=True)

        self.classifier = SourceClassifier()
        self.intent_classifier = QueryIntentClassifier()
        self.archetype_classifier = ArchetypeClassifier()
        self.provider_name = provider_name

        if provider_name == "mock":
            self.provider = MockSearchProvider()
        else:
            self.provider = MockSearchProvider()

    def generate_queries(self, topic_data, archetype):
        core = topic_data.get("technical_core", "")
        intent = topic_data.get("search_intent", "")

        queries = []

        # Archetype specific queries ensuring "Practical Value First"
        if archetype == "regulatory":
            queries.extend([f"{core} 관련 법령", f"산업안전보건법 {core}", f"{core} 규정", f"{core} 지침"])
        elif archetype == "technical_standard":
            queries.extend([f"KDS {core}", f"{core} 설계기준", f"{core} 검토사항", f"{core} 시공 사례"])
        elif archetype == "construction_methods":
            queries.extend([f"{core} 시공순서", f"{core} 공법 비교", f"{core} 장비 선정", f"{core} 현장 문제 해결", f"{core} 품질 문제"])
        elif archetype == "field_problem_solving":
            queries.extend([f"{core} 원인", f"{core} 해결책", f"{core} 현장 적용", f"{core} 시험방법", f"{core} 자주하는 실수"])

        # Fallback to core intents if specific ones fail to trigger
        if not queries:
            queries.append(f"{core} {intent}")

        return list(set(queries))[:4] # Focus on 4 distinct queries

    def search_with_cache(self, query):
        cache_key = hashlib.md5(query.encode('utf-8')).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)

        try:
            results = self.provider.search(query)
            with open(cache_file, 'w') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            return results
        except Exception as e:
            print(f"Search failed for {query}: {e}")
            return []

    def evaluate_legal_relevance(self, legal_evidence, topic_data, archetype):
        # Stop forcing laws onto purely physical construction topics
        if archetype in ["field_problem_solving", "construction_methods"]:
            return "none", "해당 실무 주제는 직접적인 법령보다 현장 경험 및 기술 지침이 우선됨"

        if not legal_evidence:
            return "none", "해당 주제를 직접 규정하는 법령을 확인하지 못함"

        core = topic_data.get("technical_core", "")
        for ev in legal_evidence:
            if core in ev.get("title", ""):
                return "direct", "관련 법령 내 직접 명시 확인됨"

        return "indirect", "관련 법적 배경이 존재하나 세부 규정은 기술기준 등에서 다루어질 가능성 높음"

    def run(self, input_file, output_summary='research/research_summary.json', output_results='research/search_results.json'):
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found.")
            return

        with open(input_file, 'r') as f:
            topics = json.load(f)

        all_results = []
        all_summaries = []

        existing_posts = []
        if os.path.exists("content_db/posts.json"):
            with open("content_db/posts.json", "r") as f:
                existing_posts = json.load(f)

        for t in topics:
            topic_title = t["topic"]

            # Determine Archetype based on Practical Value First policy
            archetype, weights = self.archetype_classifier.classify(t)

            queries = self.generate_queries(t, archetype)

            topic_serp = []
            source_dist = {"legal": 0, "technical_standard": 0, "official_guideline": 0, "academic": 0, "field_practice": 0, "unknown": 0}
            intent_dist = {}
            domains_seen = set()

            legal_basis = []
            technical_standards = []
            official_guidelines = []
            field_practices = []

            mapped_intent = self.intent_classifier.classify_query(t.get("search_intent", ""))

            for q in queries:
                res = self.search_with_cache(q)

                for r in res:
                    domain = r["domain"]
                    stype, auth, org = self.classifier.classify(domain, r.get("is_pdf", False))
                    r["source_type"] = stype
                    r["authority_level"] = auth

                    domains_seen.add(domain)
                    if stype in source_dist:
                        source_dist[stype] += 1

                    evidence_item = {
                        "title": r["title"],
                        "source_type": stype,
                        "url": r["url"]
                    }
                    if stype == "legal":
                        evidence_item["effective_date"] = r.get("effective_date", "unknown")
                        evidence_item["status"] = r.get("status", "unknown")

                    if stype == "legal" and evidence_item not in legal_basis:
                        legal_basis.append(evidence_item)
                    elif stype == "technical_standard" and evidence_item not in technical_standards:
                        technical_standards.append(evidence_item)
                    elif stype == "official_guideline" and evidence_item not in official_guidelines:
                        official_guidelines.append(evidence_item)
                    elif stype == "field_practice" and len(field_practices) < 5 and evidence_item not in field_practices:
                        # Cap field practice logs to 5 so we don't bloat JSON with generic blogs unnecessarily
                        field_practices.append(evidence_item)

                    r["query_used"] = q
                    r["query_intent"] = mapped_intent

                    if mapped_intent in intent_dist:
                        intent_dist[mapped_intent] += 1
                    else:
                        intent_dist[mapped_intent] = 1

                    topic_serp.append(r)

            overlap = "none"
            for ep in existing_posts:
                ep_title = ep.get("title", "")
                if topic_title == ep_title:
                    overlap = "high"
                    break
                elif t.get("technical_core", "") in ep_title:
                    overlap = "possible"

            content_gap = "high" if overlap == "none" else ("partial" if overlap == "possible" else "none")

            leg_rel, leg_reason = self.evaluate_legal_relevance(legal_basis, t, archetype)

            conflict_detected = False
            legal_status = "complete" if source_dist["legal"] > 0 or leg_rel == "none" else "insufficient"

            # Revised Research Readiness mapping Practical Priorities
            readiness = "low"

            if archetype == "regulatory" and source_dist["legal"] > 0:
                readiness = "high"
            elif archetype == "technical_standard" and source_dist["technical_standard"] > 0:
                readiness = "high"
            elif archetype in ["field_problem_solving", "construction_methods"]:
                # Require field practice (blogs, industry manuals) explicitly for high readiness.
                if source_dist["field_practice"] >= 2:
                    readiness = "high"
                elif source_dist["field_practice"] > 0:
                    readiness = "medium"
            elif len(topic_serp) > 0:
                readiness = "medium"

            summary = {
                "topic": topic_title,
                "content_archetype": archetype,
                "evidence_weight": weights,
                "query_count": len(queries),
                "result_count": len(topic_serp),
                "search_intent_distribution": intent_dist,
                "source_distribution": source_dist,
                "unique_domains": len(domains_seen),
                "existing_content_overlap": overlap,
                "content_gap": content_gap,
                "research_readiness": readiness,
                "legal_coverage_report": {
                    "legal_relevance": leg_rel,
                    "legal_relevance_reason": leg_reason,
                    "legal_currentness_checked": True if source_dist["legal"] > 0 else False,
                    "legal_conflict_detected": conflict_detected,
                    "legal_research_status": legal_status
                },
                "evidence_hierarchy": {
                    "legal_basis": legal_basis,
                    "technical_standards": technical_standards,
                    "official_guidelines": official_guidelines,
                    "field_practices": field_practices
                }
            }

            all_summaries.append(summary)
            all_results.append({
                "topic": topic_title,
                "queries": queries,
                "serp_results": topic_serp
            })

        with open(output_summary, 'w') as f:
            json.dump(all_summaries, f, ensure_ascii=False, indent=2)

        with open(output_results, 'w') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        all_queries = []
        for r in all_results:
            all_queries.append({
                "topic": r["topic"],
                "queries": r["queries"]
            })

        with open('research/research_queries.json', 'w') as f:
            json.dump(all_queries, f, ensure_ascii=False, indent=2)

        print(f"Research SERP processing complete for {len(topics)} topics.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Research SERP Agent")
    parser.add_argument('--input', type=str, default='topic_research/v2_2_test_candidates.json')
    parser.add_argument('--provider', type=str, default='mock')
    args = parser.parse_args()

    # Generate default source registry
    registry = {
        "kcsc.re.kr": {"organization": "국가건설기준센터", "source_type": "technical_standard", "authority_level": "very_high"},
        "law.go.kr": {"organization": "국가법령정보센터", "source_type": "legal", "authority_level": "very_high"},
        "codil.or.kr": {"organization": "건설기술정보시스템", "source_type": "official_guideline", "authority_level": "high"}
    }
    with open('research/source_registry.json', 'w') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    agent = ResearchSerpAgent(provider_name=args.provider)
    agent.run(input_file=args.input)
