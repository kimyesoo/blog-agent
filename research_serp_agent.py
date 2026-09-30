
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

        # Tier A: Law / Tech Standards (Highest Trust)
        if "법령" in query or "규정" in query or "법률" in query or "산업안전" in query or "계약" in query or "기준" in query or "KCS" in query or "KDS" in query:
            if "원리" not in query and "시험" not in query:
                if "법" in query or "규정" in query:
                    results.append({
                        "title": f"국가법령정보센터 - {query} 관련 법령",
                        "url": "https://www.law.go.kr/법령/test",
                        "domain": "law.go.kr",
                        "snippet": f"{query}에 관한 공식 법령 조항.",
                        "is_pdf": False,
                        "effective_date": "2023-01-01",
                        "status": "active"
                    })
                else:
                    results.append({
                        "title": f"국가건설기준센터 - {query} 공식 기준",
                        "url": "https://www.kcsc.re.kr/some_standard.pdf",
                        "domain": "kcsc.re.kr",
                        "snippet": f"{query}에 대한 공식 건설기준(KCS/KDS).",
                        "is_pdf": True
                    })

        # Tier B: Public Technical Guidelines (LH, K-water, etc)
        if "지침" in query or "매뉴얼" in query or "대책" in query:
            results.append({
                "title": f"공공기관 - {query} 현장 실무 지침서",
                "url": "https://www.codil.or.kr/report_123.pdf",
                "domain": "codil.or.kr",
                "snippet": f"현장 시공 중 발생하는 {query} 현황 및 공식 지침.",
                "is_pdf": True
            })

        # Tier C: Industry Pro (Technical blogs, seminars)
        if "문제점" in query or "시공" in query or "장비" in query or "사례" in query or "계산" in query or "시험" in query or "해결책" in query or "노하우" in query:
            results.append({
                "title": f"[토목기술사] {query} 현장 적용 노하우 및 해결책",
                "url": f"https://civileng7.tistory.com/post_pro",
                "domain": "civileng7.tistory.com",
                "snippet": f"현장에서 직접 겪은 {query} 사례 및 실무 팁, 해결책.",
                "is_pdf": False
            })

        # Tier D: General Community (Generic blogs)
        if not results:
            results.append({
                "title": f"[일반 블로그] {query} 완벽 정리",
                "url": f"https://blog.naver.com/generic",
                "domain": "blog.naver.com",
                "snippet": f"일반적인 {query} 개념 정리글.",
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

        self.tier_a_domains = ["law.go.kr", "kcsc.re.kr", "moleg.go.kr"]
        self.tier_b_domains = ["go.kr", "or.kr", "re.kr", "lh.or.kr"]
        self.tier_c_domains = ["civileng7.tistory.com", "ac.kr"]
        # Everything else is Tier D

    def classify(self, domain, is_pdf):
        # Determine exact source type based on registry
        source_type = "unknown"
        if domain in self.registry:
            source_type = self.registry[domain].get("source_type", "unknown")

        if source_type == "unknown":
            if any(domain.endswith(s) for s in self.tier_b_domains):
                source_type = "official_guideline"
            elif domain in self.tier_c_domains or domain.endswith("ac.kr"):
                source_type = "industry_pro"
            else:
                source_type = "general_community"

        if is_pdf and source_type == "general_community":
            source_type = "industry_pro" # PDFs likely have higher weight than generic blog

        # Determine Tier
        if domain in self.tier_a_domains or source_type in ["legal", "technical_standard"]:
            tier = "Tier A"
        elif any(domain.endswith(s) for s in self.tier_b_domains) or source_type == "official_guideline":
            tier = "Tier B"
        elif domain in self.tier_c_domains or source_type == "industry_pro":
            tier = "Tier C"
        else:
            tier = "Tier D"

        return source_type, tier, self.registry.get(domain, {}).get("organization", "unknown")

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
    def __init__(self, profile_name="practical_blog", weights_file="research/weights.json"):
        self.profile_name = profile_name
        self.weights = {}
        if os.path.exists(weights_file):
            with open(weights_file, 'r') as f:
                all_weights = json.load(f)
                self.weights = all_weights.get(profile_name, all_weights.get("practical_blog", {}))

    def classify(self, topic_data):
        main_cat = topic_data.get("topic_cluster", "")
        intent = topic_data.get("search_intent", "")

        archetype = "field_problem_solving" # default

        if main_cat in ["건설안전", "건설공무", "건설기준 및 법규"] or intent in ["기준/규정"]:
            if intent not in ["시공 방법", "장비/자재", "문제 해결"]:
                archetype = "regulatory"
        elif intent in ["시공 방법", "비교", "장비/자재", "품질관리", "문제 해결", "원인과 대책"]:
            archetype = "construction_methods"
        elif main_cat in ["구조물", "교량", "도로", "터널"] and intent in ["설계", "검토"]:
            archetype = "technical_standard"

        weight = self.weights.get(archetype, {})
        return archetype, weight


# --- AGENT ---
class ResearchSerpAgent:
    def __init__(self, provider_name="mock", profile="practical_blog"):
        self.cache_dir = "research/cache"
        os.makedirs(self.cache_dir, exist_ok=True)

        self.classifier = SourceClassifier()
        self.intent_classifier = QueryIntentClassifier()
        self.archetype_classifier = ArchetypeClassifier(profile_name=profile)
        self.provider_name = provider_name
        self.profile = profile

        if provider_name == "mock":
            self.provider = MockSearchProvider()
        else:
            self.provider = MockSearchProvider()

    def generate_queries(self, topic_data, archetype):
        core = topic_data.get("technical_core", "")
        intent = topic_data.get("search_intent", "")

        queries = []

        # Primary queries aligned with "Practical Value First"
        if intent == "시공 방법":
            queries.extend([f"{core} 시공 노하우", f"{core} 시공순서 및 문제점"])
        elif intent == "계산/산정":
            queries.extend([f"{core} 산정 시 주의사항", f"{core} 수량산출 예시"])
        elif intent in ["문제 해결", "원인과 대책"]:
            queries.extend([f"{core} 시공 문제점", f"{core} 하자 원인 및 대책"])
        else:
            queries.append(f"{core} {intent}")

        # Contextual expansions based on archetype weights
        if archetype == "regulatory":
            queries.extend([f"{core} 관련 법령", f"산업안전보건법 {core} 적용"])
        elif archetype == "technical_standard":
            queries.extend([f"KDS {core}", f"{core} 설계기준", f"{core} 시공 사례"])
        elif archetype in ["field_problem_solving", "construction_methods"]:
            queries.extend([f"{core} 현장 해결책", f"{core} 실무 사례", f"{core} 팁"])

        return list(set(queries))[:4]

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

            # Determine Archetype and Dynamic Weights
            archetype, weights = self.archetype_classifier.classify(t)

            queries = self.generate_queries(t, archetype)

            topic_serp = []
            source_dist = {"legal": 0, "technical_standard": 0, "official_guideline": 0, "industry_pro": 0, "general_community": 0}
            tier_dist = {"Tier A": 0, "Tier B": 0, "Tier C": 0, "Tier D": 0}
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
                    stype, tier, org = self.classifier.classify(domain, r.get("is_pdf", False))
                    r["source_type"] = stype
                    r["authority_tier"] = tier

                    domains_seen.add(domain)
                    if stype in source_dist:
                        source_dist[stype] += 1

                    if tier in tier_dist:
                        tier_dist[tier] += 1

                    evidence_item = {
                        "title": r["title"],
                        "source_type": stype,
                        "authority_tier": tier,
                        "url": r["url"]
                    }
                    if stype == "legal":
                        evidence_item["effective_date"] = r.get("effective_date", "unknown")
                        evidence_item["status"] = r.get("status", "unknown")

                    if tier == "Tier A" and stype == "legal" and evidence_item not in legal_basis:
                        legal_basis.append(evidence_item)
                    elif tier == "Tier A" and stype == "technical_standard" and evidence_item not in technical_standards:
                        technical_standards.append(evidence_item)
                    elif tier == "Tier B" and evidence_item not in official_guidelines:
                        official_guidelines.append(evidence_item)
                    elif tier in ["Tier C", "Tier D"] and evidence_item not in field_practices and len(field_practices) < 5:
                        field_practices.append(evidence_item)

                    r["query_used"] = q
                    r["query_intent"] = mapped_intent

                    if mapped_intent in intent_dist:
                        intent_dist[mapped_intent] += 1
                    else:
                        intent_dist[mapped_intent] = 1

                    topic_serp.append(r)

            # Gap analysis
            overlap = "none"
            for ep in existing_posts:
                ep_title = ep.get("title", "")
                if topic_title == ep_title:
                    overlap = "high"
                    break
                elif t.get("technical_core", "") in ep_title:
                    overlap = "possible"

            content_gap = "high" if overlap == "none" else ("partial" if overlap == "possible" else "none")

            # Legal Relevance Calculation (Does it inherently require legal backing?)
            leg_rel = "none"
            if archetype == "regulatory":
                leg_rel = "direct" if tier_dist["Tier A"] > 0 else "indirect"
            elif archetype == "technical_standard":
                leg_rel = "indirect"

            # Research Readiness logic
            readiness = "low"
            if archetype in ["field_problem_solving", "construction_methods"]:
                # High readiness if we have Tier C (Industry Pros) backing it up, law is irrelevant.
                if tier_dist["Tier C"] > 0:
                    readiness = "high"
                elif tier_dist["Tier D"] > 0:
                    readiness = "medium"
            else:
                # For Technical or Regulatory, Tier A/B is necessary for high readiness
                if tier_dist["Tier A"] > 0:
                    readiness = "high"
                elif tier_dist["Tier B"] > 0 or tier_dist["Tier C"] > 0:
                    readiness = "medium"

            summary = {
                "topic": topic_title,
                "content_archetype": archetype,
                "active_profile": self.profile,
                "evidence_weight": weights,
                "query_count": len(queries),
                "result_count": len(topic_serp),
                "search_intent_distribution": intent_dist,
                "source_distribution": source_dist,
                "tier_distribution": tier_dist,
                "unique_domains": len(domains_seen),
                "existing_content_overlap": overlap,
                "content_gap": content_gap,
                "research_readiness": readiness,
                "legal_coverage_report": {
                    "legal_relevance": leg_rel,
                    "legal_research_status": "complete" if tier_dist["Tier A"] > 0 else "insufficient"
                },
                "evidence_hierarchy": {
                    "tier_a_standards_and_law": legal_basis + technical_standards,
                    "tier_b_public_guidance": official_guidelines,
                    "tier_c_industry_pro": [fp for fp in field_practices if fp.get("authority_tier") == "Tier C"],
                    "tier_d_community": [fp for fp in field_practices if fp.get("authority_tier") == "Tier D"]
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

        print(f"Research SERP processing complete for {len(topics)} topics using profile: {self.profile}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Research SERP Agent")
    parser.add_argument('--input', type=str, default='topic_research/v2_2_test_candidates.json')
    parser.add_argument('--provider', type=str, default='mock')
    parser.add_argument('--profile', type=str, default='practical_blog')
    args = parser.parse_args()

    agent = ResearchSerpAgent(provider_name=args.provider, profile=args.profile)
    agent.run(input_file=args.input)
