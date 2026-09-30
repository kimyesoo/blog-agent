import json
import os

def test_taxonomy():
    assert os.path.exists('taxonomy.json'), "taxonomy.json is missing"

    with open('taxonomy.json', 'r') as f:
        tax = json.load(f)

    assert len(tax) > 0, "Taxonomy is empty"

    all_subs = []

    for main_cat, data in tax.items():
        assert "description" in data, f"'{main_cat}' missing description"
        assert "boundary" in data, f"'{main_cat}' missing boundary"
        assert "subcategories" in data, f"'{main_cat}' missing subcategories"

        subs = data["subcategories"]
        assert len(subs) > 0, f"'{main_cat}' has empty subcategories"

        for s in subs:
            assert s != "", "Empty string found in subcategories"
            all_subs.append(s)

    # Check for duplicates
    from collections import Counter
    counts = Counter(all_subs)
    duplicates = [item for item, count in counts.items() if count > 1]
    assert len(duplicates) == 0, f"Duplicate subcategories found: {duplicates}"

    print("Taxonomy validation tests passed successfully.")

if __name__ == '__main__':
    test_taxonomy()
