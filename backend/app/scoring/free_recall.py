import re


def normalize_word(word: str) -> str:
    return re.sub(r"^[^\wæøåÆØÅ]+|[^\wæøåÆØÅ]+$", "", word.lower().strip())


def score_response(presented_words: list[str], response: str) -> dict:
    presented = [normalize_word(word) for word in presented_words]
    response_words = [normalize_word(word) for word in re.split(r"[\s,;]+", response)]
    response_words = [word for word in response_words if word]

    recalled_words = set(response_words).intersection(presented)
    recalled_by_position = [word in recalled_words for word in presented]
    position_groups = {
        "primacy": recalled_by_position[:5],
        "middle": recalled_by_position[5:10],
        "recency": recalled_by_position[10:15],
    }

    def group_score(values: list[bool]) -> dict:
        return {
            "recalled": sum(values),
            "total": len(values),
            "accuracy": sum(values) / len(values) if values else 0,
        }

    return {
        "recalled_count": len(recalled_words),
        "total_words": len(presented),
        "accuracy": len(recalled_words) / len(presented),
        "recalled_words": sorted(recalled_words),
        "intrusions": sorted(set(response_words).difference(presented)),
        "position_groups": {name: group_score(values) for name, values in position_groups.items()},
    }