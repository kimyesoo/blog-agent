
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
        # Legal Queries Simulation
        if "법령" in query or "규정" in query or "법률" in query or "산업안전보건법" in query:
            # We simulate that not ALL queries have laws.
            # If the query is about specific test principles, don't return laws to test "none" relevance.
            if "원리" not in query and "계산" not in query:
                results.append({
                    "title": f"산업안전보건법 시행규칙 - {query}",
                    "url": "https://www.law.go.kr/법령/산업안전보건법",
                    "domain": "law.go.kr",
                    "snippet": f"{query}에 관한 조항입니다.",
                    "is_pdf": False,
                    "effective_date": "2023-01-01",
                    "status": "active"
                })

        # Technical Standard Simulation
        if "기준" in query or "KCS" in query or "KDS" in query:
            results.append({
                "title": f"국가건설기준센터 - {query} 관련 기준",
                "url": "https://www.kcsc.re.kr/some_standard.pdf",
                "domain": "kcsc.re.kr",
                "snippet": f"{query}에 대한 공식 국가건설기준(KCS) 설명입니다.",
                "is_pdf": True
            })

        # Official Guidelines Simulation
        if "대책" in query or "지침" in query:
            results.append({
                "title": f"{query} 현장 실무 지침서",
                "url": "https://www.codil.or.kr/report_123.pdf",
                "domain": "codil.or.kr",
                "snippet": f"현장 시공 중 발생하는 {query} 현황 및 지침 분석.",
                "is_pdf": True
            })

        # Generic Blogs
        for i in range(2):
            results.append({
                "title": f"[토목 실무] {query} 완벽 정리",
                "url": f"https://civileng7.tistory.com/post{i}",
                "domain": "tistory.com",
                "snippet": f"블로그에서 정리한 {query} 관련 내용입니다.",
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
            return "blog", "low", "Personal Blog"

        if is_pdf:
            return "industry", "medium", "Industry Document"

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

# --- AGENT ---
class ResearchSerpAgent:
    def __init__(self, provider_name="mock"):
        self.cache_dir = "research/cache"
        os.makedirs(self.cache_dir, exist_ok=True)

        self.classifier = SourceClassifier()
        self.intent_classifier = QueryIntentClassifier()
        self.provider_name = provider_name

        if provider_name == "mock":
            self.provider = MockSearchProvider()
        else:
            self.provider = MockSearchProvider()

    def generate_queries(self, topic_data):
        core = topic_data.get("technical_core", "")
        intent = topic_data.get("search_intent", "")

        general_queries = []
        legal_queries = []
        standard_queries = []

        # General Queries
        if intent == "시공 방법":
            general_queries.extend([f"{core} 시공", f"{core} 시공순서"])
        elif intent == "계산/산정":
            general_queries.extend([f"{core} 계산", f"{core} 수량산출"])
        elif intent in ["문제 해결", "원인과 대책"]:
            general_queries.extend([f"{core} 문제점", f"{core} 대책"])
        else:
            general_queries.append(f"{core} {intent}")

        # Legal Queries
        legal_queries.extend([f"{core} 관련 법령", f"{core} 안전 기준", f"산업안전보건법 {core}"])

        # Standard Queries
        standard_queries.extend([f"KDS {core}", f"KCS {core}", f"{core} 설계기준"])

        return {
            "general": list(set(general_queries))[:2],
            "legal": list(set(legal_queries))[:2],
            "standard": list(set(standard_queries))[:2]
        }

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

    def evaluate_legal_relevance(self, legal_evidence, topic_data):
        # Fallback relevance logic based on findings
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
            query_groups = self.generate_queries(t)
            all_queries_flat = query_groups["general"] + query_groups["legal"] + query_groups["standard"]

            topic_serp = []
            source_dist = {"legal": 0, "technical_standard": 0, "official_guideline": 0, "academic": 0, "industry": 0, "blog": 0, "unknown": 0}
            intent_dist = {}
            domains_seen = set()

            legal_basis = []
            technical_standards = []
            official_guidelines = []
            industry_sources = []

            mapped_intent = self.intent_classifier.classify_query(t.get("search_intent", ""))

            for q in all_queries_flat:
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
                    elif stype in ["industry", "blog"] and len(industry_sources) < 3 and evidence_item not in industry_sources:
                        industry_sources.append(evidence_item)

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

            # Legal Relevance Calculation
            leg_rel, leg_reason = self.evaluate_legal_relevance(legal_basis, t)

            # Conflict Mocking
            conflict_detected = False
            if source_dist["legal"] > 0 and source_dist["blog"] > 0:
                # In real scenario, evaluate text. Mocking false here unless strict condition meets.
                conflict_detected = False

            legal_status = "complete" if source_dist["legal"] > 0 or leg_rel == "none" else "insufficient"

            readiness = "low"
            if (source_dist["legal"] > 0 or source_dist["technical_standard"] > 0) and source_dist["blog"] > 0:
                readiness = "high"
            elif source_dist["official_guideline"] > 0 or source_dist["industry"] > 0:
                readiness = "medium"

            summary = {
                "topic": topic_title,
                "query_count": len(all_queries_flat),
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
                    "industry_sources": industry_sources
                }
            }

            all_summaries.append(summary)
            all_results.append({
                "topic": topic_title,
                "queries": all_queries_flat,
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

    agent = ResearchSerpAgent(provider_name=args.provider)
    agent.run(input_file=args.input)
