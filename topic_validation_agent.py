import json
import os
import re
from collections import defaultdict

def load_candidates(filepath="topic_research/topic_candidates.json"):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def load_existing_posts(filepath="content_db/posts.json"):
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found.")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        posts = json.load(f)
    return [post.get("title", "") for post in posts if isinstance(post, dict)]

def normalize_title(title):
    """Removes spaces and special characters for comparison."""
    return re.sub(r'[^가-힣a-zA-Z0-9]', '', title)

def check_duplicate(norm_topic, existing_titles):
    norm_existing = [normalize_title(t) for t in existing_titles]
    return norm_topic in norm_existing

def extract_core_concept(topic):
    """Extracts the core concept from a topic."""
    words = topic.split()
    if "시험" in topic:
        idx = topic.find("시험") + 2
        return topic[:idx].strip()
    return words[0] if words else ""

def get_similarity_group_key(candidate):
    """
    Groups candidates by Core Concept + Content Type / Intent.
    Instead of just '함수비 시험', it becomes '함수비 시험_개념설명'.
    """
    core = extract_core_concept(candidate["topic"])
    content_type = candidate.get("content_type", "")

    # We can treat similar intents as the same group to encourage merging
    if content_type in ["개념설명"]:
        return f"{core}_개념"
    elif content_type in ["시험방법"]:
        return f"{core}_방법"
    elif content_type in ["계산방법"]:
        return f"{core}_계산"
    elif content_type in ["결과해석"]:
        return f"{core}_결과"
    elif content_type in ["현장가이드", "문제해결", "실무"]:
        return f"{core}_실무"
    else:
        return f"{core}_기타"

def group_similar_topics(candidates):
    groups = defaultdict(list)
    for idx, candidate in enumerate(candidates):
        key = get_similarity_group_key(candidate)
        groups[key].append(idx)
    return groups

def evaluate_standalone_value(candidate):
    content_type = candidate.get("content_type", "")
    topic = candidate.get("topic", "")

    if content_type in ["시험방법", "계산방법", "결과해석", "현장가이드"]:
        return "high", 5
    elif content_type in ["개념설명", "기준정리"]:
        return "medium", 3
    elif "요약" in topic or "관련" in topic or "개요" in topic:
        return "low", 1
    else:
        return "low", 1

def evaluate_clarity(candidate):
    topic = candidate.get("topic", "")
    if "방법" in topic or "계산" in topic or "결과" in topic or "대책" in topic:
        return "high", 5
    elif "이란" in topic or "개념" in topic or "기준" in topic:
        return "medium", 3
    else:
        return "low", 1

def evaluate_practical_value(candidate):
    pv = candidate.get("practical_value", "medium")
    if pv == "높음":
        return "high", 5
    elif pv == "중간":
        return "medium", 3
    else:
        return "low", 1

def evaluate_topic_specificity(candidate):
    topic = candidate.get("topic", "")
    if "방법" in topic or "계산" in topic or "원인" in topic:
        return 5
    elif "해석" in topic or "기준" in topic:
        return 4
    elif "이란" in topic:
        return 3
    else:
        return 2

def evaluate_content_gap(candidate, existing_titles):
    norm_topic = normalize_title(candidate["topic"])
    core = extract_core_concept(candidate["topic"])
    norm_core = normalize_title(core)

    for ext in existing_titles:
        norm_ext = normalize_title(ext)
        if norm_topic == norm_ext:
            return 1 # Duplicate

        # If it's the exact same core concept, we consider how different the content type is
        # If the existing post is just the core concept (e.g., "들밀도 시험")
        # and this is "들밀도 시험 방법", it's basically the same thing.
        if norm_core == norm_ext and candidate.get("content_type") == "시험방법":
            return 2 # High chance of overlap with general post

    # Related but different content type
    related = any(norm_core in normalize_title(t) or normalize_title(t) in norm_core for t in existing_titles)
    if related:
        return 4
    return 5

def process_candidates(candidates, existing_titles):
    validated_results = []
    stats = {"keep": 0, "merge": 0, "reject": 0}

    groups = group_similar_topics(candidates)

    for group_key, indices in groups.items():
        group_candidates = [candidates[i] for i in indices]

        valid_items_in_group = []

        # Evaluate all items in this group
        for c in group_candidates:
            norm_topic = normalize_title(c["topic"])
            is_dup = check_duplicate(norm_topic, existing_titles)

            sv_str, sv_score = evaluate_standalone_value(c)
            cl_str, cl_score = evaluate_clarity(c)
            pv_str, pv_score = evaluate_practical_value(c)
            ts_score = evaluate_topic_specificity(c)
            cg_score = evaluate_content_gap(c, existing_titles)

            # Additional heuristic: If existing post is "들밀도 시험" and this is "들밀도 시험 방법", it's a reject
            if cg_score <= 2 and not is_dup:
                 is_dup = True # Treat as logical duplicate

            total_score = sv_score + cl_score + pv_score + ts_score + cg_score

            result = {
                "topic": c["topic"],
                "topic_cluster": c.get("topic_cluster", ""),
                "category": c.get("category", ""),
                "search_intent": c.get("search_intent", ""),
                "content_type": c.get("content_type", ""),
                "validation": {
                    "decision": "",
                    "duplicate": is_dup,
                    "similarity_group": group_key,
                    "standalone_value": sv_str,
                    "clarity": cl_str,
                    "practical_value": pv_str
                },
                "validation_score": total_score,
                "score_detail": {
                    "standalone_value": sv_score,
                    "clarity": cl_score,
                    "practical_value": pv_score,
                    "topic_specificity": ts_score,
                    "content_gap": cg_score
                },
                "related_existing_posts": c.get("related_existing_posts", []),
                "merge_candidates": [],
                "suggested_topic": c["topic"],
                "reason": ""
            }

            if is_dup:
                result["validation"]["decision"] = "reject"
                result["reason"] = "기존 게시물과 내용 범위가 사실상 동일하여 별도 게시물로 작성할 필요성이 낮음."
                stats["reject"] += 1
                validated_results.append(result)
            else:
                valid_items_in_group.append(result)

        # Now handle the non-rejected items in this similarity group
        if not valid_items_in_group:
            continue

        # If there are multiple items with the same intent/content type for the same core test, merge them.
        if len(valid_items_in_group) > 1:
            # Sort by score to find the best representative
            valid_items_in_group.sort(key=lambda x: x["validation_score"], reverse=True)
            best_rep = valid_items_in_group[0]

            merged_names = [item["topic"] for item in valid_items_in_group]

            best_rep["validation"]["decision"] = "merge"
            best_rep["merge_candidates"] = merged_names

            # Create a suggested topic based on the group key
            core_name = group_key.split('_')[0]
            intent_name = group_key.split('_')[1] if '_' in group_key else ""

            if intent_name == "개념":
                best_rep["suggested_topic"] = f"{core_name}의 개념과 개요"
            elif intent_name == "방법":
                best_rep["suggested_topic"] = f"{core_name} 수행 방법 가이드"
            elif intent_name == "결과":
                best_rep["suggested_topic"] = f"{core_name} 결과 해석 및 정리"
            else:
                best_rep["suggested_topic"] = f"{core_name} 통합 가이드"

            best_rep["reason"] = f"'{merged_names[0]}' 등 동일 목적(content_type)의 유사 후보들과 겹치므로 하나의 콘텐츠로 통합함."

            stats["merge"] += len(valid_items_in_group)
            validated_results.append(best_rep)
        else:
            item = valid_items_in_group[0]
            # Even if it's the only one, check if it's too weak
            if item["validation_score"] < 15 or item["validation"]["standalone_value"] == "low":
                item["validation"]["decision"] = "reject"
                item["reason"] = "독립적인 콘텐츠로서의 가치(명확성/실무가치)가 부족하여 반려함."
                stats["reject"] += 1
            else:
                item["validation"]["decision"] = "keep"
                item["reason"] = "독립적인 정보 목적을 가지며 기존 게시물과 중복되지 않는 가치 있는 주제임."
                stats["keep"] += 1
            validated_results.append(item)

    validated_results.sort(key=lambda x: x["validation_score"], reverse=True)
    return validated_results, stats, groups

def save_results(results, output_dir="topic_research", filename="validated_topics.json"):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return filepath

def main():
    print("Topic Validation Agent V1.1")
    print("=========================\n")

    candidates = load_candidates()
    if not candidates:
        return

    print(f"Input candidates: {len(candidates)}")

    existing_titles = load_existing_posts()

    validated_results, stats, groups = process_candidates(candidates, existing_titles)

    print(f"\nSimilarity groups: {len(groups)}")
    print("\nValidation complete.\n")
    print(f"KEEP: {stats['keep']}")
    print(f"MERGE: {stats['merge']}")
    print(f"REJECT: {stats['reject']}\n")
    print(f"Validated topics: {len(validated_results)}\n")

    saved_path = save_results(validated_results)
    print("Output:")
    print(saved_path)

if __name__ == "__main__":
    main()
