import json

with open("research/summary_reg.json") as f:
    reg = json.load(f)

for r in reg:
    if r["content_archetype"] == "regulatory":
        print(f"Topic: {r['topic']} | Top Source: {r['top_source_priority']}")
        print(f"Weights: {r['evidence_weight']}")
        print(f"Ranked sources:")
        for s in r['evidence_hierarchy']['ranked_sources']:
             print(f"  {s['source_type']} | {s['authority_tier']} | {s['url']}")
        print("---")
        break
