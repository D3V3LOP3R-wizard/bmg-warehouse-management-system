"""Core stock search service.

Currently uses an in-memory sample dataset. Replace with a DB or external API later.
"""

SAMPLE_DATA = [
    {
        "partNumber": "BMG-12345",
        "description": "Ball Bearing 6305-2RS",
        "currentBin": "A-12-04",
        "correctBin": "A-12-04",
        "quantity": 24,
        "status": "correct",
    },
    {
        "partNumber": "BMG-67890",
        "description": "Taper Roller Bearing 30206",
        "currentBin": "B-08-12",
        "correctBin": "B-08-11",
        "quantity": 18,
        "status": "incorrect",
    },
    {
        "partNumber": "BMG-54321",
        "description": "Spherical Roller Bearing 22208",
        "currentBin": "C-15-07",
        "correctBin": "C-15-07",
        "quantity": 36,
        "status": "correct",
    },
    {
        "partNumber": "BMG-98765",
        "description": "Cylindrical Roller Bearing NU206",
        "currentBin": "D-03-09",
        "correctBin": "D-03-09",
        "quantity": 42,
        "status": "correct",
    },
    {
        "partNumber": "BMG-13579",
        "description": "Needle Roller Bearing HK1012",
        "currentBin": "A-05-14",
        "correctBin": "A-05-13",
        "quantity": 15,
        "status": "incorrect",
    },
]


def search_stock(query: str, data=None):
    """Return list of stock items matching `query` in part number or description.

    Matching is case-insensitive and will return any item where the query is
    contained in the part number or description.
    """
    if data is None:
        data = SAMPLE_DATA

    q = (query or "").strip()
    if not q:
        return []

    q_lower = q.lower()
    results = []
    for item in data:
        if q_lower in item.get("partNumber", "").lower() or q_lower in item.get("description", "").lower():
            results.append(item)

    return results


if __name__ == "__main__":
    import json

    print(json.dumps(search_stock("BMG-12345"), indent=2))
