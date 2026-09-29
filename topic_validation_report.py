import json
import os
from collections import defaultdict

def load_json(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_distribution(data_list, key_extractor):
    dist = defaultdict(int)
    total = len(data_list)
    for item in data_list:
        val = key_extractor(item)
        dist[val] += 1

    result = {}
    # sort by count descending
    for k, v in sorted(dist.items(), key=lambda x: x[1], reverse=True):
        result[str(k)] = {
            "count": v,
            "percentage": round((v / total * 100), 2) if total > 0 else 0.0
        }
    return result

def categorize_review_reason(r_item):
    """
    Parses V1.2.1 reason_codes array if available,
    otherwise falls back to heuristic parsing of the string reason.
    """
    codes = r_item.get("reason_codes", [])
    if codes:
        return codes

    reason = r_item.get("reason", "")
    if "포괄적인" in reason or "중복 여부를 원문 확인" in reason:
        return ["existing_content_overlap"]
    elif "유형" in reason or "재분류" in reason:
        if "모호" in reason:
            return ["title_semantic_ambiguity"]
        else:
            return ["content_type_reclassification"]
    elif "가치" in reason or "부족하여" in reason:
        return ["low_confidence"]
    else:
        return ["other"]

def generate_report_data(topics, summary):
    total = len(topics)

    # 1. Base distribution
    keep_topics = [t for t in topics if t["validation"]["decision"] == "keep"]
    merge_topics = [t for t in topics if t["validation"]["decision"] in ["merge", "merge_child"]]
    primary_merge_topics = [t for t in topics if t["validation"]["decision"] == "merge"]
    review_topics = [t for t in topics if t["validation"]["decision"] == "review"]
    reject_topics = [t for t in topics if t["validation"]["decision"] == "reject"]

    decision_distribution = {
        "keep": {"count": len(keep_topics), "percentage": round((len(keep_topics) / total * 100), 2)},
        "merge": {"count": len(merge_topics), "percentage": round((len(merge_topics) / total * 100), 2)},
        "review": {"count": len(review_topics), "percentage": round((len(review_topics) / total * 100), 2)},
        "reject": {"count": len(reject_topics), "percentage": round((len(reject_topics) / total * 100), 2)}
    }

    # 2. KEEP Analysis
    keep_analysis = {
        "by_content_type": calculate_distribution(keep_topics, lambda x: x["content_type"]),
        "by_search_intent": calculate_distribution(keep_topics, lambda x: x["search_intent"]),
        "by_validation_score": calculate_distribution(keep_topics, lambda x: x["validation_score"])
    }

    # 3. MERGE Analysis (Only use primary merge items for group analysis)
    merge_analysis = []
    for m in primary_merge_topics:
        self_ref = m["topic"] in m.get("merge_candidates", [])
        merge_analysis.append({
            "canonical_topic": m.get("suggested_topic", m["topic"]),
            "merge_group_id": m["validation"]["similarity_group"],
            "child_topics": m.get("merge_candidates", []),
            "child_count": len(m.get("merge_candidates", [])),
            "reason": m.get("reason", ""),
            "confidence": m["validation"]["confidence"],
            "self_reference_detected": self_ref
        })

    # 4. REVIEW Analysis
    review_reasons_dist = defaultdict(int)
    review_details = []
    reclassifications = []

    for r in review_topics:
        codes = categorize_review_reason(r)
        for code in codes:
            review_reasons_dist[code] += 1

    # Track all reclassifications across all decisions, not just REVIEW
    for r in topics:
        if r["validation"]["decision"] == "merge_child":
            continue

        orig_ct = r.get("content_type", "")
        sugg_ct = r["validation"].get("content_type_suggested") or orig_ct

        if orig_ct != sugg_ct:
            reclassifications.append({
                "topic": r["topic"],
                "original": orig_ct,
                "suggested": sugg_ct,
                "decision": r["validation"]["decision"]
            })

        if r["validation"]["decision"] == "review":
            review_details.append({
                "topic": r["topic"],
                "decision": "review",
                "reason": r.get("reason", ""),
                "reason_codes": r.get("reason_codes", categorize_review_reason(r)),
                "confidence": r["validation"]["confidence"],
                "validation_score": r["validation_score"],
                "content_type_original": orig_ct,
                "content_type_suggested": sugg_ct,
                "search_intent": r.get("search_intent", ""),
                "related_existing_posts": r.get("related_existing_posts", []),
                "merge_candidates": r.get("merge_candidates", []),
                "related_topics": r.get("related_topics", [])
            })

    # 5. Confidence Analysis
    confidence_distribution = calculate_distribution(topics, lambda x: x["validation"].get("confidence", "unknown"))

    # Cross-tabulation: Confidence x Decision
    confidence_by_decision = {
        "high": {"keep": 0, "merge": 0, "review": 0, "reject": 0},
        "medium": {"keep": 0, "merge": 0, "review": 0, "reject": 0},
        "low": {"keep": 0, "merge": 0, "review": 0, "reject": 0}
    }

    low_confidence_topics = []
    for t in topics:
        dec = t["validation"]["decision"]
        conf = t["validation"].get("confidence", "unknown").lower()
        if conf in confidence_by_decision and dec in ["keep", "merge", "review", "reject"]:
            confidence_by_decision[conf][dec] += 1

        if conf == "low":
            low_confidence_topics.append({
                "topic": t["topic"],
                "decision": t["validation"]["decision"],
                "reason": t.get("reason", ""),
                "validation_score": t.get("validation_score", 0),
                "confidence": "low"
            })

    # 6. Similarity Group Analysis
    sim_groups = defaultdict(list)
    for t in topics:
        sim_groups[t["validation"]["similarity_group"]].append(t)

    group_sizes = {"single_topic_groups": 0, "two_topic_groups": 0, "three_or_more_topic_groups": 0}
    multi_topic_groups = []
    for g, items in sim_groups.items():
        size = len(items)
        if size == 1:
            group_sizes["single_topic_groups"] += 1
        elif size == 2:
            group_sizes["two_topic_groups"] += 1
            multi_topic_groups.append({"group": g, "topics": [i["topic"] for i in items]})
        else:
            group_sizes["three_or_more_topic_groups"] += 1
            multi_topic_groups.append({"group": g, "topics": [i["topic"] for i in items]})

    # 7. Anomaly Patterns
    anomalies = defaultdict(list)
    for t in topics:
        dec = t["validation"]["decision"]
        conf = t["validation"].get("confidence", "")
        score = t.get("validation_score", 0)

        if dec == "merge" and score >= 23:
            anomalies["high_score_merge"].append(t["topic"])
        if dec == "keep" and conf == "low":
            anomalies["low_confidence_keep"].append(t["topic"])
        if dec == "review" and conf == "high":
            anomalies["high_confidence_review"].append(t["topic"])
        if dec == "reject" and conf == "low":
            anomalies["low_confidence_reject"].append(t["topic"])
        if dec == "merge" and t["topic"] in t.get("merge_candidates", []):
            anomalies["self_reference_in_merge"].append(t["topic"])

        grp = t["validation"].get("similarity_group", "")
        if grp in ["현장_방법", "현장_계산", "현장_실무"]:
            anomalies["generic_similarity_group"].append(t["topic"])

    # 8. Representative Cases
    rep_cases = {
        "keep_high_score": [t["topic"] for t in sorted(keep_topics, key=lambda x: x["validation_score"], reverse=True)[:3]],
        "keep_low_score": [t["topic"] for t in sorted(keep_topics, key=lambda x: x["validation_score"])[:3]],
        "merge_groups": [m["topic"] for m in primary_merge_topics[:3]],
        "review_existing_overlap": [r["topic"] for r in review_details if "existing_content_overlap" in r.get("reason_codes", [])][:2],
        "review_content_reclass": [r["topic"] for r in review_details if "content_type_reclassification" in r.get("reason_codes", [])][:2],
        "review_semantic": [r["topic"] for r in review_details if "title_semantic_ambiguity" in r.get("reason_codes", [])][:2],
        "review_low_confidence": [r["topic"] for r in review_details if "low_confidence" in r.get("reason_codes", [])][:2]
    }

    return {
        "summary_stats": summary,
        "decision_distribution": decision_distribution,
        "keep_analysis": keep_analysis,
        "merge_analysis": merge_analysis,
        "review_reasons": dict(review_reasons_dist),
        "review_details": review_details,
        "content_type_reclassification": reclassifications,
        "confidence_distribution": confidence_distribution,
        "confidence_by_decision": confidence_by_decision,
        "low_confidence_topics": low_confidence_topics,
        "similarity_group_distribution": group_sizes,
        "multi_topic_groups": multi_topic_groups,
        "anomalies": dict(anomalies),
        "representative_cases": rep_cases
    }

def generate_markdown(data, output_path):
    s = data["summary_stats"]
    lines = [
        "# Topic Validation V1.2.1 Report\n",
        "## 1. 전체 결과\n",
        f"- 입력 후보: {s.get('input_count', 0)}",
        f"- KEEP: {s.get('keep_count', 0)}",
        f"- MERGE: {s.get('merge_count', 0)}",
        f"- REVIEW: {s.get('review_count', 0)}",
        f"- REJECT: {s.get('reject_count', 0)}",
        f"- Similarity Group: {s.get('similarity_group_count', 0)}\n",
        "## 2. 주요 관찰\n"
    ]

    lines.append(f"- KEEP 판정 비율은 {data['decision_distribution']['keep']['percentage']}% 이며, 리뷰 대상은 {data['decision_distribution']['review']['percentage']}%를 차지함.")
    lines.append(f"- 유사성 그룹은 총 {s.get('similarity_group_count', 0)}개 형성되었으며, 그 중 단일 후보 그룹이 {data['similarity_group_distribution']['single_topic_groups']}개로 대다수를 이룸.")
    lines.append(f"- Confidence 수준은 High가 {data['confidence_distribution'].get('high', {}).get('count', 0)}건 관찰됨.\n")

    lines.append("## 3. Confidence × Decision 교차 통계\n")
    lines.append("| Confidence | KEEP | MERGE | REVIEW | REJECT |")
    lines.append("|---|---:|---:|---:|---:|")
    cbd = data["confidence_by_decision"]
    lines.append(f"| High | {cbd['high']['keep']} | {cbd['high']['merge']} | {cbd['high']['review']} | {cbd['high']['reject']} |")
    lines.append(f"| Medium | {cbd['medium']['keep']} | {cbd['medium']['merge']} | {cbd['medium']['review']} | {cbd['medium']['reject']} |")
    lines.append(f"| Low | {cbd['low']['keep']} | {cbd['low']['merge']} | {cbd['low']['review']} | {cbd['low']['reject']} |\n")

    lines.append("## 4. REVIEW 주요 원인\n")
    lines.append("| Reason | Count |")
    lines.append("|---|---:|")
    for reason, count in data["review_reasons"].items():
        lines.append(f"| {reason} | {count} |")

    lines.append("\n## 5. 자동 재분류 사례\n")
    for reclass in data["content_type_reclassification"]:
        lines.append(f"- **{reclass['topic']}**")
        lines.append(f"  - 기존: {reclass['original']}")
        lines.append(f"  - 제안: {reclass['suggested']}")
        lines.append(f"  - 결정: {reclass['decision']}\n")
    if not data["content_type_reclassification"]:
        lines.append("- 자동 재분류 사례 없음")

    lines.append("\n## 6. 이상 패턴\n")
    for pattern, items in data["anomalies"].items():
        lines.append(f"- {pattern}: {len(items)}건")

    lines.append("\n## 7. 대표 사례\n")
    lines.append("### KEEP")
    lines.append(f"- High Score: {', '.join(data['representative_cases']['keep_high_score'])}")
    lines.append(f"- Low Score: {', '.join(data['representative_cases']['keep_low_score'])}")
    lines.append("\n### MERGE")
    lines.append(f"- {', '.join(data['representative_cases']['merge_groups'])}")
    lines.append("\n### REVIEW")

    lines.append("#### Existing Content Overlap")
    for r in data['representative_cases']['review_existing_overlap']:
        lines.append(f"- {r}")
        # Note: in a fully robust system we'd pull original details from `review_details` but for markdown list this is sufficient.

    lines.append("\n#### Content Type Reclassification")
    for r in data['representative_cases']['review_content_reclass']:
        lines.append(f"- {r}")

    lines.append("\n## 8. 다음 검토 대상\n")
    lines.append("- REVIEW로 분류된 항목 중 기존 게시물 원문 대조가 필요한 항목들의 수동 검토 필요.")
    lines.append("- 모호한 유사도 그룹(generic_similarity_group)의 분류 세분화 고려.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    topics_path = "topic_research/validated_topics.json"
    summary_path = "topic_research/validation_summary.json"

    topics = load_json(topics_path)
    summary = load_json(summary_path)

    if not topics or not summary:
        print("Data files not found. Run validation agent first.")
        return

    report_data = generate_report_data(topics, summary)

    # Filter out merge_child pseudo-topics from standard topics total check
    # to align with summary expectations for KEEP/MERGE/REVIEW/REJECT

    out_json = "topic_research/validation_report.json"
    out_md = "topic_research/validation_report.md"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    generate_markdown(report_data, out_md)

    print("=== Topic Validation V1.2.1 ===\n")
    print(f"Input: {summary.get('input_count', 0)}\n")
    print(f"KEEP: {summary.get('keep_count', 0)}")
    print(f"MERGE: {summary.get('merge_count', 0)}")
    print(f"REVIEW: {summary.get('review_count', 0)}")
    print(f"REJECT: {summary.get('reject_count', 0)}\n")
    print(f"Similarity Groups: {summary.get('similarity_group_count', 0)}\n")

    print("=== REVIEW Reasons ===\n")
    for reason, count in report_data["review_reasons"].items():
        print(f"{reason}: {count}")

    print("\n=== Confidence ===\n")
    print(f"HIGH: {report_data['confidence_distribution'].get('high', {}).get('count', 0)}")
    print(f"MEDIUM: {report_data['confidence_distribution'].get('medium', {}).get('count', 0)}")
    print(f"LOW: {report_data['confidence_distribution'].get('low', {}).get('count', 0)}\n")

    print("=== Anomalies ===\n")
    # Output 0 if an anomaly is missing so the prompt format is fully respected
    anomaly_keys = [
        "high_score_merge", "low_confidence_keep", "high_confidence_review",
        "low_confidence_reject", "self_reference_in_merge", "generic_similarity_group"
    ]
    for k in anomaly_keys:
        print(f"{k}: {len(report_data['anomalies'].get(k, []))}")

    print("\n=== Output ===\n")
    print("topic_research/validated_topics.json")
    print("topic_research/validation_summary.json")
    print("topic_research/validation_report.json")
    print("topic_research/validation_report.md")

if __name__ == "__main__":
    main()
