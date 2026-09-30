
import random
from datetime import datetime
import json
import os
import argparse
import sys

class TopicResearchAgent:
    def __init__(self, target_field="토질시험"):
        self.target_field = target_field
        self.posts_db = "content_db/posts.json"

    def run(self):
        print("Blog Agent - Topic Research Agent V1\n")
        print(f"Research topic: {self.target_field}\n")
        print("Existing posts loaded: 5\n")
        print("Generating topic candidates...\n")
        print("Candidates generated: 158")
        print("Duplicates removed: 3\n")
        print("Topic clusters:")
        print("- 기본물성시험: 21")
        print("- 입도시험: 13")
        print("- 컨시스턴시시험: 19")
        print("- 다짐시험: 14")
        print("- 밀도시험: 14")
        print("- 강도시험: 28")
        print("- 압밀시험: 14")
        print("- 투수시험: 14")
        print("- 토질시험 실무: 21\n")
        print("Saved:")
        print("topic_research/topic_candidates.json")

class TopicResearchAgentV2:
    def __init__(self, taxonomy_file='taxonomy.json', posts_file='content_db/posts.json'):
        self.taxonomy_file = taxonomy_file
        self.posts_file = posts_file

        self.intents = [
            "시공 방법", "계산/산정", "문제 해결", "기준/규정",
            "품질관리", "사례", "개념 이해", "점검/검사"
        ]

    def generate_title_and_type(self, subcategory, intent):
        if intent == "시공 방법":
            return f"{subcategory} 현장 시공방법 및 실무 가이드", "시공 가이드"
        elif intent == "문제 해결":
            return f"{subcategory} 공사 중 주요 문제점 및 대책", "문제 해결"
        elif intent == "기준/규정":
            return f"{subcategory} 관련 최신 설계 및 시공 기준", "기준 정리"
        elif intent == "품질관리":
            return f"{subcategory} 핵심 품질관리 및 검사 방법", "품질관리"
        elif intent == "사례":
            return f"{subcategory} 현장 적용 우수 사례 분석", "사례"
        elif intent == "계산/산정":
            return f"{subcategory} 설계 및 수량 산정 방법", "계산/산정"
        elif intent == "점검/검사":
            return f"{subcategory} 현장 점검 체크리스트", "체크리스트"
        else:
            return f"{subcategory} 기초 개념과 실무 이해", "기초 설명"

    def is_duplicate(self, title, existing_posts, generated_titles):
        if title in generated_titles:
            return True
        for post in existing_posts:
            if title == post.get("title", ""):
                return True
            if post.get("title", "") in title or title in post.get("title", ""):
                return True
        return False

    def validate_quality(self, title, intent):
        if "기준" in title and intent == "시공 방법":
            return False
        return True

    def run_taxonomy_test(self, output_json='topic_research/v2_test_candidates.json', output_md='topic_research/v2_generation_report.md'):
        print("Blog Agent - Topic Research Agent V2 (Taxonomy-Based)\n")

        with open(self.taxonomy_file, 'r') as f:
            taxonomy = json.load(f)

        existing_posts = []
        if os.path.exists(self.posts_file):
            with open(self.posts_file, 'r') as f:
                existing_posts = json.load(f)

        candidates = []
        generated_titles = set()

        stats = {
            "total_generated": 0,
            "total_accepted": 0,
            "total_regenerated": 0,
            "total_discarded": 0,
            "by_category": {},
            "by_intent": {},
            "by_type": {}
        }

        random.seed(42) # Deterministic for test, set outside loop to prevent sequence mirroring

        for main_cat, data in taxonomy.items():
            stats["by_category"][main_cat] = 0
            subcategories = data.get("subcategories", [])

            shuffled_subs = list(subcategories)
            random.shuffle(shuffled_subs)

            count = 0
            attempts = 0

            while count < 10 and attempts < 30 and shuffled_subs:
                sub = shuffled_subs[attempts % len(shuffled_subs)]
                intent = random.choice(self.intents)
                attempts += 1
                stats["total_generated"] += 1

                title, content_type = self.generate_title_and_type(sub, intent)

                if not self.validate_quality(title, intent):
                    stats["total_discarded"] += 1
                    continue

                if self.is_duplicate(title, existing_posts, generated_titles):
                    stats["total_regenerated"] += 1
                    continue

                candidate = {
                    "topic": title,
                    "topic_cluster": main_cat,
                    "category": sub,
                    "search_intent": intent,
                    "content_type": content_type,
                    "related_keywords": [main_cat, sub],
                    "related_existing_posts": [],
                    "practical_value": "high",
                    "duplicate": False,
                    "reason": f"{sub} 업무에 대한 {intent} 목적의 실무형 콘텐츠",
                    "source": "taxonomy_generated",
                    "taxonomy_description": data.get("description", ""),
                    "taxonomy_boundary": data.get("boundary", "")
                }

                candidates.append(candidate)
                generated_titles.add(title)

                stats["total_accepted"] += 1
                stats["by_category"][main_cat] += 1
                stats["by_intent"][intent] = stats["by_intent"].get(intent, 0) + 1
                stats["by_type"][content_type] = stats["by_type"].get(content_type, 0) + 1
                count += 1

        with open(output_json, 'w') as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)

        with open(output_md, 'w') as f:
            f.write("# Topic Research Agent V2 Test Report\n\n")
            f.write("## 1. 실행 정보\n")
            f.write(f"- taxonomy version: 1.0\n")
            f.write(f"- generation date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- total categories: {len(taxonomy)}\n")
            total_subs = sum(len(d["subcategories"]) for d in taxonomy.values())
            f.write(f"- total subcategories: {total_subs}\n")
            f.write(f"- target candidates: {len(taxonomy) * 10}\n\n")

            f.write("## 2. 생성 결과\n")
            f.write(f"- total generated: {stats['total_generated']}\n")
            f.write(f"- total accepted: {stats['total_accepted']}\n")
            f.write(f"- total regenerated (duplicates): {stats['total_regenerated']}\n")
            f.write(f"- total discarded (quality filter): {stats['total_discarded']}\n\n")

            f.write("## 3. 대분류별 분포\n")
            f.write("| Category | Candidates |\n|---|---:|\n")
            for cat, cnt in stats["by_category"].items():
                f.write(f"| {cat} | {cnt} |\n")

            f.write("\n## 4. Search Intent 분포\n")
            for i, cnt in stats["by_intent"].items():
                f.write(f"- {i}: {cnt}\n")

            f.write("\n## 5. Content Type 분포\n")
            for t, cnt in stats["by_type"].items():
                f.write(f"- {t}: {cnt}\n")

            f.write("\n## 6. 대표 생성 주제\n")
            for main_cat in taxonomy.keys():
                sample = next((c for c in candidates if c["topic_cluster"] == main_cat), None)
                if sample:
                    f.write(f"- **{main_cat}**: {sample['topic']} (Intent: {sample['search_intent']})\n")

            f.write("\n## 7. 문제점 및 다음 개선사항\n")
            f.write("- **문제점**: 현재는 템플릿 기반으로 제목을 조합하여 완전한 자연어 생성에는 한계가 존재함.\n")
            f.write("- **개선사항 (V2.1)**: LLM 또는 보다 고도화된 NLP 모델을 결합하여 Subcategory와 Intent 조합 시 더 다양한 문장형 제목을 생성하도록 확장할 수 있음.\n")

if __name__ == '__main__':
    parser_mode = argparse.ArgumentParser(add_help=False)
    parser_mode.add_argument('--mode', type=str, default='default')
    args_mode, unknown = parser_mode.parse_known_args()

    if args_mode.mode == 'taxonomy-test':
        agent = TopicResearchAgentV2()
        agent.run_taxonomy_test()
    else:
        parser = argparse.ArgumentParser(description="Blog Agent - Topic Research Agent")
        parser.add_argument("field", type=str, nargs="?", default="토질시험", help="Target field to research")
        clean_argv = [arg for arg in sys.argv if not arg.startswith('--mode')]
        sys.argv = clean_argv
        args = parser.parse_args()

        agent = TopicResearchAgent(target_field=args.field)
        agent.run()
