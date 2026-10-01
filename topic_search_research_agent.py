import json
import os
import sys
import argparse
import time
import hashlib
from urllib.parse import urlparse
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from tavily import TavilyClient, MissingAPIKeyError
except ImportError:
    TavilyClient = None
    MissingAPIKeyError = Exception

def load_json(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_query_variants(topic):
    """Generates simple natural query variants based on the topic."""
    variants = [topic]
    if "시험방법" in topic:
        variants.append(topic.replace("시험방법", "시험"))
        variants.append(topic.replace("시험방법", "시험 방법"))
    elif "방법" in topic:
        variants.append(topic.replace(" 방법", ""))
    return list(dict.fromkeys(variants))[:4] # Return unique max 4

class SearchProvider:
    def __init__(self):
        self.provider_status = {
            "provider": "unknown",
            "api_key_detected": False,
            "client_initialized": False,
            "search_test_success": False,
            "last_error": ""
        }
    def search(self, query: str, max_results: int = 10) -> dict:
        raise NotImplementedError

class TavilySearchProvider(SearchProvider):
    def __init__(self):
        super().__init__()
        self.provider_status["provider"] = "tavily"
        self.api_key = os.environ.get("TAVILY_API_KEY")

        if self.api_key:
            self.provider_status["api_key_detected"] = True
            if self.api_key == "dummy":
                self.provider_status["last_error"] = "dummy API key used"
        else:
            self.provider_status["last_error"] = "missing_api_key"
            raise ValueError("missing_api_key")

        if not TavilyClient:
            self.provider_status["last_error"] = "tavily_sdk_not_installed"
            raise ValueError("tavily_sdk_not_installed")

        try:
            self.client = TavilyClient(api_key=self.api_key)
            self.provider_status["client_initialized"] = True
        except Exception as e:
            self.provider_status["client_initialized"] = False
            self.provider_status["last_error"] = f"initialization_failed: {str(e)}"
            raise ValueError(f"initialization_failed: {str(e)}")

    def search(self, query: str, max_results: int = 10) -> dict:
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                # Basic search query
                response = self.client.search(query=query, max_results=max_results, search_depth="basic")
                results = []

                for idx, res in enumerate(response.get("results", [])):
                    url = res.get("url", "")
                    domain = urlparse(url).netloc if url else ""

                    results.append({
                        "rank": idx + 1,
                        "title": res.get("title", ""),
                        "url": url,
                        "domain": domain,
                        "snippet": res.get("content", ""),
                        "provider_score": res.get("score", 0.0)
                    })

                self.provider_status["search_test_success"] = True
                self.provider_status["last_error"] = ""
                return {
                    "status": "success",
                    "provider": "tavily",
                    "results": results
                }

            except MissingAPIKeyError as e:
                self.provider_status["last_error"] = str(e)
                return {"status": "search_failed", "error": "authentication_error", "exception": "MissingAPIKeyError", "message": str(e)}
            except Exception as e:
                err_msg = str(e)
                self.provider_status["last_error"] = err_msg

                if "unauthorized" in err_msg.lower() or "invalid api key" in err_msg.lower() or "not authorized" in err_msg.lower() or "401" in err_msg:
                    return {"status": "search_failed", "error": "authentication_error", "exception": type(e).__name__, "message": err_msg}

                if attempt < max_retries:
                    time.sleep(2) # Brief pause before retry
                    continue
                else:
                    return {"status": "search_failed", "error": "provider_error", "exception": type(e).__name__, "message": err_msg}

class DummySearchProvider(SearchProvider):
    """Fallback provider when no real provider is available."""
    def __init__(self, last_error=""):
        super().__init__()
        self.provider_status["last_error"] = last_error

    def search(self, query: str, max_results: int = 10) -> dict:
        return {
            "status": "search_failed",
            "error": "search_provider_unavailable",
            "exception": "DummyProviderError",
            "message": "No active search provider",
            "results": []
        }

def get_provider(provider_name: str) -> SearchProvider:
    if provider_name.lower() == "tavily":
        try:
            return TavilySearchProvider()
        except ValueError as e:
            print(f"Warning: Failed to initialize Tavily provider ({str(e)}). Falling back to safe dummy mode.")
            return DummySearchProvider(last_error=str(e))
    else:
        print(f"Warning: Provider '{provider_name}' not supported. Falling back to safe dummy mode.")
        return DummySearchProvider(last_error=f"Unsupported provider: {provider_name}")

import collections

def analyze_intent(text):
    if not text:
        return "기타"
    text = text.replace(" ", "")
    if "시험방법" in text or "측정방법" in text or "방법론" in text:
        return "시험방법 확인"
    elif "계산" in text or "공식" in text or "구하는" in text:
        return "계산방법 확인"
    elif "해석" in text or "결과" in text or "판독" in text:
        return "결과해석"
    elif "현장" in text or "실무" in text or "적용" in text:
        return "현장적용"
    elif "기준" in text or "규정" in text or "지침" in text or "시방서" in text:
        return "기준/규정 확인"
    elif "부적합" in text or "원인" in text or "대책" in text or "문제" in text:
        return "문제해결"
    elif "비교" in text or "차이" in text or "vs" in text.lower():
        return "비교/차이점"
    elif "사례" in text:
        return "사례/실무"
    elif "자료" in text or "문서" in text or "다운" in text:
        return "자료/문서 찾기"
    elif "이란" in text or "정의" in text or "개념" in text or "원리" in text:
        return "개념/정의 확인"
    return "기타"

def analyze_content_type(domain, title, snippet):
    domain = domain.lower()
    text = (title + " " + snippet).lower()

    if ".go.kr" in domain or ".or.kr" in domain:
        return "government"
    if "kci.go.kr" in domain or "riss.kr" in domain or "dbpia" in domain or "논문" in text:
        return "academic"
    if "blog.naver.com" in domain or "blog.daum.net" in domain:
        return "blog"
    if "tistory.com" in domain:
        return "tistory"
    if "cafe.naver.com" in domain or "cafe.daum.net" in domain or "dcinside" in domain:
        return "community"
    if "youtube.com" in domain or "youtu.be" in domain or "동영상" in text:
        return "video"
    if "pdf" in text or "다운로드" in text or ".pdf" in urlparse(domain).path:
        return "document"
    if ".co.kr" in domain or ".com" in domain:
        return "commercial"
    return "unknown"

def analyze_title_pattern(title):
    t = title.replace(" ", "")
    if "시험방법" in t or "방법" in t:
        return "시험방법"
    if "계산" in t or "예제" in t:
        return "계산방법"
    if "결과" in t or "해석" in t:
        return "결과해석"
    if "원인" in t or "대책" in t or "부적합" in t:
        return "문제해결"
    if "현장" in t or "실무" in t:
        return "현장실무"
    if "기준" in t or "규정" in t:
        return "기준/규정 확인"
    return "정보탐색"

def process_topic(item, original_candidates_dict, existing_posts_dict, cache_dir, delay, refresh, provider, dry_run=False):
    topic = item["topic"]

    # Check cache
    safe_hash = hashlib.md5(topic.encode('utf-8')).hexdigest()
    cache_path = os.path.join(cache_dir, f"{safe_hash}.json")
    if not refresh and os.path.exists(cache_path):
        res = load_json(cache_path)
        # Verify it wasn't a failed search before returning. Failed searches shouldn't be permanently cached.
        if res.get("research_status") != "failed":
            res["_cache_hit"] = True
            return res

    variants = generate_query_variants(topic)

    if dry_run:
        print(f"[DRY-RUN] Will search queries: {variants}")
        return None

    queries_data = []
    serp_presence = False
    unique_domains = set()
    total_organic = 0
    top_content = []
    domain_counts = collections.defaultdict(int)
    content_type_counts = collections.defaultdict(int)
    observed_related_queries = set()

    # Text corpus to extract intent and topics
    combined_titles = ""
    combined_snippets = ""
    serp_topics_freq = collections.defaultdict(int)

    for i, q in enumerate(variants):
        if i > 0:
            time.sleep(delay) # rate limiting

        res = provider.search(q, max_results=10)
        q_type = "primary" if i == 0 else "variant"

        q_data = {
            "query": q,
            "query_type": q_type,
            "status": res["status"],
            "results": res.get("results", [])
        }

        if res.get("provider"):
            q_data["provider"] = res["provider"]

        if res["status"] != "success":
            q_data["error"] = {
                "code": res.get("error", "unknown"),
                "exception": res.get("exception", ""),
                "message": res.get("message", "")
            }

        # Add basic ISO timestamp for when this was searched
        from datetime import datetime, timezone
        q_data["searched_at"] = datetime.now(timezone.utc).isoformat()

        queries_data.append(q_data)

        if res["status"] == "success" and len(res.get("results", [])) > 0:
            serp_presence = True
            total_organic += len(res["results"])

            for idx, r in enumerate(res["results"]):
                domain = r.get("domain", "")
                title = r.get("title", "")
                snippet = r.get("snippet", "")

                combined_titles += f" {title}"
                combined_snippets += f" {snippet}"

                if domain:
                    unique_domains.add(domain)
                    domain_counts[domain] += 1

                # Heuristically guess observed_topics based on snippet for SERP analysis
                s_lower = snippet.lower()
                obs_topics = []
                if "목적" in s_lower: obs_topics.append("시험 목적")
                if "원리" in s_lower: obs_topics.append("시험 원리")
                if "기구" in s_lower or "장비" in s_lower: obs_topics.append("시험 장비")
                if "방법" in s_lower or "순서" in s_lower: obs_topics.append("시험 방법")
                if "계산" in s_lower or "공식" in s_lower: obs_topics.append("계산 방법")
                if "결과" in s_lower: obs_topics.append("결과 해석")

                for ot in obs_topics:
                    serp_topics_freq[ot] += 1

                # Populate top_content from the top 5 results of the primary query
                if i == 0 and idx < 5:
                    ct = analyze_content_type(domain, title, snippet)
                    content_type_counts[ct] += 1
                    tp = analyze_title_pattern(title)

                    top_content.append({
                        "rank": r.get("rank", idx + 1),
                        "title": title,
                        "url": r.get("url", ""),
                        "domain": domain,
                        "content_type": ct,
                        "title_pattern": tp,
                        "observed_topics": obs_topics
                    })

            # Basic related query extraction from titles
            for r in res["results"]:
                t = r.get("title", "")
                if t and "시험" in t and len(t) < 30 and t != topic:
                    # Very simple heuristic to grab related looking titles as queries
                    cleaned = t.split("|")[0].split("-")[0].strip()
                    if cleaned and len(cleaned) > 5:
                        observed_related_queries.add(cleaned)

    # As per prompt constraints, we must map existing post data if available
    core = item["validation"].get("similarity_group", "").split("_")[0]
    existing_post_data = None
    for k, v in existing_posts_dict.items():
        # Heuristic matching for the existing post
        if core in k or k in core:
            existing_post_data = {
                "title": k,
                "views": v
            }
            break

    # Fetch related keywords from the original candidates if it exists
    gen_related_kws = original_candidates_dict.get(topic, [])

    # Observe intent based on gathered text
    obs_intent = None
    if serp_presence:
        obs_intent = analyze_intent(combined_titles + " " + combined_snippets)

    val_intent = item.get("search_intent", "")

    intent_analysis = None
    if serp_presence:
        match_val = (val_intent == obs_intent) if obs_intent != "기타" else None
        reason_txt = f"상위 검색 결과에서 '{obs_intent}' 패턴이 다수 관찰됨" if obs_intent != "기타" else "관찰된 검색 의도가 불분명함"
        intent_analysis = {
            "validation_intent": val_intent,
            "observed_intent": obs_intent,
            "match": match_val,
            "confidence": "medium", # Heuristic approach
            "reason": reason_txt
        }

    content_gap = []
    if serp_presence:
        # Heuristic gap analysis without LLM
        if "계산" not in combined_titles and "예제" not in combined_snippets:
            content_gap.append({
                "gap": "실제 계산 예제",
                "evidence": "상위 결과의 snippet에서 계산 예제가 확인되지 않음",
                "confidence": "medium"
            })
        if "현장" not in combined_titles and "실무" not in combined_titles:
            content_gap.append({
                "gap": "현장 적용 및 실무 팁",
                "evidence": "검색 결과 제목에서 현장 실무 관련 내용이 확인되지 않음",
                "confidence": "medium"
            })

    serp_content_structure = {}
    if serp_presence and serp_topics_freq:
        common_topics = [k for k, v in sorted(serp_topics_freq.items(), key=lambda x: x[1], reverse=True) if v > 1]
        serp_content_structure = {
            "common_topics": common_topics,
            "topic_frequency": dict(serp_topics_freq)
        }

    # Compile top domains properly
    top_domains = []
    for d, c in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        top_domains.append({"domain": d, "count": c})

    # Construct final object
    result = {
        "topic": topic,
        "topic_cluster": item.get("topic_cluster", ""),
        "validation_decision": item["validation"]["decision"],
        "validation_search_intent": val_intent,
        "observed_search_intent": obs_intent,
        "intent_analysis": intent_analysis,

        "queries": queries_data,

        "serp": {
            "serp_presence": serp_presence,
            "organic_result_count": total_organic,
            "unique_domains": len(unique_domains),
            "top_domains": top_domains,
            "content_type_distribution": dict(content_type_counts)
        },

        "serp_content_structure": serp_content_structure,

        "generated_related_keywords": gen_related_kws,
        "observed_related_queries": list(observed_related_queries)[:5],

        "top_content": top_content,
        "content_gap": content_gap,

        "search_volume": None,
        "search_volume_source": None,
        "competition": None,
        "competition_source": None,

        "existing_post": existing_post_data,

        "research_status": "failed" if not serp_presence else "complete",
        "errors": []
    }

    # Collect errors into an array of objects
    for qd in queries_data:
        if qd.get("error") and qd["error"] not in result["errors"]:
            result["errors"].append(qd["error"])

    # Only cache successful queries to avoid persistent failure caching
    if result["research_status"] != "failed":
        save_json(result, cache_path)

    return result

def generate_report(results, summary, output_md):
    lines = [
        "# Topic Search Research Report\n",
        f"Search Provider: {summary.get('provider', 'Unknown')}\n",
        "## 1. Summary\n",
        f"- 조사 후보: {summary['input_count']}",
        f"- 성공: {summary['success_count']}",
        f"- 실패: {summary['failed_count']}",
        f"- Cache hit: {summary.get('cache_hit_count', 0)}\n",
        "## 1.1 Provider Status\n",
        f"- API Key Detected: {summary.get('provider_status', {}).get('api_key_detected', False)}",
        f"- Client Initialized: {summary.get('provider_status', {}).get('client_initialized', False)}",
        f"- Search Test Success: {summary.get('provider_status', {}).get('search_test_success', False)}",
        f"- Last Error: {summary.get('provider_status', {}).get('last_error', '')}\n",
    ]

    lines.append("## 2. 세부 결과\n")
    for r in results:
        lines.append(f"### 주제: {r['topic']}")
        lines.append(f"- **Validation Intent**: {r.get('validation_search_intent')}")
        lines.append(f"- **Observed Intent**: {r.get('observed_search_intent')}")

        ia = r.get("intent_analysis")
        if ia:
            lines.append(f"- **Intent Match**: {'YES' if ia.get('match') else 'NO'}")
        else:
            lines.append(f"- **Intent Match**: N/A")

        s = r.get("serp", {})
        lines.append(f"\n#### SERP")
        lines.append(f"- 검색 결과: {s.get('organic_result_count', 0)}")
        lines.append(f"- 고유 도메인: {s.get('unique_domains', 0)}")

        lines.append(f"\n#### Top Content")
        topc = r.get("top_content", [])
        for tc in topc:
            lines.append(f"{tc.get('rank')}. {tc.get('title')} (Type: {tc.get('content_type')}, Pattern: {tc.get('title_pattern')})")

        lines.append(f"\n#### Observed Related Queries")
        orq = r.get("observed_related_queries", [])
        for q in orq:
            lines.append(f"- {q}")

        lines.append(f"\n#### Content Gap")
        cg = r.get("content_gap", [])
        for gap in cg:
            lines.append(f"- {gap.get('gap')} ({gap.get('evidence')})")

        lines.append(f"\n#### 기존 검색 데이터 (생성됨)")
        gk = r.get("generated_related_keywords", [])
        for k in gk:
            lines.append(f"- {k}")

        lines.append("\n---\n")

    lines.append("## 3. Failed Research\n")
    lines.append("- 검색 실패 후보:\n")
    for r in results:
        if r["research_status"] == "failed":
            errs = [e.get("code", "unknown") for e in r["errors"]]
            lines.append(f"  - {r['topic']} (Reason: {', '.join(errs)})")

    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    parser = argparse.ArgumentParser(description="Topic Search Research Agent V1")
    parser.add_argument("--decision", type=str, default="KEEP", help="Validation decision to filter (KEEP, ALL, etc)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of topics to research")
    parser.add_argument("--topic", type=str, default=None, help="Specific topic to research")
    parser.add_argument("--refresh", action="store_true", help="Ignore cache and force refresh")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between searches in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print queries without executing search")
    parser.add_argument("--provider", type=str, default=os.environ.get("SEARCH_PROVIDER", "tavily"), help="Search provider to use")
    parser.add_argument("--disable-cache", action="store_true", help="Disable caching mechanism")
    parser.add_argument("--refresh-cache", action="store_true", help="Same as --refresh")
    parser.add_argument("--diagnose", action="store_true", help="Run provider diagnostics")
    parser.add_argument("--clear-cache", action="store_true", help="Delete all cache files")

    args = parser.parse_args()

    if args.refresh_cache or args.disable_cache:
        args.refresh = True

    out_dir = "topic_search"
    cache_dir = os.path.join(out_dir, "cache")

    if args.clear_cache:
        if os.path.exists(cache_dir):
            import glob
            files = glob.glob(os.path.join(cache_dir, "*.json"))
            for f in files:
                os.remove(f)
            print(f"Cleared {len(files)} cache files from {cache_dir}.")
        else:
            print("No cache directory found to clear.")
        sys.exit(0)

    if args.diagnose:
        print("Running Diagnostics...\n")
        provider = get_provider(args.provider)
        print(f"Provider: {provider.provider_status.get('provider', 'unknown')}")
        print(f"API Key Detected: {provider.provider_status.get('api_key_detected', False)}")
        print(f"Client Initialized: {provider.provider_status.get('client_initialized', False)}")

        # Test search
        if provider.provider_status.get('client_initialized', False):
            print("Testing search execution...")
            res = provider.search("테스트", max_results=1)
            print(f"Search Test Success: {provider.provider_status.get('search_test_success', False)}")
            if not provider.provider_status.get('search_test_success', False):
                print(f"Last Error: {provider.provider_status.get('last_error', '')}")
        else:
            print(f"Search Test Success: False")
            print(f"Last Error: {provider.provider_status.get('last_error', '')}")

        sys.exit(0)

    print("Blog Agent - Topic Search Research Agent V1\n")

    os.makedirs(cache_dir, exist_ok=True)

    validated_path = "topic_research/validated_topics.json"
    posts_path = "content_db/posts.json"
    original_candidates_path = "topic_research/topic_candidates.json"

    validated_topics = load_json(validated_path)
    posts_db = load_json(posts_path)
    original_candidates = load_json(original_candidates_path)

    if not validated_topics:
        return

    existing_posts_dict = {}
    if posts_db:
        for p in posts_db:
            if "title" in p:
                existing_posts_dict[p["title"]] = p.get("views", 0)

    original_candidates_dict = {}
    if original_candidates:
        for c in original_candidates:
            if "topic" in c and "related_keywords" in c:
                original_candidates_dict[c["topic"]] = c["related_keywords"]

    # Filter candidates
    targets = []
    for t in validated_topics:
        if args.topic and t["topic"] != args.topic:
            continue
        if args.decision != "ALL" and t["validation"]["decision"].upper() != args.decision.upper():
            continue
        targets.append(t)

    if args.limit:
        targets = targets[:args.limit]

    print(f"Target topics to research: {len(targets)}")

    out_dir = "topic_search"
    cache_dir = os.path.join(out_dir, "cache")

    provider = get_provider(args.provider)

    results = []
    success_c = 0
    failed_c = 0
    cache_hit_c = 0
    serp_c = 0
    vol_c = 0
    intent_match = 0
    intent_mismatch = 0

    print("Researching...")
    for i, item in enumerate(targets):
        if i > 0:
            time.sleep(args.delay) # Delay between overall topics

        res = process_topic(item, original_candidates_dict, existing_posts_dict, cache_dir, args.delay, args.refresh, provider, args.dry_run)
        if res is None:
            continue

        if res.pop("_cache_hit", False):
            cache_hit_c += 1
            print(f"[{item['topic']}] CACHE HIT (Status: {res['research_status']})")

        results.append(res)

        if res["research_status"] == "success" or res["research_status"] == "complete":
            success_c += 1
        else:
            failed_c += 1

        if res["serp"]["serp_presence"]:
            serp_c += 1

        if res["search_volume"] is not None:
            vol_c += 1

        # Intent matching logic (only applies if observed intent exists)
        vi = res.get("validation_search_intent")
        oi = res.get("observed_search_intent")
        if oi:
            if vi == oi:
                intent_match += 1
            else:
                intent_mismatch += 1

    # Save outputs
    res_path = os.path.join(out_dir, "search_results.json")
    sum_path = os.path.join(out_dir, "search_summary.json")
    rep_path = os.path.join(out_dir, "search_report.md")

    save_json(results, res_path)

    # Count cache hits by checking if it was just loaded vs processed
    # We can approximate this if the result doesn't have an execution log or just rely on file checks.
    # We will let cache_hit_count be 0 for simplicity if not tracked internally.

    intent_unk = len(results) - (intent_match + intent_mismatch)
    gap_count = sum([1 for r in results if r.get("content_gap")])
    rq_count = sum([1 for r in results if r.get("observed_related_queries")])
    tc_count = sum([1 for r in results if r.get("top_content")])

    summary = {
        "input_count": len(targets),
        "researched_count": len(results),
        "success_count": success_c,
        "failed_count": failed_c,
        "cache_hit_count": cache_hit_c,
        "provider": args.provider,
        "provider_status": provider.provider_status if hasattr(provider, "provider_status") else {},
        "search_volume_available_count": vol_c,
        "serp_found_count": serp_c,
        "intent_match_count": intent_match,
        "intent_mismatch_count": intent_mismatch,
        "intent_unknown_count": intent_unk,
        "content_gap_available_count": gap_count,
        "related_query_available_count": rq_count,
        "top_content_analysis_count": tc_count
    }

    save_json(summary, sum_path)
    generate_report(results, summary, rep_path)

    print("\nResearch complete.\n")
    print(f"Input: {len(targets)}")
    print(f"Success: {success_c}")
    print(f"Failed: {failed_c}\n")
    print("Output:")
    print(res_path)
    print(sum_path)
    print(rep_path)

if __name__ == "__main__":
    main()
