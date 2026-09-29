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
    return re.sub(r'[^가-힣a-zA-Z0-9]', '', title)

def extract_core_concept(topic):
    words = topic.split()
    if "시험" in topic:
        idx = topic.find("시험") + 2
        return topic[:idx].strip()
    elif "조사" in topic or "평가" in topic:
        idx = max(topic.find("조사"), topic.find("평가")) + 2
        return topic[:idx].strip()
    return words[0] if words else ""

def validate_content_type(topic, current_ct):
    """V1.2 Content Type Validation"""
    suggested = current_ct

    # basic heuristic mapping
    if "다짐도 평가" in topic or "평가 방법" in topic:
        suggested = "평가방법"
    elif "보고서 해석" in topic or "성적서 판독" in topic:
        suggested = "결과해석"
    elif "부적합" in topic or "원인" in topic or "대책" in topic:
        suggested = "문제해결"
    elif "계산" in topic:
        suggested = "계산방법"
    elif "결과 해석" in topic:
        suggested = "결과해석"
    elif "현장 적용" in topic or "현장 실무" in topic:
        suggested = "현장실무"
    elif "이란" in topic or "개요" in topic:
        suggested = "개념설명"

    if current_ct == "시험방법" and not ("시험방법" in topic or "시험 방법" in topic):
        # Could be an over-classification, but only change if we didn't already
        if suggested == current_ct:
            suggested = "기타"

    valid = (suggested == current_ct)
    return valid, suggested

def validate_search_intent(topic, current_intent):
    """V1.2 Search Intent Validation"""
    suggested = current_intent

    if "방법" in topic and "계산" not in topic and "현장" not in topic:
        suggested = "시험방법 확인"
    elif "계산" in topic:
        suggested = "계산방법 확인"
    elif "결과 해석" in topic or "판독" in topic:
        suggested = "결과해석"
    elif "현장" in topic or "적용" in topic:
        suggested = "현장 적용"
    elif "부적합" in topic or "대책" in topic or "원인" in topic:
        suggested = "문제 해결"
    elif "이란" in topic or "개요" in topic or "개념" in topic:
        suggested = "정보 탐색"

    valid = (suggested == current_intent)
    return valid, suggested

def evaluate_standalone_value(topic, content_type):
    # 5: High independence, 4: likely, 3: medium, 2: low indep, 1: none
    if content_type in ["시험방법", "계산방법", "결과해석", "문제해결", "평가방법", "현장가이드", "현장실무"]:
        return "high", 5
    elif content_type in ["개념설명", "기준정리"]:
        if "이란" in topic or "개요" in topic:
            return "medium", 3
        else:
            return "high", 4
    elif "요약" in topic or "관련 정보" in topic:
        return "low", 2
    else:
        return "low", 1

def evaluate_clarity(topic):
    if "방법" in topic or "계산" in topic or "해석" in topic or "대책" in topic or "원인" in topic or "판독" in topic:
        return "high", 5
    elif "이란" in topic or "기준" in topic or "평가" in topic:
        return "high", 4
    elif "실무" in topic or "개념" in topic:
        return "medium", 3
    elif "요약" in topic or "관련" in topic:
        return "low", 2
    else:
        return "low", 1

def evaluate_practical_value(pv_str):
    if pv_str == "높음":
        return "high", 5
    elif pv_str == "중간":
        return "medium", 3
    else:
        return "low", 1

def evaluate_topic_specificity(topic):
    if "방법" in topic or "계산" in topic or "대책" in topic or "판독" in topic:
        return "high", 5
    elif "해석" in topic or "기준" in topic or "평가" in topic:
        return "high", 4
    elif "이란" in topic or "개념" in topic:
        return "medium", 3
    elif "실무" in topic:
        return "medium", 2
    else:
        return "low", 1

def evaluate_content_gap(norm_topic, norm_core, existing_titles, content_type):
    for ext in existing_titles:
        norm_ext = normalize_title(ext)
        if norm_topic == norm_ext:
            return "low", 0 # Exact duplicate

        # Existing post is generic (e.g. 들밀도 시험) but we have specific method
        if norm_core == norm_ext and content_type == "시험방법":
            return "medium", 2 # Overlap possible, requires REVIEW

    related = any(norm_core in normalize_title(t) or normalize_title(t) in norm_core for t in existing_titles)
    if related:
        return "high", 4 # Safe extension
    return "high", 5 # New topic entirely

def process_candidates(candidates, existing_titles):
    validated_results = []
    stats = {"keep": 0, "merge": 0, "reject": 0, "review": 0}

    # 1. First pass: augment candidates with validation metrics
    augmented = []
    groups = defaultdict(list)

    for c in candidates:
        topic = c["topic"]
        core = extract_core_concept(topic)
        current_ct = c.get("content_type", "")
        current_intent = c.get("search_intent", "")

        # Content Type / Intent Validation
        ct_valid, ct_suggested = validate_content_type(topic, current_ct)
        si_valid, si_suggested = validate_search_intent(topic, current_intent)

        c["_temp_ct"] = ct_suggested
        c["_temp_intent"] = si_suggested
        c["_temp_core"] = core

        sv_str, sv_score = evaluate_standalone_value(topic, ct_suggested)
        cl_str, cl_score = evaluate_clarity(topic)
        pv_str, pv_score = evaluate_practical_value(c.get("practical_value", ""))
        ts_str, ts_score = evaluate_topic_specificity(topic)
        cg_str, cg_score = evaluate_content_gap(normalize_title(topic), normalize_title(core), existing_titles, ct_suggested)

        total_score = sv_score + cl_score + pv_score + ts_score + cg_score

        # Include search_intent in the similarity group key to prevent aggressive merging
        # of topics with different intents
        group_key_intent = si_suggested if si_suggested else current_intent

        result = {
            "topic": topic,
            "topic_cluster": c.get("topic_cluster", ""),
            "category": c.get("category", ""),
            "search_intent": current_intent,
            "content_type": current_ct,
            "validation": {
                "decision": "",
                "duplicate": cg_score == 0,
                "similarity_group": f"{core}_{ct_suggested}_{group_key_intent}",
                "standalone_value": sv_str,
                "clarity": cl_str,
                "practical_value": pv_str,
                "topic_specificity": ts_str,
                "content_gap": cg_str,
                "content_type_valid": ct_valid,
                "content_type_suggested": ct_suggested if not ct_valid else None,
                "search_intent_valid": si_valid,
                "search_intent_suggested": si_suggested if not si_valid else None,
                "confidence": "medium" # Will adjust below
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
            "related_topics": [],
            "suggested_topic": topic,
            "reason": ""
        }
        augmented.append(result)

        # Group by similarity key
        group_key = result["validation"]["similarity_group"]
        groups[group_key].append(result)

    # 2. Second pass: Decision Logic (KEEP, MERGE, REJECT, REVIEW)
    for group_key, items in groups.items():
        # Identify related topics across the core concept (for related_topics population)
        core_concept = items[0]["validation"]["similarity_group"].split("_")[0]
        all_core_topics = [a["topic"] for a in augmented if a["validation"]["similarity_group"].startswith(core_concept)]

        for item in items:
            item["related_topics"] = [t for t in all_core_topics if t != item["topic"]]

            # REJECT conditions
            if item["validation"]["duplicate"]:
                item["validation"]["decision"] = "reject"
                item["validation"]["confidence"] = "high"
                item["reason"] = "기존 게시물과 명확하게 중복되는 주제임."
                stats["reject"] += 1
                continue

            # REVIEW conditions
            if item["score_detail"]["content_gap"] == 2:
                # Existing generic post exists, this is a method post. Don't reject, but REVIEW
                item["validation"]["decision"] = "review"
                item["validation"]["confidence"] = "medium"
                item["reason"] = "기존에 포괄적인 주제의 게시물이 존재하여, 본 내용의 중복 여부를 원문 확인 후 판단해야 함."
                stats["review"] += 1
                continue

            if not item["validation"]["content_type_valid"] or not item["validation"]["search_intent_valid"]:
                # Misclassified or ambiguous intent -> REVIEW
                # BUT if it's part of a mergeable cluster, we might merge it. Let's defer to merge logic if len > 1.
                if len(items) == 1:
                    item["validation"]["decision"] = "review"
                    item["validation"]["confidence"] = "low"
                    item["reason"] = "콘텐츠 유형이나 검색 의도가 모호하거나 재분류가 필요함."
                    stats["review"] += 1
                    continue

        # MERGE conditions
        # Filter items that are not already rejected/reviewed
        valid_items = [i for i in items if i["validation"]["decision"] == ""]

        if len(valid_items) > 1:
            # We have multiple items with the exact same core concept and content type/intent.
            # Example: "함수비 시험 이란?" and "함수비 시험 개요"

            # Sort to find the best representative
            valid_items.sort(key=lambda x: x["validation_score"], reverse=True)
            rep = valid_items[0]

            # Exclude self from merge_candidates
            merged_names = [x["topic"] for x in valid_items[1:]]
            rep["validation"]["decision"] = "merge"
            rep["validation"]["confidence"] = "high"
            rep["merge_candidates"] = merged_names

            # Filter out merged items from related_topics
            rep["related_topics"] = [t for t in rep["related_topics"] if t not in merged_names]

            intent = rep["validation"].get("search_intent_suggested") or rep["search_intent"]

            if intent == "정보 탐색":
                rep["suggested_topic"] = f"{core_concept}의 개념과 개요"
            elif intent == "시험방법 확인":
                rep["suggested_topic"] = f"{core_concept} 방법 및 절차"
            else:
                rep["suggested_topic"] = f"{core_concept} 통합 정리"

            rep["reason"] = "동일한 정보 목적을 가진 매우 유사한 주제들이 존재하여 통합하는 것이 합리적임."

            stats["merge"] += len(valid_items)

            # We only append the representative to our final valid list
            validated_results.append(rep)
        elif len(valid_items) == 1:
            # KEEP
            item = valid_items[0]
            item["validation"]["decision"] = "keep"
            item["validation"]["confidence"] = "high"
            item["reason"] = "독립적인 정보 목적을 가지며 차별성 있는 콘텐츠로 작성할 가치가 높음."
            stats["keep"] += 1
            validated_results.append(item)

        # Append rejected/reviewed items to the final output as well (they are still part of the pool)
        for item in items:
            if item["validation"]["decision"] in ["reject", "review"]:
                validated_results.append(item)

        # Also, if multiple valid items were found but not merged because the condition (len(valid_items) > 1)
        # somehow bypassed (which it shouldn't), we ensure all original items are accounted for.
        # However, for merged items, the non-representative ones need to be appended with a "merged_into" status
        # to maintain the 158 output count if the prompt implied 158 should be outputted.
        # Based on constraints: `validated_results` should contain exactly all processed topics.
        if len(valid_items) > 1:
            for item in valid_items[1:]:
                item["validation"]["decision"] = "merge_child"
                item["validation"]["confidence"] = "high"
                item["reason"] = f"'{rep['topic']}' (으)로 통합됨."
                validated_results.append(item)

    validated_results.sort(key=lambda x: x["validation_score"], reverse=True)
    return validated_results, stats, groups

def save_results(results, stats, output_dir="topic_research"):
    os.makedirs(output_dir, exist_ok=True)

    val_path = os.path.join(output_dir, "validated_topics.json")
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    sum_path = os.path.join(output_dir, "validation_summary.json")
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    return val_path, sum_path

def main():
    print("Topic Validation Agent V1.2")
    print("=========================\n")

    candidates = load_candidates()
    if not candidates:
        return

    existing_titles = load_existing_posts()

    validated_results, stats, groups = process_candidates(candidates, existing_titles)

    # Calculate group count (unique core concepts)
    unique_cores = set([g.split("_")[0] for g in groups.keys()])

    print(f"Input candidates: {len(candidates)}")
    print(f"Similarity groups: {len(groups)} (Core concepts: {len(unique_cores)})\n")

    print("Validation complete.\n")
    print(f"KEEP: {stats['keep']}")
    print(f"MERGE: {stats['merge']}")
    print(f"REJECT: {stats['reject']}")
    print(f"REVIEW: {stats['review']}\n")

    print(f"Validated topics generated: {len(validated_results)}\n")

    val_path, sum_path = save_results(validated_results, {
        "input_count": len(candidates),
        "keep_count": stats["keep"],
        "merge_count": stats["merge"],
        "reject_count": stats["reject"],
        "review_count": stats["review"],
        "similarity_group_count": len(groups)
    })

    print("Outputs:")
    print("-", val_path)
    print("-", sum_path)

if __name__ == "__main__":
    main()
