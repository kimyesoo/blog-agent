# Civil Engineering Taxonomy Report

## 1. Overview
This taxonomy is designed to support the Topic Research Agent. It ensures that content generation is balanced across the entire spectrum of civil engineering practices in South Korea, preventing over-concentration in specific areas like soil testing.

## 2. Statistics
- **Total Main Categories (대분류):** 14
- **Total Subcategories (세부분류):** 105

## 3. Category Distribution (분야별 비율)
| Main Category | Subcategory Count | Ratio (%) |
|---------------|-------------------|-----------|
| 토공 | 8 | 7.6% |
| 지반 및 토질 | 8 | 7.6% |
| 상하수도 | 9 | 8.6% |
| 도로 | 8 | 7.6% |
| 구조물 | 8 | 7.6% |
| 교량 | 8 | 7.6% |
| 터널 | 8 | 7.6% |
| 품질관리 | 8 | 7.6% |
| 측량 | 7 | 6.7% |
| 건설안전 | 7 | 6.7% |
| 공무 | 8 | 7.6% |
| 적산 및 공사비 | 6 | 5.7% |
| 건설기준 | 6 | 5.7% |
| 유지관리 | 6 | 5.7% |

## 4. Bias Analysis (편중 여부 분석)
The taxonomy successfully covers 14 distinct main categories ranging from structural engineering to public administration (공무), safety, and cost estimation (적산). Subcategories are relatively evenly distributed (each taking ~5-8% of the total taxonomy). This ensures no single domain, such as `지반 및 토질` (Soil Mechanics), dominates the overall content pool.

## 5. Future Usage Instructions for Topic Research Agent
The `Topic Research Agent` must read `taxonomy.json` prior to execution. When researching topics, it should:
1. Distribute candidate generation across multiple main categories.
2. Track the number of generated topics per subcategory to ensure adherence to the balanced ratios defined in this taxonomy.
3. Map newly discovered keywords directly to this taxonomy to maintain structural integrity.
