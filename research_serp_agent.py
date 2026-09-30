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
        # Generates realistic-looking mock data based on the query for testing
        results = []
        if "기준" in query or "KCS" in query or "KDS" in query:
            results.append({
                "title": f"국가건설기준센터 - {query} 관련 기준",
                "url": "https://www.kcsc.re.kr/some_standard.pdf",
                "domain": "kcsc.re.kr",
                "snippet": f"{query}에 대한 공식 국가건설기준(KCS) 설명입니다.",
                "is_pdf": True
            })

        if "문제점" in query or "대책" in query:
            results.append({
                "title": f"{query} 현장 실무 보고서",
                "url": "https://www.codil.or.kr/report_123.pdf",
                "domain": "codil.or.kr",
                "snippet": f"현장 시공 중 발생하는 {query} 현황 및 건설기술연구원 분석.",
                "is_pdf": True
            })

        # Add generic blog results
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
    def __init__(self, registry_file='research/source_registry.json'):
        self.registry = {}
        if os.path.exists(registry_file):
            with open(registry_file, 'r') as f:
                self.registry = json.load(f)

        # Default fallback rules
        self.official_domains = ["go.kr", "or.kr", "re.kr"]
        self.academic_domains = ["ac.kr"]

    def classify(self, domain, is_pdf):
        # Exact match
        if domain in self.registry:
            reg = self.registry[domain]
            return reg.get("source_type", "unknown"), reg.get("authority_level", "unknown"), reg.get("organization", "unknown")

        # Heuristics
        for suffix in self.official_domains:
            if domain.endswith(suffix):
                return "official", "high", "Public Institution"

        for suffix in self.academic_domains:
            if domain.endswith(suffix):
                return "academic", "medium", "University/Research"

        if domain.endswith("tistory.com") or domain.endswith("naver.com"):
            return "blog", "low", "Personal Blog"

        if is_pdf:
            return "industry", "medium", "Industry Document"

        return "unknown", "unknown", "unknown"

# --- AGENT ---
class ResearchSerpAgent:
    def __init__(self, provider_name="mock"):
        self.cache_dir = "research/cache"
        os.makedirs(self.cache_dir, exist_ok=True)

        self.classifier = SourceClassifier()
        self.provider_name = provider_name

        if provider_name == "mock":
            self.provider = MockSearchProvider()
        else:
            # Fallback to mock if API not implemented
            self.provider = MockSearchProvider()

    def generate_queries(self, topic_data):
        core = topic_data.get("technical_core", "")
        intent = topic_data.get("search_intent", "")

        queries = [topic_data["topic"]] # The full title

        if intent == "시공 방법":
            queries.extend([f"{core} 시공", f"{core} 시공순서", f"{core} 작업방법"])
        elif intent == "계산/산정":
            queries.extend([f"{core} 계산", f"{core} 산정기준", f"{core} 수량산출"])
        elif intent in ["문제 해결", "원인과 대책"]:
            queries.extend([f"{core} 문제점", f"{core} 대책", f"{core} 하자 원인"])
        elif intent == "기준/규정":
            queries.extend([f"{core} 기준", f"{core} KCS", f"{core} KDS", f"{core} 시방서"])
        elif intent == "시험/측정":
            queries.extend([f"{core} 시험방법", f"{core} 결과 해석"])
        else:
            queries.extend([f"{core} {intent}", f"{core} 실무"])

        return list(set(queries))[:3] # Limit to 3 distinct queries per topic

    def search_with_cache(self, query):
        cache_key = hashlib.md5(query.encode('utf-8')).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)

        # Retry/Backoff logic would go here if using real API
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

        # We also want to map existing posts to check gap
        existing_posts = []
        if os.path.exists("content_db/posts.json"):
            with open("content_db/posts.json", "r") as f:
                existing_posts = json.load(f)

        for t in topics:
            topic_title = t["topic"]
            queries = self.generate_queries(t)

            topic_serp = []
            source_dist = {"official": 0, "academic": 0, "industry": 0, "blog": 0, "unknown": 0}
            domains_seen = set()

            official_evidence = []
            industry_evidence = []

            for q in queries:
                res = self.search_with_cache(q)

                # Classify results
                for r in res:
                    domain = r["domain"]
                    stype, auth, org = self.classifier.classify(domain, r.get("is_pdf", False))
                    r["source_type"] = stype
                    r["authority_level"] = auth

                    domains_seen.add(domain)
                    if stype in source_dist:
                        source_dist[stype] += 1

                    if stype == "official" and len(official_evidence) < 2:
                        official_evidence.append(r["title"])
                    elif stype == "industry" and len(industry_evidence) < 2:
                        industry_evidence.append(r["title"])

                    r["query_used"] = q
                    topic_serp.append(r)

            # Existing Content Gap
            overlap = "none"
            for ep in existing_posts:
                ep_title = ep.get("title", "")
                if topic_title == ep_title:
                    overlap = "high"
                    break
                elif t.get("technical_core", "") in ep_title:
                    overlap = "possible"

            content_gap = "high" if overlap == "none" else ("partial" if overlap == "possible" else "none")

            # Research Readiness
            readiness = "low"
            if source_dist["official"] > 0 and source_dist["blog"] > 0:
                readiness = "high"
            elif source_dist["official"] > 0 or source_dist["industry"] > 0:
                readiness = "medium"

            summary = {
                "topic": topic_title,
                "query_count": len(queries),
                "result_count": len(topic_serp),
                "source_distribution": source_dist,
                "official_source_count": source_dist["official"],
                "industry_source_count": source_dist["industry"],
                "academic_source_count": source_dist["academic"],
                "unique_domains": len(domains_seen),
                "official_evidence": official_evidence,
                "industry_evidence": industry_evidence,
                "existing_content_overlap": overlap,
                "content_gap": content_gap,
                "research_readiness": readiness
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

        print(f"Research SERP processing complete for {len(topics)} topics.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Research SERP Agent")
    parser.add_argument('--input', type=str, default='topic_research/v2_2_test_candidates.json')
    parser.add_argument('--provider', type=str, default='mock')
    args = parser.parse_args()

    # Generate default source registry
    registry = {
        "kcsc.re.kr": {"organization": "국가건설기준센터", "source_type": "official", "authority_level": "very_high"},
        "law.go.kr": {"organization": "국가법령정보센터", "source_type": "official", "authority_level": "very_high"},
        "codil.or.kr": {"organization": "건설기술정보시스템", "source_type": "official", "authority_level": "high"}
    }
    with open('research/source_registry.json', 'w') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    agent = ResearchSerpAgent(provider_name=args.provider)
    agent.run(input_file=args.input)
