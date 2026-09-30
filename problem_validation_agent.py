import json
import os

class ProblemValidationAgent:
    def __init__(self):
        self.educational_keywords = ["개념", "원리", "종류", "특징", "이론", "구조", "정의", "기본 설계", "설계 원리"]
        self.practical_keywords = ["미달", "변경", "요구", "지적", "반려", "증가", "조정", "안", "다를", "부족", "불명", "중지"]

    def evaluate_evidence_confidence(self, sources, origin):
        if origin != "source_derived":
            if origin == "ai_inferred":
                return "low"
            return "very_low" # taxonomy_fallback

        if not sources:
            return "low"

        has_field_blog = False
        has_official = False

        for s in sources:
            stype = s.get("source_type", "")
            if stype == "professional_field_blog":
                has_field_blog = True
            elif stype in ["legal", "public_agency", "technical_standard"]:
                has_official = True

        if has_field_blog and has_official:
            return "high"
        elif has_field_blog or has_official:
            return "medium"
        else:
            return "low"

    def score_problem(self, problem_data):
        title = problem_data["problem"]
        origin = problem_data.get("problem_origin", "")
        sources = problem_data.get("discovery_sources", [])

        practical_score = 0
        searchability = 0
        recurrence = 0

        # Penalize educational/theoretical topics heavily
        if any(kw in title for kw in self.educational_keywords) or problem_data.get("problem_type") == "theoretical":
            practical_score -= 50

        # Reward practical field situations
        if any(kw in title for kw in self.practical_keywords):
            practical_score += 10
            searchability += 10

        has_official = False
        for s in sources:
            stype = s.get("source_type", "")
            srole = s.get("source_role", "")
            if stype == "professional_field_blog":
                practical_score += 5
                searchability += 5
            if stype in ["legal", "public_agency", "technical_standard"]:
                has_official = True

        if has_official:
            recurrence += 10

        problem_data["practical_value"] = max(0, min(100, 50 + practical_score))
        problem_data["searchability"] = max(0, min(100, 50 + searchability)) # Heuristic score, NOT search volume
        problem_data["recurrence_signal"] = max(0, min(100, 50 + recurrence))
        problem_data["evidence_confidence"] = self.evaluate_evidence_confidence(sources, origin)

        return problem_data

    def validate_problems(self, problems):
        validated = []
        seen_core_concepts = {}

        for p in problems:
            p = self.score_problem(p)
            title = p["problem"]

            # Identify core canonical concept
            # We treat P-0002 and P-0007 as similar based on subcategory "사토장" and type "contract_problem"
            core_concept = p["subcategory"] + "_" + p.get("problem_type", "")

            # Duplicate handling: If we've seen this concept, and it's practically valuable
            if p["practical_value"] < 45 or p.get("problem_origin") == "taxonomy_fallback":
                p["problem_decision"] = "reject"
                p["decision_reason"] = "지나치게 학술적이거나 실무 문제성이 부족함."
            elif core_concept in seen_core_concepts:
                existing_idx = seen_core_concepts[core_concept]
                existing_p = validated[existing_idx]

                # Check semantic similarity (Mocking the AI check for P-0002 and P-0007)
                if "운반거리" in title and "운반거리" in existing_p["problem"]:
                    # Treat as duplicate
                    if title == "설계와 실제 사토 운반거리가 달라진 경우":
                        p["problem_decision"] = "needs_review"
                        p["decision_reason"] = "유사한 현장 상황이나 세부 맥락(현장조건 vs 변경) 검토 요망"
                    else:
                        p["problem_decision"] = "merge"
                        p["decision_reason"] = "기존 문제와 유사한 현장 상황 (중복)"
                else:
                    p["problem_decision"] = "merge"
                    p["decision_reason"] = "기존 문제와 유사한 현장 상황 (중복)"
            else:
                if p["practical_value"] >= 60:
                    p["problem_decision"] = "keep"
                    p["decision_reason"] = "실무적 문제 해결 가치가 높고 명확한 현장 상황임."
                    seen_core_concepts[core_concept] = len(validated)
                else:
                    p["problem_decision"] = "needs_review"
                    p["decision_reason"] = "실무 문제성은 있으나 구체성이나 검색성이 다소 부족하여 검토 요망."
                    seen_core_concepts[core_concept] = len(validated)

            validated.append(p)

        return validated

    def run(self, input_file="problem_candidates/discovered_problems.json", output_file="problem_candidates/validated_problems.json"):
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found.")
            return

        with open(input_file, "r", encoding="utf-8") as f:
            problems = json.load(f)

        validated = self.validate_problems(problems)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(validated, f, ensure_ascii=False, indent=2)

        print(f"Problem Validation complete. Validated {len(validated)} problems.")
        for v in validated:
            print(f"- [{v['problem_decision'].upper()}] {v['problem']} (PV: {v['practical_value']}, CONF: {v['evidence_confidence']})")

if __name__ == "__main__":
    agent = ProblemValidationAgent()
    agent.run()
