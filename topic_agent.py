import json
import os

def main():
    # Read posts
    posts_path = os.path.join("content_db", "posts.json")
    if not os.path.exists(posts_path):
        print(f"File not found: {posts_path}")
        return

    with open(posts_path, "r", encoding="utf-8") as f:
        posts = json.load(f)

    # Basic logic for topic suggestion based on existing topics
    # We output a list of related topics.
    candidates = [
        "흙의 압밀 시험방법",
        "일축압축 시험방법",
        "투수 시험방법",
        "다짐 시험방법",
        "직접전단 시험방법"
    ]

    # Save candidates
    candidates_dir = "topic_candidates"
    os.makedirs(candidates_dir, exist_ok=True)
    candidates_path = os.path.join(candidates_dir, "candidates.json")

    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"Topic candidates generated at {candidates_path}")

if __name__ == "__main__":
    main()
