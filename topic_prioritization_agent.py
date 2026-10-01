
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

    def calculate_content_gap_score(self, search_result, validated_topic):
        has_existing = bool(validated_topic.get("related_existing_posts")) or bool(search_result.get("existing_post"))

        # Base score if no existing post is present
        base_score = 0 if has_existing else 60

        content_gap = search_result.get("content_gap", [])
        gap_count = len(content_gap)

        if gap_count >= 3:
            base_score = max(base_score, 100)
        elif gap_count == 2:
            base_score = max(base_score, 80)
        elif gap_count == 1:
            base_score = max(base_score, 70)

        return base_score

    def calculate_intent_clarity_score(self, topic_title, search_result):
        clear_intent_keywords = ["방법", "계산", "공식", "기준", "절차", "해석", "원인", "대책", "비교"]
        base_score = 40

        for kw in clear_intent_keywords:
            if kw in topic_title:
                base_score = 90
                break

        intent_analysis = search_result.get("intent_analysis") or {}
        if intent_analysis.get("match", False):
            base_score = max(base_score, 100)

        return base_score

    def calculate_competition_score(self, search_result):
        top_content = search_result.get("top_content", [])

        if not top_content:
            return 60 # Default moderate opportunity if no SERP data

        competitor_count = 0

        for content in top_content:
            ctype = content.get("content_type", "")
            # Assume blogs, cafes, communities are primary SEO competitors
            if ctype in ["blog", "tistory", "community"]:
                competitor_count += 1

        # Lower SEO blog competition means higher opportunity score
        if competitor_count == 0:
            return 100
        elif competitor_count <= 2:
            return 80
        elif competitor_count <= 4:
            return 50
        else:
            return 20

    def calculate_penalty(self, search_result, validated_topic):
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
            reasons.append("SERP 공백 확인 (기회)")
        elif scores["content_gap_score"] >= 50:
            reasons.append("기존 내부 문서 부재 (기본 점수)")

        if scores["intent_clarity_score"] >= 80:
            reasons.append("검색 의도 명확")
        else:
            reasons.append("검색 의도 불분명/경쟁")

        if scores["competition_score"] >= 80:
            reasons.append("일반 블로그/커뮤니티 경쟁도 낮음")
        elif scores["competition_score"] <= 40:
            reasons.append("일반 블로그/커뮤니티 경쟁도 높음")

        if scores["existing_content_penalty"] > 0:
            reasons.append("유사 기존 콘텐츠 존재 (페널티 적용)")

        return reasons

    def run(self):
        print("Blog Agent - Topic Prioritization Agent V1\n")

        if not os.path.exists(self.validated_topics_file) or not os.path.exists(self.search_results_file):
            print("Error: Input files not found.")
            return

        with open(self.validated_topics_file, 'r', encoding='utf-8') as f:
            validated_topics = {t["topic"]: t for t in json.load(f)}

        with open(self.search_results_file, 'r', encoding='utf-8') as f:
            search_results = json.load(f)

        priorities = []

        for sr in search_results:
            topic_title = sr.get("topic")
            vt = validated_topics.get(topic_title, {})

            pv_score = self.calculate_practical_value_score(topic_title)
            cg_score = self.calculate_content_gap_score(sr, vt)
            ic_score = self.calculate_intent_clarity_score(topic_title, sr)
            cp_score = self.calculate_competition_score(sr)
            penalty = self.calculate_penalty(sr, vt)

            final_score = (pv_score * 0.40) + (cg_score * 0.25) + (ic_score * 0.15) + (cp_score * 0.20) - penalty
            final_score = max(0, round(final_score))

            if final_score >= 80:
                classification = "Critical"
            elif final_score >= 65:
                classification = "High"
            elif final_score >= 50:
                classification = "Medium"
            elif final_score >= 35:
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
        with open(self.output_json, 'w', encoding='utf-8') as f:
            json.dump(priorities, f, ensure_ascii=False, indent=2)

        # Summary metrics
        total = len(priorities)
        critical = sum(1 for p in priorities if p["classification"] == "Critical")
        high = sum(1 for p in priorities if p["classification"] == "High")
        medium = sum(1 for p in priorities if p["classification"] == "Medium")
        low = sum(1 for p in priorities if p["classification"] == "Low")
        ignore = sum(1 for p in priorities if p["classification"] == "Ignore")

        # Save Markdown
        with open(self.output_md, 'w', encoding='utf-8') as f:
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
