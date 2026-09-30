# Weight Sensitivity Validation Report

This report verifies whether changing `weights.json` profiles materially impacts the Research Agent's output across Research Readiness and Source Prioritization.

## Summary Statistics
- Total Topics Evaluated: 160
- Topics with Readiness Shifts: 2 (1.2%)
- Topics with Source Priority Shifts: 124 (77.5%)
- Configuration Dead-Zones (No Change): 34 (21.2%)

## Example Topic Shifts

### Topic: 발파 기본 설계 원리 및 검토사항 (Archetype: field_problem_solving)
| Profile | Readiness | Top Source Priority |
|---|---|---|
| Practical Blog | high | industry_pro |
| Balanced | high | industry_pro |
| Tech Reference | high | technical_standard |
| Regulation Focus | high | technical_standard |

### Topic: 토공장비 시공 중 주요 문제점과 대책 (Archetype: construction_methods)
| Profile | Readiness | Top Source Priority |
|---|---|---|
| Practical Blog | high | industry_pro |
| Balanced | high | industry_pro |
| Tech Reference | high | technical_standard |
| Regulation Focus | high | technical_standard |

### Topic: 사면 시공 시험 및 측정 방법 (Archetype: field_problem_solving)
| Profile | Readiness | Top Source Priority |
|---|---|---|
| Practical Blog | high | industry_pro |
| Balanced | high | industry_pro |
| Tech Reference | high | technical_standard |
| Regulation Focus | high | technical_standard |

### Topic: 굴착 시공 중 주요 문제점과 대책 (Archetype: construction_methods)
| Profile | Readiness | Top Source Priority |
|---|---|---|
| Practical Blog | high | industry_pro |
| Balanced | high | industry_pro |
| Tech Reference | high | technical_standard |
| Regulation Focus | high | technical_standard |

### Topic: 다짐 시설물 보수보강 가이드 (Archetype: field_problem_solving)
| Profile | Readiness | Top Source Priority |
|---|---|---|
| Practical Blog | high | industry_pro |
| Balanced | high | industry_pro |
| Tech Reference | high | technical_standard |
| Regulation Focus | high | technical_standard |

## Configuration Dead-Zones Analysis
The following topics showed absolutely no change in final evaluation regardless of profile. This usually occurs when the Mock Search Provider only returned one type of result, meaning weights had no alternative sources to prioritize.
- 상수도 적용 기준
- 터널발파 적용 기준
- 라이닝 적용 기준
- 노선측량 적용 기준
- 측량성과 적용 기준
- 일반측량 적용 기준
- 자재검사 적용 기준
- 위험성평가 시험 및 측정 방법
- 굴착안전 핵심 품질관리 기준
- 산업안전 수량 산정 방법