import json
import os
import re

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
    """Extracts the core concept from a topic to help with similarity grouping."""
    words = topic.split()
    # Simple heuristic: Usually the first 1-2 words indicate the core test/concept.
    if "시험" in topic:
        idx = topic.find("시험") + 2
        return topic[:idx].strip()
    return words[0] if words else ""

def group_similar_topics(candidates):
    """Groups candidates by their core concept."""
    groups = {}
    for idx, candidate in enumerate(candidates):
        core = extract_core_concept(candidate["topic"])
        if core not in groups:
            groups[core] = []
        groups[core].append(idx)
    return groups

def evaluate_standalone_value(candidate):
    intent = candidate.get("search_intent", "")
    content_type = candidate.get("content_type", "")

    if content_type in ["시험방법", "문제해결", "현장가이드", "계산방법"]:
        return "high", 5
    elif content_type in ["개념설명", "기준정리"]:
        return "medium", 3
    else:
        return "low", 1

def evaluate_clarity(candidate):
    topic = candidate.get("topic", "")
    if "방법" in topic or "계산" in topic or "원인" in topic or "대책" in topic:
        return "high", 5
    elif "이란" in topic or "개념" in topic or "기준" in topic:
        return "medium", 3
    else:
        return "low", 1

def evaluate_practical_value(candidate):
    # Base it off the existing practical_value if it exists, otherwise infer
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

    related = False
    for ext in existing_titles:
        norm_ext = normalize_title(ext)
        if norm_topic == norm_ext:
            return 1 # Duplicate
        if norm_core in norm_ext or norm_ext in norm_core:
            related = True

    if related:
        # Related to existing, but not duplicate. Good for expansion.
        return 4
    else:
        # Completely new area.
        return 5

def calculate_validation_score(evaluations):
    return sum([
        evaluations["standalone_score"],
        evaluations["clarity_score"],
        evaluations["practical_score"],
        evaluations["specificity_score"],
        evaluations["gap_score"]
    ])

def process_candidates(candidates, existing_titles):
    validated_results = []

    # 1. Similarity Grouping (Identify candidates sharing the same core concept)
    groups = group_similar_topics(candidates)

    # Track indices that have been merged
    merged_indices = set()

    stats = {"keep": 0, "merge": 0, "reject": 0}

    for core, indices in groups.items():
        group_candidates = [candidates[i] for i in indices]

        # Determine if we should merge this group
        # If there are multiple low/medium standalone value items, we merge them.
        merge_list = []
        keep_list = []

        for idx in indices:
            c = candidates[idx]
            norm_topic = normalize_title(c["topic"])
            is_dup = check_duplicate(norm_topic, existing_titles)

            # Evaluate metrics
            sv_str, sv_score = evaluate_standalone_value(c)
            cl_str, cl_score = evaluate_clarity(c)
            pv_str, pv_score = evaluate_practical_value(c)
            ts_score = evaluate_topic_specificity(c)
            cg_score = evaluate_content_gap(c, existing_titles)

            total_score = sv_score + cl_score + pv_score + ts_score + cg_score

            evaluations = {
                "decision": "",
                "duplicate": is_dup,
                "similarity_group": core,
                "standalone_value": sv_str,
                "clarity": cl_str,
                "practical_value": pv_str
            }

            score_detail = {
                "standalone_value": sv_score,
                "clarity": cl_score,
                "practical_value": pv_score,
                "topic_specificity": ts_score,
                "content_gap": cg_score
            }

            result = {
                "topic": c["topic"],
                "topic_cluster": c.get("topic_cluster", ""),
                "category": c.get("category", ""),
                "search_intent": c.get("search_intent", ""),
                "content_type": c.get("content_type", ""),
                "validation": evaluations,
                "validation_score": total_score,
                "score_detail": score_detail,
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
            elif total_score < 15 or sv_str == "low":
                # Candidate for merge
                merge_list.append(result)
            else:
                # Keep
                result["validation"]["decision"] = "keep"
                result["reason"] = "독립적인 콘텐츠로 작성할 가치가 있으며 기존 게시물과 직접적인 중복이 없음."
                stats["keep"] += 1
                keep_list.append(result)

        # Handle merges for this group
        if merge_list:
            if len(merge_list) == 1:
                # Only one weak topic, just keep it or reject it. Let's keep it but note it's weak.
                m = merge_list[0]
                m["validation"]["decision"] = "keep"
                m["reason"] = "독립성은 다소 낮으나 통합할 다른 유사 후보가 없어 개별 유지함."
                stats["keep"] += 1
                validated_results.append(m)
            else:
                # Create a single merged entry
                best_merge = max(merge_list, key=lambda x: x["validation_score"])
                merged_names = [m["topic"] for m in merge_list]

                best_merge["validation"]["decision"] = "merge"
                best_merge["merge_candidates"] = merged_names
                best_merge["suggested_topic"] = f"{core} 통합 가이드"
                best_merge["reason"] = f"'{merged_names[0]}' 등 유사 후보와 콘텐츠 범위가 겹치므로 하나의 통합 콘텐츠로 묶는 것이 적절함."
                stats["merge"] += 1
                validated_results.append(best_merge)

        validated_results.extend(keep_list)

    # Sort results for consistent output
    validated_results.sort(key=lambda x: x["validation_score"], reverse=True)
    return validated_results, stats

def save_results(results, output_dir="topic_research", filename="validated_topics.json"):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return filepath

def main():
    print("Topic Validation Agent V1")
    print("=========================\n")

    candidates = load_candidates()
    if not candidates:
        return

    print(f"Input candidates: {len(candidates)}")

    existing_titles = load_existing_posts()

    validated_results, stats = process_candidates(candidates, existing_titles)

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
