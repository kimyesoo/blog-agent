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
            origin = p.get("problem_origin", "")
            conf = p.get("evidence_confidence", "low")

            # Identify core canonical concept for duplication check
            core_concept = p["subcategory"] + "_" + p.get("problem_type", "")

            # Base filters
            if p["practical_value"] < 45 or origin == "taxonomy_fallback" or p.get("problem_type") == "theoretical":
                p["problem_decision"] = "reject"
                p["decision_reason"] = "지나치게 학술적이거나 실무 문제성이 부족함."
            elif origin == "ai_inferred":
                # Crucial Fix: Prevent ai_inferred from automatically becoming keep
                p["problem_decision"] = "needs_review"
                p["decision_reason"] = "AI 추론 문제이므로 실제 현장 사례 확인 요망."
                seen_core_concepts[core_concept] = len(validated)
            elif core_concept in seen_core_concepts:
                # Duplication Check
                existing_idx = seen_core_concepts[core_concept]
                existing_p = validated[existing_idx]

                # Semantic similarity check (Mocking AI check for similar nuances)
                if ("운반거리" in title and "운반거리" in existing_p["problem"]) or \
                   ("암반" in title and "암반" in existing_p["problem"]):
                    if title != existing_p["problem"]:
                        # Topic 단계에서 다르게 파생 가능하므로 무조건 merge하지 않고 needs_review
                        p["problem_decision"] = "needs_review"
                        p["decision_reason"] = "유사한 현장 상황이나 세부 맥락 검토 요망 (Topic 다양성 확보)"
                    else:
                        p["problem_decision"] = "merge"
                        p["decision_reason"] = "기존 문제와 동일한 현장 상황 (중복)"
                else:
                    p["problem_decision"] = "merge"
                    p["decision_reason"] = "기존 문제와 유사한 현장 상황 (중복)"
            else:
                # Decision logic for source_derived
                if p["practical_value"] >= 60:
                    p["problem_decision"] = "keep"
                    p["decision_reason"] = "실무적 문제 해결 가치가 높고 명확한 현장 상황임."
                    seen_core_concepts[core_concept] = len(validated)
                elif p["practical_value"] >= 50 and conf == "high":
                    # Crucial Fix: Prevent over-penalizing high confidence source derived problems
                    p["problem_decision"] = "keep"
                    p["decision_reason"] = "점수가 다소 낮으나 명확한 출처와 근거를 가진 현장 문제임."
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
            print(f"- [{v['problem_decision'].upper()}] {v['problem']} (ORIGIN: {v['problem_origin']}, CONF: {v['evidence_confidence']}, PV: {v['practical_value']})")

if __name__ == "__main__":
    agent = ProblemValidationAgent()
    agent.run()
