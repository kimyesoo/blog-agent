import json
import os
import sys

from topic_research_agent import TopicResearchAgentV2_1

class MetricAgent(TopicResearchAgentV2_1):
    def extract_metrics(self):
        with open(self.taxonomy_file, 'r') as f:
            taxonomy = json.load(f)

        existing_posts = []
        if os.path.exists(self.posts_file):
            with open(self.posts_file, 'r') as f:
                existing_posts = json.load(f)

        all_evaluated = []
        generated_concepts = set()

        import random
        random.seed(123)

        for main_cat, data in taxonomy.items():
            subcategories = data.get("subcategories", [])
            shuffled_subs = list(subcategories)
            random.shuffle(shuffled_subs)

            count = 0
            attempts = 0

            while count < 10 and attempts < 60 and shuffled_subs:
                sub = shuffled_subs[attempts % len(shuffled_subs)]
                intent = random.choice(self.all_intents)
                attempts += 1

                eval_res = self.evaluate_quality(main_cat, sub, intent)
                concept, title, content_type = self.generate_concept_and_title(sub, intent)

                is_dup, dup_reason = self.is_duplicate(title, intent, sub, existing_posts, generated_concepts)

                status = "accepted"
                if eval_res["score"] < 50:
                    status = "discarded_quality"
                elif is_dup:
                    status = "discarded_duplicate"
                    eval_res["flags"].append(dup_reason)
                else:
                    generated_concepts.add(f"{sub}_{intent}")
                    count += 1

                all_evaluated.append({
                    "topic": title,
                    "concept": concept,
                    "topic_cluster": main_cat,
                    "category": sub,
                    "search_intent": intent,
                    "status": status,
                    "quality_score": eval_res["score"],
                    "quality_flags": eval_res["flags"],
                    "compatibility": eval_res["metrics"]
                })

        return all_evaluated

def run():
    agent = MetricAgent()
    results = agent.extract_metrics()

    accepted = [r for r in results if r["status"] == "accepted"]

    print("=== 1. 전체 160개 topic 목록 ===")
    for idx, r in enumerate(accepted):
        print(f"[{idx+1}] {r['topic']} (Category: {r['category']}, Intent: {r['search_intent']})")

    print("\n\n=== 2. quality_score 하위 30개 ===")
    sorted_by_score = sorted(results, key=lambda x: x["quality_score"])
    for idx, r in enumerate(sorted_by_score[:30]):
        print(f"[{idx+1}] {r['topic']} | Score: {r['quality_score']} | Flags: {r['quality_flags']}")

    print("\n\n=== 3. quality_flags가 하나라도 있는 모든 topic ===")
    flagged = [r for r in results if len(r["quality_flags"]) > 0]
    for r in flagged:
        print(f"- {r['topic']} | Flags: {r['quality_flags']}")

    print("\n\n=== 4. Category(대분류)별 대표 topic 3개씩 ===")
    cat_map = {}
    for r in accepted:
        c = r["topic_cluster"]
        if c not in cat_map:
            cat_map[c] = []
        if len(cat_map[c]) < 3:
            cat_map[c].append(r)

    for c, items in cat_map.items():
        print(f"[{c}]")
        for i in items:
            print(f"  - {i['topic']}")

    print("\n\n=== 5. 동일/유사 concept로 판단된 topic 그룹 (duplicate_concept) ===")
    duplicate_concepts = [r for r in results if "duplicate_concept" in r["quality_flags"]]
    # group them by concept
    from collections import defaultdict
    dup_map = defaultdict(list)
    for r in duplicate_concepts:
        dup_map[r["concept"]].append(r["topic"])

    for concept, topics in dup_map.items():
        print(f"Concept: {concept}")
        for t in topics:
            print(f"  - {t} (Discarded)")

    if not duplicate_concepts:
        print("  - 없음 (This run didn't trigger duplicate concept rejections within the threshold).")

    print("\n\n=== 6. intent compatibility score가 낮은 topic (Semantic < 50) ===")
    low_intent = [r for r in results if r["compatibility"]["semantic"] < 50]
    for r in low_intent[:20]: # limit to 20 for readability
        print(f"- {r['topic']} | Intent: {r['search_intent']} | Semantic: {r['compatibility']['semantic']}")

    print("\n\n=== 7. specificity score가 낮은 topic (Specificity < 50) ===")
    low_spec = [r for r in results if r["compatibility"]["specificity"] < 50]
    for r in low_spec:
        print(f"- {r['topic']} | Specificity: {r['compatibility']['specificity']} | Flags: {r['quality_flags']}")

if __name__ == '__main__':
    run()
