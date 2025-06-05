from src.eutils_retrieval.query import create_one_combination_query

TEST_DEVICES = [
    "Hemoblast",
    "Biom'up",
    "Gelfoam",
    "Gelatin sponge",
]
TEST_INDICATORS = ["Urology Indicators", "urological surgery", "vascular surgery"]


def test_create_query():
    expected_query = (
        '("Hemoblast" OR "Biom\'up" OR "Gelfoam" OR "Gelatin sponge")'
        " AND "
        '("Urology Indicators" OR "urological surgery" OR "vascular surgery")'
    )
    result = create_one_combination_query(TEST_DEVICES, TEST_INDICATORS)
    assert result == expected_query
