from collections import Counter


def normalize_sequence(value: str) -> list[str]:
    return [character.upper() for character in value if character.isalnum()]


def longest_common_subsequence_length(first: list[str], second: list[str]) -> int:
    previous = [0] * (len(second) + 1)
    for first_item in first:
        current = [0]
        for index, second_item in enumerate(second, start=1):
            if first_item == second_item:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def score_response(presented_sequence: str, response: str) -> dict:
    presented = normalize_sequence(presented_sequence)
    recalled = normalize_sequence(response)

    positional_matches = sum(
        recalled_item == presented_item
        for recalled_item, presented_item in zip(recalled, presented)
    )
    item_matches = sum((Counter(presented) & Counter(recalled)).values())
    ordered_subsequence_matches = longest_common_subsequence_length(presented, recalled)
    omissions = max(len(presented) - len(recalled), 0)
    intrusions = max(len(recalled) - len(presented), 0)
    substitutions = sum(
        recalled_item != presented_item
        for recalled_item, presented_item in zip(recalled, presented)
    )
    presented_counts = {item: presented.count(item) for item in set(presented)}
    recalled_counts = {item: recalled.count(item) for item in set(recalled)}
    repetitions = sum(
        max(count - presented_counts.get(item, 0), 0)
        for item, count in recalled_counts.items()
    )
    transpositions = sum(
        recalled_item != presented[index]
        and recalled_item in presented
        for index, recalled_item in enumerate(recalled[: len(presented)])
    )

    return {
        "presented_length": len(presented),
        "response_length": len(recalled),
        "positional_matches": positional_matches,
        "positional_accuracy": positional_matches / len(presented) if presented else 0,
        "item_matches": item_matches,
        "item_accuracy": item_matches / len(presented) if presented else 0,
        "ordered_subsequence_matches": ordered_subsequence_matches,
        "ordered_subsequence_accuracy": ordered_subsequence_matches / len(presented) if presented else 0,
        "whole_sequence_correct": recalled == presented,
        "omissions": omissions,
        "intrusions": intrusions,
        "substitutions": substitutions,
        "repetitions": repetitions,
        "transpositions": transpositions,
    }