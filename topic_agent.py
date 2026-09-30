import json
import os

TOPIC_MAP = {
    "체분석 시험방법": [
        "비중계 시험방법",
        "조립률 계산법",
        "체가름 시험 결과 그래프 해석"
    ],
    "들밀도 시험": [
        "모래치환법의 주의사항",
        "현장 다짐도 평가 방법",
        "고무풍선법 밀도 시험"
    ],
    "액성한계 시험방법": [
        "소성지수(PI)의 의미",
        "Casagrande 방법과 Fall Cone 방법 비교",
        "통일분류법(USCS)의 액성한계 활용"
    ],
    "모래의 비중 시험방법": [
        "굵은 골재의 비중 시험",
        "비중 병 보정 방법",
        "흙의 공극비 계산"
    ],
    "소성한계 시험방법": [
        "수축한계 시험방법",
        "점토 광물이 소성한계에 미치는 영향",
        "터터버그 한계 종합 분석"
    ]
}

def main():
    posts_path = os.path.join("content_db", "posts.json")
    if not os.path.exists(posts_path):
        print(f"File not found: {posts_path}")
        return

    with open(posts_path, "r", encoding="utf-8") as f:
        posts = json.load(f)

    # Extract existing post titles to exclude them
    existing_titles = {post["title"] for post in posts if "title" in post}

    candidates_dict = {}

    for post in posts:
        title = post.get("title")
        views = post.get("views", 0)

        if title in TOPIC_MAP:
            for related_topic in TOPIC_MAP[title]:
                if related_topic in existing_titles:
                    continue

                if related_topic not in candidates_dict:
                    candidates_dict[related_topic] = {
                        "topic": related_topic,
                        "score": 0,
                        "reason": f"기존 인기글 '{title}' 등과 연관성이 높아 조회수가 기대됩니다.",
                        "related_posts": []
                    }

                candidates_dict[related_topic]["score"] += views
                if title not in candidates_dict[related_topic]["related_posts"]:
                    candidates_dict[related_topic]["related_posts"].append(title)

    candidates = list(candidates_dict.values())

    # Sort candidates by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)

    candidates_dir = "topic_candidates"
    os.makedirs(candidates_dir, exist_ok=True)
    candidates_path = os.path.join(candidates_dir, "candidates.json")

    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"Topic candidates (V2) generated at {candidates_path}")

if __name__ == "__main__":
    main()
