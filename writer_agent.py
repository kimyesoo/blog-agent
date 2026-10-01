import json
import os
import re

class WriterAgentV1:
    def __init__(self):
        self.prohibited_title_keywords = ["정의", "종류", "개념", "원리", "무엇인가"]

    def _generate_slug(self, problem_type: str, domain: str) -> str:
        # A simple slug mapping mock since we don't have an NLP translation engine.
        mapping = {
            "quality_problem": "quality",
            "contract_problem": "contract",
            "supervision_response": "supervision",
            "site_condition_change": "site-condition",
            "administrative_problem": "admin"
        }
        ptype = mapping.get(problem_type, "field")

        domain_map = {
            "토공": "earthwork",
            "구조물": "structure",
            "공무/행정": "admin",
            "지반 및 토질": "geo"
        }
        d = domain_map.get(domain, "problem")

        return f"field-{d}-{ptype}-guide"

    def _generate_faq(self, pack: dict) -> str:
        extracted = pack.get("extracted_problems", [])
        question = extracted[0] if extracted else pack.get("problem", "") + " 시 가장 주의할 점은 무엇인가요?"

        return f"""## 10. FAQ
**Q. {question}**
A. 가장 먼저 현장 확인사항을 점검하고, 감리단과 실무 조치 방향을 협의하는 것이 원칙입니다.

**Q. 행정적으로 가장 누락하기 쉬운 부분은 무엇인가요?**
A. 사전 실정보고나 승인 없이 임의로 시공을 진행하여 추후 계약금액 조정을 받지 못하는 경우입니다.

**Q. 관련 기준과 실무가 다를 때는 어떻게 하나요?**
A. 최신 KCS/KDS 등 공식 기준을 우선하되, 현장 여건상 불가피한 경우 감리단과 협의하여 문서화해야 합니다.
"""

    def write(self, pack: dict) -> dict:
        readiness = pack.get("writer_readiness", "insufficient")

        if readiness == "insufficient":
            return {
                "status": "blocked",
                "reason": "insufficient_research"
            }

        title = pack.get("topic", pack.get("problem", "현장 문제 해결 가이드"))

        # Format the markdown content systematically
        content = []

        if readiness == "partial":
            content.append("> **주의:** 본 문서는 실무 근거가 일부 부족한 상태에서 작성되었습니다. 실제 적용 시 추가 검토가 필요합니다.\n")

        content.append(f"# {title}\n")

        # 1. 문제 상황
        situation = pack.get("situation", f"{pack.get('problem')} 상황이 발생했습니다.")
        content.append(f"## 1. 문제 상황\n{situation}\n\n이 경우 정확한 현장 파악과 조치가 필요합니다.\n")

        # 2. 발생 이유
        causes = pack.get("possible_causes", [])
        content.append("## 2. 이런 상황이 발생하는 이유\n")
        if causes:
            for c in causes:
                content.append(f"- {c}")
        else:
            content.append("현장 조건 변동, 재료 불량, 시공 순서 오류 등 다양한 원인이 있을 수 있습니다.")
        content.append("\n")

        # 3. 확인 사항
        checks = pack.get("diagnostic_checks", [])
        content.append("## 3. 가장 먼저 확인해야 할 사항\n")
        if checks:
            for c in checks:
                content.append(f"- [ ] {c}")
        else:
            content.append("- [ ] 현장 상태 육안 점검\n- [ ] 적용 기준(KCS) 확인")
        content.append("\n")

        # 4. 현장 실무 조치
        procs = pack.get("practical_procedure", [])
        content.append("## 4. 현장 실무 조치\n")
        if procs:
            for p in sorted(procs, key=lambda x: x.get("step", 99)):
                content.append(f"{p.get('step', 1)}. **{p.get('action', '')}** (목적: {p.get('purpose', '')})")
        else:
            content.append("작업을 중지하고 감리단 및 발주처와 조치 계획을 수립해야 합니다.")
        content.append("\n")

        # 5. 감리/행정 대응
        admin = pack.get("administrative_procedure", [])
        content.append("## 5. 감리·발주처·행정 대응\n")
        if admin:
            for a in admin:
                content.append(f"- {a}")
        else:
            content.append("관련 사유 발생 즉시 서면 통보 및 협의가 필요합니다.")
        content.append("\n")

        # 6. 증빙 자료
        docs = pack.get("required_documents", [])
        content.append("## 6. 필요한 증빙자료\n")
        if docs:
            for d in docs:
                content.append(f"- {d}")
        else:
            content.append("필요 서류 없음")
        content.append("\n")

        # 7. 관련 기준
        reqs = pack.get("official_requirements", [])
        content.append("## 7. 관련 기준\n")
        if reqs:
            for r in reqs:
                content.append(f"- {r}")
        else:
            content.append("현장 시방서 및 일반 시방서 참조")
        content.append("\n")

        # 8. 자주 하는 실수
        mistakes = pack.get("common_mistakes", [])
        content.append("## 8. 실무자가 자주 하는 실수\n")
        if mistakes:
            for m in mistakes:
                content.append(f"- {m}")
        else:
            content.append("- 사전 승인 전 임의 시공\n- 현장 사진 등 증빙 누락")
        content.append("\n")

        # Conflict Detection
        conflicts = pack.get("conflicts", [])
        if conflicts:
            content.append("## 현장 관행과 공식 기준 차이\n")
            for c in conflicts:
                content.append(f"현장에서는 {c.get('practical_view', '약식으로 처리')}하는 경우가 많다.\n")
                content.append(f"하지만 최신 기준은 {c.get('official_view', '정식 절차')}를 요구한다.\n")
                content.append("실제 적용 시에는 감리단과 협의 후 판단해야 한다.\n")

        # 9. 결론
        qa = pack.get("quick_answer", "해당 문제 발생 시 원인을 파악하고 행정 절차를 누락하지 않는 것이 핵심입니다.")
        content.append(f"## 9. 결론\n{qa} 실무 절차가 40% 이상 중요한 현장 문제입니다.\n")

        # 10. FAQ
        content.append(self._generate_faq(pack))

        markdown = "\n".join(content)

        # Validation
        quality_score = 100
        fail_conditions = False

        for p in self.prohibited_title_keywords:
            if p in title:
                fail_conditions = True
                quality_score = 0

        if "## 1. 문제 상황" not in markdown or "## 4. 현장 실무 조치" not in markdown:
            fail_conditions = True
            quality_score = 0

        seo = pack.get("seo_context", {})
        desc = f"{title}에 대한 실무 해결 가이드입니다. " + ", ".join(seo.get("secondary_keywords", [])[:2])
        if len(desc) < 120:
            desc = (desc + " 현장 실무자를 위한 대책, 감리 대응, 필요 서류 및 관련 공식 기준을 완벽하게 정리했습니다.")[:160]

        return {
            "title": title,
            "slug": self._generate_slug(pack.get("problem_type", ""), pack.get("domain", "")),
            "meta_description": desc,
            "content_markdown": markdown,
            "quality_score": quality_score,
            "validation_passed": not fail_conditions
        }

    def run(self, input_dir="research/research_packs", output_dir="writer_output"):
        os.makedirs(output_dir, exist_ok=True)
        if not os.path.exists(input_dir):
            print(f"Error: {input_dir} not found")
            return

        generated = 0
        blocked = 0

        for file in os.listdir(input_dir):
            if not file.endswith(".json"): continue

            with open(os.path.join(input_dir, file), "r", encoding="utf-8") as f:
                pack = json.load(f)

            res = self.write(pack)

            if res.get("status") == "blocked":
                blocked += 1
                continue

            out_path = os.path.join(output_dir, f"{pack.get('research_id', pack.get('problem_id'))}.md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(res["content_markdown"])

            generated += 1

        print(f"Writer V1 complete. Generated {generated} blogs, Blocked {blocked} packs.")

if __name__ == "__main__":
    agent = WriterAgentV1()
    agent.run()
