
import json
import os
import argparse

class TopicOpportunityScoringAgent:
    def __init__(self, input_file='topic_search/search_results.json', output_json='topic_search/opportunity_scores.json', output_md='topic_search/opportunity_report.md'):
        self.input_file = input_file
        self.output_json = output_json
        self.output_md = output_md

    def calculate_scores(self, result):
        top_content = result.get("top_content", [])
        serp = result.get("serp", {})

        # 1. Domain Types count
        blog_count = 0
        government_count = 0
        academic_count = 0
        video_count = 0

        for content in top_content:
            ctype = content.get("content_type", "")
            if ctype in ["blog", "tistory"]:
                blog_count += 1
            elif ctype == "video":
                video_count += 1
            elif ctype in ["government", "public_technical"]:
                government_count += 1
            elif ctype == "academic":
                academic_count += 1

        authority_domain_count = government_count + academic_count

        # 2. Saturation Score
        # Use organic_result_count from the entire SERP, not just top_content limit
        organic_count = serp.get("organic_result_count", 0)

        if organic_count >= 50:
            saturation_score = 100
        elif organic_count >= 20:
            saturation_score = 75
        elif organic_count >= 5:
            saturation_score = 40
        elif organic_count > 0:
            saturation_score = 10
        else:
            saturation_score = 0

        low_saturation_score = 100 - saturation_score

        # 3. Content Gap Score
        # Utilize both content_gap and observed_topics dynamically.
        # Find all unique observed topics across top_content
        observed_topics_set = set()
        for content in top_content:
            topics = content.get("observed_topics", [])
            for t in topics:
                observed_topics_set.add(t)

        observed_topic_count = len(observed_topics_set)

        content_gap = result.get("content_gap", [])
        gap_count = len(content_gap)

        # The logic: more gaps = higher opportunity. Fewer observed topics = higher opportunity.
        # Max score is heavily driven by gaps.
        if gap_count >= 3:
            content_gap_score = 100
        elif gap_count == 2:
            content_gap_score = 70
        elif gap_count == 1:
            content_gap_score = 40
        else:
            content_gap_score = 0

        # Slightly boost score if observed topics are very sparse
        if observed_topic_count <= 2 and gap_count > 0:
            content_gap_score = min(content_gap_score + 20, 100)

        # 4. Intent Clarity Score
        # Do not use content_type for intent. Use intent_analysis / observed_search_intent
        intent_analysis = result.get("intent_analysis") or {}

        # If match is true and dominant intent is clear, clarity is high.
        # If there's mismatch or unknown, it means competing or unclear intents.
        is_match = intent_analysis.get("match", False)

        if is_match:
            intent_clarity_score = 100 # HIGH: single dominant intent aligns
        else:
            intent_clarity_score = 40  # LOW/MEDIUM: competing intents or mismatch

        # Fallback for empty results
        if result.get("research_status") == "failed" or organic_count == 0:
            intent_clarity_score = 0
            content_gap_score = 0
            saturation_score = 0
            low_saturation_score = 0

        # 5. Final Opportunity Score
        opportunity_score = (content_gap_score * 0.4) + (intent_clarity_score * 0.2) + (low_saturation_score * 0.4)
        opportunity_score = round(opportunity_score)

        # 6. Classification
        if opportunity_score >= 80:
            classification = "excellent"
        elif opportunity_score >= 60:
            classification = "good"
        elif opportunity_score >= 40:
            classification = "average"
        else:
            classification = "poor"

        # Reason generation
        reasoning = []
        reasoning.append(f"Content Gap identified {gap_count} missing subtopics and {observed_topic_count} observed topics (Score: {content_gap_score}).")
        reasoning.append(f"Intent Clarity is based on dominant intent matching (Score: {intent_clarity_score}).")
        reasoning.append(f"Saturation is based on {organic_count} total organic results (Score: {saturation_score}).")
        reasoning.append(f"Domain Authority: Blogs({blog_count}), Government({government_count}), Academic({academic_count}), Video({video_count}).")

        return {
            "topic": result.get("topic"),
            "opportunity_score": opportunity_score,
            "classification": classification,
            "content_gap_score": content_gap_score,
            "intent_clarity_score": intent_clarity_score,
            "saturation_score": saturation_score,
            "domain_metrics": {
                "authority_domain_count": authority_domain_count,
                "blog_count": blog_count,
                "government_count": government_count,
                "academic_count": academic_count,
                "video_count": video_count
            },
            "reasoning": reasoning
        }

    def run(self):
        print("Blog Agent - Topic Opportunity Scoring Agent V1\n")

        if not os.path.exists(self.input_file):
            print(f"Error: Input file {self.input_file} not found.")
            return

        with open(self.input_file, 'r') as f:
            search_results = json.load(f)

        scores = []
        for res in search_results:
            score_data = self.calculate_scores(res)
            scores.append(score_data)

        # Sort descending by opportunity score
        scores.sort(key=lambda x: x["opportunity_score"], reverse=True)

        # Output JSON
        with open(self.output_json, 'w') as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)

        # Output Markdown
        with open(self.output_md, 'w') as f:
            f.write("# Topic Opportunity Report\n\n")
            f.write("Deterministic scoring based on observable SERP structures.\n\n")
            for idx, item in enumerate(scores):
                f.write(f"### Rank {idx + 1}: {item['topic']}\n")
                f.write(f"- **Opportunity Score:** {item['opportunity_score']}\n")
                f.write(f"- **Classification:** {item['classification'].upper()}\n")
                f.write(f"- **Reasoning:**\n")
                for reason in item['reasoning']:
                    f.write(f"  - {reason}\n")
                f.write("\n")

        print(f"Scored {len(scores)} topics.")
        print(f"Output saved to {self.output_json} and {self.output_md}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default='topic_search/search_results.json', help='Path to search_results.json')
    args = parser.parse_args()

    agent = TopicOpportunityScoringAgent(input_file=args.input)
    agent.run()
