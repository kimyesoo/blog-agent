import json
import os
import sys

# ---------------------------------------------------------
# Seed Data Definitions
# ---------------------------------------------------------
TEST_TYPES = {
    "기본물성시험": ["함수비 시험", "비중 시험", "단위중량 시험"],
    "입도시험": ["체분석 시험", "비중계 시험"],
    "컨시스턴시시험": ["액성한계 시험", "소성한계 시험", "수축한계 시험"],
    "다짐시험": ["실내 다짐시험", "CBR 시험"],
    "밀도시험": ["들밀도 시험", "고무풍선법 밀도 시험"],
    "강도시험": ["일축압축시험", "직접전단시험", "삼축압축시험", "베인전단시험"],
    "압밀시험": ["표준 압밀시험", "급속 압밀시험"],
    "투수시험": ["정수두 투수시험", "변수두 투수시험"],
    "토질시험 실무": ["현장 다짐도 평가", "지반조사 보고서 해석", "시험 성적서 판독"]
}

INTENT_TEMPLATES = [
    {"intent": "정보 탐색", "content_type": "개념설명", "suffix": "이란?", "practical_value": "중간"},
    {"intent": "시험방법 확인", "content_type": "시험방법", "suffix": "방법", "practical_value": "높음"},
    {"intent": "계산방법 확인", "content_type": "계산방법", "suffix": "계산 방법", "practical_value": "높음"},
    {"intent": "결과 해석", "content_type": "결과해석", "suffix": "결과 해석", "practical_value": "높음"},
    {"intent": "기준 확인", "content_type": "기준정리", "suffix": "관련 기준", "practical_value": "중간"},
    {"intent": "현장 적용", "content_type": "현장가이드", "suffix": "현장 적용 방법", "practical_value": "높음"},
    {"intent": "문제 해결", "content_type": "문제해결", "suffix": "부적합 원인과 대책", "practical_value": "높음"}
]

def load_existing_posts(filepath="content_db/posts.json"):
    """Loads existing posts and returns a list of titles."""
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Returning empty list.")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        posts = json.load(f)
    return [post.get("title", "") for post in posts if isinstance(post, dict)]

def build_topic_seed_map(category="토질시험"):
    """Returns the seed map based on the category."""
    # For V1, we only fully support "토질시험".
    if category != "토질시험":
        print(f"Warning: Seed map for '{category}' is limited. Using basic fallback.")
        return {"일반": [f"{category} 기초"]}
    return TEST_TYPES

def normalize_title(title):
    """Normalizes titles by removing spaces to help detect duplicates like '체분석 시험방법' vs '체분석시험 방법'"""
    return title.replace(" ", "").strip()

def generate_content_candidates(seed_map, category, existing_titles):
    """Generates a structured list of candidates based on seed map and intents."""
    candidates = []

    # Pre-process existing titles for fast duplication checks
    norm_existing = {normalize_title(t): t for t in existing_titles}

    for cluster, tests in seed_map.items():
        for test in tests:
            for template in INTENT_TEMPLATES:
                # E.g., "들밀도 시험" + " " + "방법" = "들밀도 시험 방법"
                raw_topic = f"{test} {template['suffix']}"

                # Check for direct relationship with existing posts
                # For instance, if test is "들밀도 시험" and we have an existing post "들밀도 시험"
                related_existing = [
                    t for t in existing_titles
                    if test.replace(" ", "") in t.replace(" ", "") or t.replace(" ", "") in test.replace(" ", "")
                ]

                candidate = {
                    "topic": raw_topic.replace("  ", " ").strip(),
                    "topic_cluster": cluster,
                    "category": category,
                    "search_intent": template["intent"],
                    "content_type": template["content_type"],
                    "related_keywords": [
                        test,
                        f"{test} {template['suffix']}",
                        f"{test} 실무",
                        f"{test} 요약"
                    ],
                    "related_existing_posts": related_existing,
                    "practical_value": template["practical_value"],
                    "duplicate": False,
                    "reason": f"[{cluster}] 분류의 '{test}'에 대해 '{template['intent']}' 의도를 충족하는 콘텐츠 확장이 필요함."
                }
                candidates.append(candidate)

    return candidates

def remove_duplicates(candidates, existing_titles):
    """Marks and filters out duplicates based on existing titles."""
    norm_existing = {normalize_title(t) for t in existing_titles}
    filtered = []
    duplicate_count = 0

    # We also keep track of what we generated to avoid internal duplicates
    seen_norm = set()

    for candidate in candidates:
        norm_topic = normalize_title(candidate["topic"])

        # Check against existing posts
        if norm_topic in norm_existing:
            candidate["duplicate"] = True
            duplicate_count += 1
            continue

        # Check against already generated candidates in this run
        if norm_topic in seen_norm:
            candidate["duplicate"] = True
            duplicate_count += 1
            continue

        seen_norm.add(norm_topic)
        filtered.append(candidate)

    return filtered, duplicate_count

def save_candidates(candidates, output_dir="topic_research", filename="topic_candidates.json"):
    """Saves the candidate list to a JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)
    return filepath

def main():
    print("Blog Agent - Topic Research Agent V1\n")

    # Parse category from command line or default to "토질시험"
    category = "토질시험"
    if len(sys.argv) > 1:
        category = sys.argv[1]

    print(f"Research topic: {category}\n")

    # 1. Load existing posts
    existing_titles = load_existing_posts()
    print(f"Existing posts loaded: {len(existing_titles)}\n")

    # 2. Build seed map
    seed_map = build_topic_seed_map(category)

    # 3. Generate initial candidates
    print("Generating topic candidates...\n")
    raw_candidates = generate_content_candidates(seed_map, category, existing_titles)

    # 4. Remove duplicates
    final_candidates, duplicates_removed = remove_duplicates(raw_candidates, existing_titles)

    print(f"Candidates generated: {len(final_candidates)}")
    print(f"Duplicates removed: {duplicates_removed}\n")

    # 5. Summarize clusters
    cluster_counts = {}
    for c in final_candidates:
        cluster = c["topic_cluster"]
        cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1

    print("Topic clusters:")
    for cluster, count in cluster_counts.items():
        print(f"- {cluster}: {count}")

    # 6. Save
    saved_path = save_candidates(final_candidates)
    print(f"\nSaved:\n{saved_path}")

if __name__ == "__main__":
    main()
