import json
import collections

PROFILES = ["practical_blog", "balanced", "technical_reference", "regulation_focus"]

def load_summaries():
    data = {}
    for profile in PROFILES:
        filename = f"research/summary_{'practical' if profile == 'practical_blog' else 'reg' if profile == 'regulation_focus' else 'tech' if profile == 'technical_reference' else 'balanced'}.json"
        with open(filename, 'r') as f:
            data[profile] = json.load(f)
    return data

def generate_report():
    data = load_summaries()

    if not data["practical_blog"]:
        print("No data found")
        return

    num_topics = len(data["practical_blog"])

    topic_map = {}
    for i in range(num_topics):
        t_data = {}
        for profile in PROFILES:
            t_data[profile] = data[profile][i]
        topic_map[data["practical_blog"][i]["topic"]] = t_data

    significant_topics = []
    moderate_topics = []
    no_change_topics = []

    profile_tier_contrib = {p: {"Tier A": 0, "Tier B": 0, "Tier C": 0, "Tier D": 0, "total": 0} for p in PROFILES}
    profile_top_sources = {p: collections.Counter() for p in PROFILES}

    for topic, profiles_data in topic_map.items():
        readiness_set = set(profiles_data[p]["research_readiness"] for p in PROFILES)
        top_source_set = set(profiles_data[p]["top_source_priority"] for p in PROFILES)
        top_evidence_set = set(tuple(e["url"] for e in profiles_data[p]["evidence_hierarchy"]["ranked_sources"]) for p in PROFILES)

        is_readiness_changed = len(readiness_set) > 1
        is_top_source_changed = len(top_source_set) > 1
        is_evidence_changed = len(top_evidence_set) > 1

        if is_readiness_changed and is_top_source_changed:
            significant_topics.append(topic)
        elif is_top_source_changed or is_evidence_changed:
            moderate_topics.append(topic)
        else:
            no_change_topics.append(topic)

        for p in PROFILES:
            t_data = profiles_data[p]
            for tier, count in t_data["tier_distribution"].items():
                profile_tier_contrib[p][tier] += count
                profile_tier_contrib[p]["total"] += count

            for source in t_data["evidence_hierarchy"]["ranked_sources"]:
                profile_top_sources[p][source["url"]] += 1

    report = []
    report.append("# Weight Sensitivity Validation Report\n")
    report.append("This report verifies whether changing `weights.json` profiles materially impacts the Research Agent's output across Research Readiness and Source Prioritization.\n")

    report.append("## Summary Statistics")
    report.append(f"- Total Topics Evaluated: {num_topics}")
    report.append(f"- Topics with Significant Sensitivity (Readiness & Priority shifts): {len(significant_topics)} ({len(significant_topics)/num_topics*100:.1f}%)")
    report.append(f"- Topics with Moderate Sensitivity (Priority or Evidence shifts): {len(moderate_topics)} ({len(moderate_topics)/num_topics*100:.1f}%)")
    report.append(f"- Topics with No Meaningful Sensitivity (Configuration Dead-Zones): {len(no_change_topics)} ({len(no_change_topics)/num_topics*100:.1f}%)\n")

    report.append("## Percentage Contribution of Tier A/B/C/D Sources")
    for p in PROFILES:
        total = profile_tier_contrib[p]["total"] or 1
        report.append(f"### {p}")
        report.append(f"- Tier A: {profile_tier_contrib[p]['Tier A']/total*100:.1f}%")
        report.append(f"- Tier B: {profile_tier_contrib[p]['Tier B']/total*100:.1f}%")
        report.append(f"- Tier C: {profile_tier_contrib[p]['Tier C']/total*100:.1f}%")
        report.append(f"- Tier D: {profile_tier_contrib[p]['Tier D']/total*100:.1f}%")
    report.append("")

    report.append("## Top 20 Sources Most Frequently Selected Under Each Profile")
    for p in PROFILES:
        report.append(f"### {p}")
        for source, count in profile_top_sources[p].most_common(20):
            report.append(f"- {source} ({count} times)")
    report.append("")

    report.append("## Detailed Topic Comparisons")
    report.append("Showing representative topics to illustrate the sensitivity across profiles.\n")

    # Pick 10 representative topics (mix of significant, moderate, and dead-zones)
    sample_topics = (significant_topics[:3] + moderate_topics[:4] + no_change_topics[:3])
    if len(sample_topics) < 10:
        sample_topics = list(topic_map.keys())[:10]

    for topic in sample_topics:
        report.append(f"### Topic: {topic}")
        report.append(f"**Archetype:** {topic_map[topic]['practical_blog']['content_archetype']}\n")

        report.append("| Profile | Readiness | Top Source Priority | Top Evidence URL |")
        report.append("|---|---|---|---|")
        for p in PROFILES:
            t_data = topic_map[topic][p]
            readiness = t_data['research_readiness']
            top_source = t_data['top_source_priority']
            top_url = t_data['evidence_hierarchy']['ranked_sources'][0]['url'] if t_data['evidence_hierarchy']['ranked_sources'] else 'N/A'
            report.append(f"| {p} | {readiness} | {top_source} | {top_url} |")
        report.append("")

    report.append("## Sensitivity Analysis\n")

    report.append("### 1. Topics with Significant Profile Sensitivity")
    report.append("These topics showed changes in *both* research readiness and top source priority across profiles. This indicates highly balanced queries where different profiles successfully push different tiers of information over the readiness threshold.")
    for t in significant_topics[:5]: report.append(f"- {t}")
    report.append(f"... (total {len(significant_topics)} topics)\n")

    report.append("### 2. Topics with Moderate Profile Sensitivity")
    report.append("These topics showed changes in top source priority or evidence hierarchy, but the overall research readiness remained stable. This indicates that while the system successfully reordered sources based on the profile, there was enough information overall to maintain the same readiness level.")
    for t in moderate_topics[:5]: report.append(f"- {t}")
    report.append(f"... (total {len(moderate_topics)} topics)\n")

    report.append("### 3. Topics with No Meaningful Profile Sensitivity (Configuration Dead-Zones)")
    report.append("These topics showed absolutely no change in final evaluation regardless of profile. **WHY no change occurred:** This usually occurs when the Mock Search Provider only returned one type of result (e.g. only Tier A, or only Tier C), meaning the dynamic weights had no alternative sources to prioritize. If only Law documents are found, even the 'practical_blog' profile must select Law as the top source.")
    for t in no_change_topics[:5]: report.append(f"- {t}")
    report.append(f"... (total {len(no_change_topics)} topics)\n")

    report.append("## Recommendations for Improving Profile Differentiation")
    report.append("1. **Enhance Search Diversity:** Ensure the Mock Search Provider returns a wider variety of sources (Tier A/B/C/D) for every query. Dead-zones are caused by a lack of diverse evidence to re-rank.")
    report.append("2. **Adjust Readiness Thresholds:** Research readiness could be tied directly to the *presence* of the top-weighted tier for the active profile, rather than a cumulative score. For example, 'regulation_focus' might require Tier A to be 'high' readiness, whereas 'practical_blog' could achieve 'high' readiness with only Tier C.")
    report.append("3. **Widen Weight Deltas:** The differences between weights in `weights.json` could be increased to force more dramatic re-ranking, especially for borderline sources.")

    with open("weight_sensitivity_report.md", "w") as f:
        f.write("\n".join(report))

if __name__ == "__main__":
    generate_report()
