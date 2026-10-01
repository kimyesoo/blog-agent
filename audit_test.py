import json

with open("research/search_results.json") as f:
    results = json.load(f)

with open("research/summary_reg.json") as f:
    reg = json.load(f)

print("Topics where Top Source is technical_standard in regulation_focus:")
for r in reg:
    if r["top_source_priority"] == "technical_standard" and r["content_archetype"] == "regulatory":
        print(f"Topic: {r['topic']}")
        print(f"Evidence: {[e['url'] for e in r['evidence_hierarchy']['ranked_sources']]}")
        # find queries
        topic_res = next((res for res in results if res["topic"] == r["topic"]), None)
        if topic_res:
            print(f"Queries: {topic_res['queries']}")
            print(f"Raw SERP domains: {[s['domain'] for s in topic_res['serp_results']]}")
        print("---")
        break
