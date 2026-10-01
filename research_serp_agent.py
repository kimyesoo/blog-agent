
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

        # Tier A: Law
        if "법령" in query or "규정" in query or "법률" in query or "산업안전" in query or "계약" in query:
            if "원리" not in query and "시험" not in query:
                results.append({
                    "title": f"국가법령정보센터 - {query} 관련 법령",
                    "url": "https://www.law.go.kr/법령/test",
                    "domain": "law.go.kr",
                    "snippet": f"{query}에 관한 공식 법령 조항.",
                    "is_pdf": False,
                    "effective_date": "2023-01-01",
                    "status": "active"
                })

        # Tier A: Technical Standard
        if "기준" in query or "KCS" in query or "KDS" in query or "설계" in query or "시공" in query:
            results.append({
                "title": f"국가건설기준센터 - {query} 공식 기준",
                "url": "https://www.kcsc.re.kr/some_standard.pdf",
                "domain": "kcsc.re.kr",
                "snippet": f"{query}에 대한 국가건설기준(KCS/KDS).",
                "is_pdf": True
            })

        # Tier B: Public Technical Guidelines
        if "지침" in query or "매뉴얼" in query or "대책" in query:
            results.append({
                "title": f"공공기관 - {query} 현장 실무 지침서",
                "url": "https://www.codil.or.kr/report_123.pdf",
                "domain": "codil.or.kr",
                "snippet": f"현장 시공 중 발생하는 {query} 현황 및 공식 지침.",
                "is_pdf": True
            })

        # Tier C: Industry Pro
        if "문제점" in query or "시공" in query or "장비" in query or "사례" in query or "계산" in query or "시험" in query or "해결책" in query or "노하우" in query:
            results.append({
                "title": f"[토목기술사] {query} 현장 적용 노하우 및 해결책",
                "url": f"https://civileng7.tistory.com/post_pro",
                "domain": "civileng7.tistory.com",
                "snippet": f"현장에서 직접 겪은 {query} 사례 및 실무 팁, 해결책.",
                "is_pdf": False
            })

        # Tier D: General Community
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
            with open(registry_file, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)

        if os.path.exists(legal_registry_file):
            with open(legal_registry_file, 'r', encoding='utf-8') as f:
                self.registry.update(json.load(f))

        self.tier_a_domains = ["law.go.kr", "kcsc.re.kr", "moleg.go.kr"]
        self.tier_b_domains = ["go.kr", "or.kr", "re.kr", "lh.or.kr"]
        self.tier_c_domains = ["civileng7.tistory.com", "ac.kr"]

    def classify(self, domain, is_pdf):
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
            source_type = "industry_pro"

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
            with open(weights_file, 'r', encoding='utf-8') as f:
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
        self.provider = MockSearchProvider()

    def generate_queries(self, topic_data, archetype):
        core = topic_data.get("technical_core", "")
        intent = topic_data.get("search_intent", "")

        queries = []

        # Profile heavily influences the queries we try
        if archetype == "regulatory":
            queries.extend([f"{core} 관련 법령", f"산업안전보건법 {core} 적용", f"{core} 규정", f"{core} 지침"])
        elif archetype == "technical_standard":
            queries.extend([f"KDS {core}", f"{core} 설계기준", f"{core} 설계 검토사항"])
        elif archetype == "construction_methods":
            queries.extend([f"{core} 시공순서", f"{core} 공법 비교", f"{core} 장비 선정", f"{core} 품질 문제"])
        elif archetype == "field_problem_solving":
            queries.extend([f"{core} 시공 현장 문제", f"{core} 실무 사례 해결", f"{core} 노하우", f"{core} 자주하는 실수"])

        if not queries:
            queries.append(f"{core} {intent}")

        return list(set(queries))[:4]

    def search_with_cache(self, query):
        cache_key = hashlib.md5(query.encode('utf-8')).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        try:
            results = self.provider.search(query)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            return results
        except Exception as e:
            print(f"Search failed for {query}: {e}")
            return []

    def evaluate_readiness_dynamically(self, tier_dist, weights):
        # We calculate readiness purely based on whether the data we found matches what the active profile weighs heaviest.
        score = 0

        # Normalize weights conceptually:
        # law maps to Tier A (Legal)
        # technical_standard maps to Tier A (KCS/KDS)
        # public_guidance maps to Tier B
        # field_practice maps to Tier C and D

        if tier_dist["Tier A"] > 0:
            score += weights.get("law", 0) + weights.get("technical_standard", 0)
        if tier_dist["Tier B"] > 0:
            score += weights.get("public_guidance", 0)
        if tier_dist["Tier C"] > 0 or tier_dist["Tier D"] > 0:
            score += weights.get("field_practice", 0) + weights.get("problem_solving", 0)

        if score >= 60:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"

    def rank_sources_dynamically(self, all_evidence, weights):
        # Dynamically ranks source priority based strictly on profile weights.
        # all_evidence is a list of all gathered source dicts.

        w_law = weights.get("law", 0)
        w_tech = weights.get("technical_standard", 0)
        w_pub = weights.get("public_guidance", 0)
        w_field = weights.get("field_practice", 0) + weights.get("problem_solving", 0)

        ranked = []
        for e in all_evidence:
            stype = e.get("source_type")
            score = 0
            if stype == "legal": score = w_law
            elif stype == "technical_standard": score = w_tech
            elif stype == "official_guideline": score = w_pub
            elif stype in ["industry_pro", "general_community"]: score = w_field

            # Slightly boost Tier C over Tier D within field practice
            if e.get("authority_tier") == "Tier C":
                score += 5

            e["weight_score"] = score
            ranked.append(e)

        ranked.sort(key=lambda x: x["weight_score"], reverse=True)

        # Strip internal score before outputting final array
        for r in ranked:
            del r["weight_score"]

        return ranked

    def run(self, input_file, output_summary='research/research_summary.json', output_results='research/search_results.json'):
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found.")
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            topics = json.load(f)

        all_results = []
        all_summaries = []

        for t in topics:
            topic_title = t["topic"]
            archetype, weights = self.archetype_classifier.classify(t)
            queries = self.generate_queries(t, archetype)

            topic_serp = []
            source_dist = {"legal": 0, "technical_standard": 0, "official_guideline": 0, "industry_pro": 0, "general_community": 0}
            tier_dist = {"Tier A": 0, "Tier B": 0, "Tier C": 0, "Tier D": 0}
            intent_dist = {}
            domains_seen = set()

            raw_evidence = []
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

                    if evidence_item not in raw_evidence:
                        raw_evidence.append(evidence_item)

                    r["query_used"] = q
                    r["query_intent"] = mapped_intent

                    if mapped_intent in intent_dist:
                        intent_dist[mapped_intent] += 1
                    else:
                        intent_dist[mapped_intent] = 1

                    topic_serp.append(r)

            readiness = self.evaluate_readiness_dynamically(tier_dist, weights)
            ranked_evidence = self.rank_sources_dynamically(raw_evidence, weights)

            # The top source type reveals what the profile prioritizes practically
            top_source_priority = ranked_evidence[0]["source_type"] if ranked_evidence else "unknown"

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
                "research_readiness": readiness,
                "top_source_priority": top_source_priority,
                "evidence_hierarchy": {
                    "ranked_sources": ranked_evidence[:5] # Top 5 prioritized
                }
            }

            all_summaries.append(summary)
            all_results.append({
                "topic": topic_title,
                "queries": queries,
                "serp_results": topic_serp
            })

        with open(output_summary, 'w', encoding='utf-8') as f:
            json.dump(all_summaries, f, ensure_ascii=False, indent=2)

        with open(output_results, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        print(f"Research SERP processing complete for {len(topics)} topics using profile: {self.profile}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Research SERP Agent")
    parser.add_argument('--input', type=str, default='topic_research/v2_2_test_candidates.json')
    parser.add_argument('--profile', type=str, default='practical_blog')
    parser.add_argument('--output', type=str, default='research/research_summary.json')
    args = parser.parse_args()

    # Generate default source registry if it doesn't exist
    if not os.path.exists('research/source_registry.json'):
        registry = {
            "kcsc.re.kr": {"organization": "국가건설기준센터", "source_type": "technical_standard", "authority_level": "very_high"},
            "law.go.kr": {"organization": "국가법령정보센터", "source_type": "legal", "authority_level": "very_high"},
            "codil.or.kr": {"organization": "건설기술정보시스템", "source_type": "official_guideline", "authority_level": "high"},
            "civileng7.tistory.com": {
                "organization": "개인(토목기술사)",
                "source_type": "industry_pro",
                "authority_level": "medium",
                "practical_value": "high",
                "recommended_archetypes": ["field_problem_solving", "construction_methods"]
            },
            "2030-view.tistory.com": {
                "organization": "개인(건설공무)",
                "source_type": "industry_pro",
                "authority_level": "medium",
                "practical_value": "high",
                "recommended_archetypes": ["regulatory", "field_problem_solving"]
            }
        }
        with open('research/source_registry.json', 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)

    agent = ResearchSerpAgent(profile=args.profile)
    agent.run(input_file=args.input, output_summary=args.output)
