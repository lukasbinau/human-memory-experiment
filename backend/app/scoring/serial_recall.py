def score_response(presented_sequence: str, response: str) -> dict:
    presented = [digit for digit in presented_sequence if digit.isdigit()]
    recalled = [digit for digit in response if digit.isdigit()]

    positional_matches = sum(
        recalled_digit == presented_digit
        for recalled_digit, presented_digit in zip(recalled, presented)
    )
    omissions = max(len(presented) - len(recalled), 0)
    intrusions = max(len(recalled) - len(presented), 0)
    substitutions = sum(
        recalled_digit != presented_digit
        for recalled_digit, presented_digit in zip(recalled, presented)
    )
    presented_counts = {digit: presented.count(digit) for digit in set(presented)}
    recalled_counts = {digit: recalled.count(digit) for digit in set(recalled)}
    repetitions = sum(
        max(count - presented_counts.get(digit, 0), 0)
        for digit, count in recalled_counts.items()
    )
    transpositions = sum(
        recalled_digit != presented[index]
        and recalled_digit in presented
        for index, recalled_digit in enumerate(recalled[: len(presented)])
    )

    return {
        "presented_length": len(presented),
        "response_length": len(recalled),
        "positional_matches": positional_matches,
        "positional_accuracy": positional_matches / len(presented),
        "whole_sequence_correct": recalled == presented,
        "omissions": omissions,
        "intrusions": intrusions,
        "substitutions": substitutions,
        "repetitions": repetitions,
        "transpositions": transpositions,
    }