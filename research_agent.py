import json
import os

def main():
    # Read topic candidates
    candidates_path = os.path.join("topic_candidates", "candidates.json")
    if not os.path.exists(candidates_path):
        print(f"File not found: {candidates_path}")
        return

    with open(candidates_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    if not candidates:
        print("No candidates found.")
        return

    # Select the first candidate for research
    selected_topic = candidates[0]
    print(f"Selected topic for research: {selected_topic}")

    # Generate research content
    research_content = f"""# {selected_topic}

## 1. 시험 목적
(이곳에 시험 목적 내용을 작성합니다.)

## 2. 시험 원리
(이곳에 시험 원리 내용을 작성합니다.)

## 3. 시험 장비
(이곳에 시험 장비 내용을 작성합니다.)

## 4. 시험 절차
(이곳에 시험 절차 내용을 작성합니다.)

## 5. 계산 방법
(이곳에 계산 방법 내용을 작성합니다.)

## 6. 결과 해석
(이곳에 결과 해석 내용을 작성합니다.)

## 7. 관련 기준
(이곳에 관련 기준 내용을 작성합니다.)

## 8. 현장 활용
(이곳에 현장 활용 내용을 작성합니다.)
"""

    # Save to research/<topic>.md
    research_dir = "research"
    os.makedirs(research_dir, exist_ok=True)

    # Clean the topic string to make it a safe filename if necessary
    # In this case we just append .md
    safe_topic_name = selected_topic.replace(" ", "_")
    output_path = os.path.join(research_dir, f"{safe_topic_name}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(research_content)

    print(f"Research output generated at: {output_path}")

if __name__ == "__main__":
    main()
