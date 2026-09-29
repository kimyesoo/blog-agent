import json
import os
import sys
import argparse
import time
import hashlib

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

def simulate_search(query, delay):
    """
    Simulates a web search since we are prohibited from using external APIs in V1.
    Will gracefully fail and return structure as requested.
    """
    time.sleep(delay)
    # Returning a failure response because no actual search provider is configured.
    return {
        "status": "search_failed",
        "error": "search_provider_unavailable",
        "results": []
    }

def process_topic(item, original_candidates_dict, existing_posts_dict, cache_dir, delay, refresh):
    topic = item["topic"]

    # Check cache
    safe_hash = hashlib.md5(topic.encode('utf-8')).hexdigest()
    cache_path = os.path.join(cache_dir, f"{safe_hash}.json")
    if not refresh and os.path.exists(cache_path):
        return load_json(cache_path)

    variants = generate_query_variants(topic)
    queries_data = []

    serp_presence = False
    for i, q in enumerate(variants):
        res = simulate_search(q, delay)
        q_type = "primary" if i == 0 else "variant"
        queries_data.append({
            "query": q,
            "query_type": q_type,
            "status": res["status"],
            "results": res["results"]
        })
        if res["status"] == "success" and len(res["results"]) > 0:
            serp_presence = True

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
            "organic_result_count": 0,
            "unique_domains": 0
        },

        "generated_related_keywords": gen_related_kws,
        "observed_related_queries": [],

        "top_content": [],
        "content_gap": [],

        "search_volume": None,
        "search_volume_source": None,
        "competition": None,
        "competition_source": None,

        "existing_post": existing_post_data,

        "research_status": "failed" if not serp_presence else "complete",
        "errors": ["search_provider_unavailable"] if not serp_presence else []
    }

    save_json(result, cache_path)
    return result

def generate_report(results, summary, output_md):
    lines = [
        "# Topic Search Research Report\n",
        "## 1. Summary\n",
        f"- 조사 후보: {summary['input_count']}",
        f"- 성공: {summary['success_count']}",
        f"- 실패: {summary['failed_count']}\n",
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
            lines.append(f"  - {r['topic']} (Reason: {', '.join(r['errors'])})")

    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    parser = argparse.ArgumentParser(description="Topic Search Research Agent V1")
    parser.add_argument("--decision", type=str, default="KEEP", help="Validation decision to filter (KEEP, ALL, etc)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of topics to research")
    parser.add_argument("--topic", type=str, default=None, help="Specific topic to research")
    parser.add_argument("--refresh", action="store_true", help="Ignore cache and force refresh")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between searches in seconds")

    args = parser.parse_args()

    print("Blog Agent - Topic Search Research Agent V1\n")

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
    os.makedirs(cache_dir, exist_ok=True)

    results = []
    success_c = 0
    failed_c = 0
    serp_c = 0
    vol_c = 0
    intent_match = 0
    intent_mismatch = 0

    print("Researching...")
    for i, item in enumerate(targets):
        res = process_topic(item, original_candidates_dict, existing_posts_dict, cache_dir, args.delay, args.refresh)
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

    summary = {
        "input_count": len(targets),
        "researched_count": len(results),
        "success_count": success_c,
        "failed_count": failed_c,
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
