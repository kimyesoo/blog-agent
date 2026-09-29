import json
import os
import argparse

class TopicPrioritizationAgent:
    def __init__(self,
                 validated_topics_file='topic_research/validated_topics.json',
                 search_results_file='topic_search/search_results.json',
                 output_json='topic_priority/topic_priority.json',
                 output_md='topic_priority/topic_priority_report.md'):
        self.validated_topics_file = validated_topics_file
        self.search_results_file = search_results_file
        self.output_json = output_json
        self.output_md = output_md

    def calculate_practical_value_score(self, topic_title):
        high_value_keywords = [
            "계산 방법", "결과 해석", "현장 적용", "평가 방법",
            "판독 방법", "부적합", "원인", "대책", "실무"
        ]
        low_value_keywords = ["이란", "개요", "정의", "뜻"]

        score = 50  # Base score

        for kw in high_value_keywords:
            if kw in topic_title:
                score += 30
                break # Apply once

        for kw in low_value_keywords:
            if kw in topic_title:
                score -= 30
                break # Apply once

        return max(0, min(100, score))

    def calculate_content_gap_score(self, search_result):
        content_gap = search_result.get("content_gap", [])
        top_content = search_result.get("top_content", [])

        observed_topics_set = set()
        for content in top_content:
            topics = content.get("observed_topics", [])
            for t in topics:
                observed_topics_set.add(t)

        gap_count = len(content_gap)
        observed_count = len(observed_topics_set)

        if gap_count >= 3:
            score = 100
        elif gap_count == 2:
            score = 75
        elif gap_count == 1:
            score = 50
        else:
            score = 10

        # Boost slightly if very few topics are observed
        if observed_count <= 2 and gap_count > 0:
            score = min(100, score + 20)

        return score

    def calculate_intent_clarity_score(self, search_result):
        intent_analysis = search_result.get("intent_analysis") or {}
        is_match = intent_analysis.get("match", False)

        # We rely on intent_analysis matching as dominant intent
        if is_match:
            return 100
        else:
            return 40

    def calculate_competition_score(self, search_result):
        serp = search_result.get("serp", {})
        organic_count = serp.get("organic_result_count", 0)
        unique_domains = serp.get("unique_domains", 0)

        # Lower competition -> Higher score
        # Since organic_count is usually capped per request (e.g. 5 or so if mock, but real SERP has more),
        # If unique_domains is high, competition is high -> lower score.

        if unique_domains == 0:
            return 0 # No data

        if unique_domains >= 10:
            score = 20
        elif unique_domains >= 5:
            score = 50
        elif unique_domains >= 2:
            score = 80
        else:
            score = 100

        return score

    def calculate_penalty(self, search_result, validated_topic):
        # existing_post exists if related_existing_posts has items or search_result has existing_post
        related_posts = validated_topic.get("related_existing_posts", [])
        if related_posts or search_result.get("existing_post"):
            return 30
        return 0

    def generate_reasons(self, scores):
        reasons = []
        if scores["practical_value_score"] >= 80:
            reasons.append("실무 활용도가 높음")
        elif scores["practical_value_score"] <= 40:
            reasons.append("단순 정보성 주제")

        if scores["content_gap_score"] >= 70:
            reasons.append("SERP 공백 존재")

        if scores["intent_clarity_score"] >= 80:
            reasons.append("검색 의도 명확")
        else:
            reasons.append("검색 의도 불분명/경쟁")

        if scores["competition_score"] >= 80:
            reasons.append("경쟁 강도 낮음 (기회)")
        elif scores["competition_score"] <= 40:
            reasons.append("경쟁 강도 높음")

        if scores["existing_content_penalty"] > 0:
            reasons.append("유사 기존 콘텐츠 존재 (페널티 적용)")

        return reasons

    def run(self):
        print("Blog Agent - Topic Prioritization Agent V1\n")

        if not os.path.exists(self.validated_topics_file) or not os.path.exists(self.search_results_file):
            print("Error: Input files not found.")
            return

        with open(self.validated_topics_file, 'r') as f:
            validated_topics = {t["topic"]: t for t in json.load(f)}

        with open(self.search_results_file, 'r') as f:
            search_results = json.load(f)

        priorities = []

        for sr in search_results:
            topic_title = sr.get("topic")
            vt = validated_topics.get(topic_title, {})

            # If search failed, we might still want to score practical value, but everything else is 0.
            is_failed = sr.get("research_status") == "failed"

            pv_score = self.calculate_practical_value_score(topic_title)
            cg_score = self.calculate_content_gap_score(sr) if not is_failed else 0
            ic_score = self.calculate_intent_clarity_score(sr) if not is_failed else 0
            cp_score = self.calculate_competition_score(sr) if not is_failed else 0
            penalty = self.calculate_penalty(sr, vt)

            final_score = (pv_score * 0.40) + (cg_score * 0.25) + (ic_score * 0.15) + (cp_score * 0.20) - penalty
            final_score = max(0, round(final_score))

            if final_score >= 90:
                classification = "Critical"
            elif final_score >= 80:
                classification = "High"
            elif final_score >= 60:
                classification = "Medium"
            elif final_score >= 40:
                classification = "Low"
            else:
                classification = "Ignore"

            scores = {
                "practical_value_score": pv_score,
                "content_gap_score": cg_score,
                "intent_clarity_score": ic_score,
                "competition_score": cp_score,
                "existing_content_penalty": penalty
            }

            reasons = self.generate_reasons(scores)

            priorities.append({
                "topic": topic_title,
                "priority_score": final_score,
                "classification": classification,
                "score_breakdown": scores,
                "reasons": reasons
            })

        # Sort descending by priority_score
        priorities.sort(key=lambda x: x["priority_score"], reverse=True)

        # Save JSON
        with open(self.output_json, 'w') as f:
            json.dump(priorities, f, ensure_ascii=False, indent=2)

        # Summary metrics
        total = len(priorities)
        critical = sum(1 for p in priorities if p["classification"] == "Critical")
        high = sum(1 for p in priorities if p["classification"] == "High")
        medium = sum(1 for p in priorities if p["classification"] == "Medium")
        low = sum(1 for p in priorities if p["classification"] == "Low")
        ignore = sum(1 for p in priorities if p["classification"] == "Ignore")

        # Save Markdown
        with open(self.output_md, 'w') as f:
            f.write("# Topic Priority Report\n\n")

            f.write("## Summary\n")
            f.write(f"- **Total topics:** {total}\n")
            f.write(f"- **Critical:** {critical}\n")
            f.write(f"- **High:** {high}\n")
            f.write(f"- **Medium:** {medium}\n")
            f.write(f"- **Low:** {low}\n")
            f.write(f"- **Ignore:** {ignore}\n\n")

            f.write("## Top 20 Recommendations\n")
            top_20 = priorities[:20]
            for idx, item in enumerate(top_20):
                f.write(f"### Rank {idx + 1}: {item['topic']}\n")
                f.write(f"- **Priority Score:** {item['priority_score']}\n")
                f.write(f"- **Classification:** {item['classification']}\n")
                f.write(f"- **Reasons:**\n")
                for r in item["reasons"]:
                    f.write(f"  - {r}\n")
                f.write("\n")

            f.write("## All Priorities\n")
            f.write("| Rank | Topic | Score | Classification | Practical | Gap | Intent | Comp | Penalty |\n")
            f.write("|---|---|---|---|---|---|---|---|---|\n")
            for idx, item in enumerate(priorities):
                s = item["score_breakdown"]
                f.write(f"| {idx+1} | {item['topic']} | **{item['priority_score']}** | {item['classification']} | {s['practical_value_score']} | {s['content_gap_score']} | {s['intent_clarity_score']} | {s['competition_score']} | {s['existing_content_penalty']} |\n")

        print(f"Prioritized {total} topics.")
        print(f"Outputs saved to {self.output_json} and {self.output_md}")

if __name__ == '__main__':
    agent = TopicPrioritizationAgent()
    agent.run()
