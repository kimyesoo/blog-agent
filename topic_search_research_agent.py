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
        # Keeping it simple per standard library specs
        from datetime import datetime, timezone
        q_data["searched_at"] = datetime.now(timezone.utc).isoformat()

        queries_data.append(q_data)

        if res["status"] == "success" and len(res.get("results", [])) > 0:
            serp_presence = True
            total_organic += len(res["results"])
            for r in res["results"]:
                if r.get("domain"):
                    unique_domains.add(r["domain"])

            # Populate top_content from the primary query
            if i == 0:
                for idx, r in enumerate(res["results"]):
                    top_content.append({
                        "rank": r.get("rank", idx + 1),
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "domain": r.get("domain", ""),
                        "content_type_observed": None, # Cannot determine without page extraction yet
                        "likely_sections": []
                    })

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

    # Construct final object
    result = {
        "topic": topic,
        "topic_cluster": item.get("topic_cluster", ""),
        "validation_decision": item["validation"]["decision"],
        "validation_search_intent": item.get("search_intent", ""),
        "observed_search_intent": None,  # Null because search failed

        "queries": queries_data,

        "serp": {
            "serp_presence": serp_presence,
            "organic_result_count": total_organic,
            "unique_domains": len(unique_domains)
        },

        "generated_related_keywords": gen_related_kws,
        "observed_related_queries": [],

        "top_content": top_content,
        "content_gap": [],

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
        "## 2. Search Intent\n",
        "- Validation intent와 실제 관찰 intent가 일치/불일치한 후보 (데이터 없음: 검색 실패)\n",
        "## 3. SERP Findings\n",
        f"- 검색 결과가 확인된 후보: {summary['serp_found_count']} 건\n",
        "## 4. Content Gap\n",
        "- 검색 결과에서 확인된 콘텐츠 공백 (데이터 없음: 검색 실패)\n",
        "## 5. Search Volume\n",
        f"- 실제 검색량 데이터 제공 여부: {summary['search_volume_available_count']} 건 확인됨\n",
        "## 6. Failed Research\n",
        "- 검색 실패 후보:\n"
    ]

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
        "intent_mismatch_count": intent_mismatch
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
