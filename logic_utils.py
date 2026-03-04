"""Pure-logic helpers for the Game Glitch Investigator guessing game."""


def get_range_for_difficulty(difficulty: str) -> tuple[int, int]:
    """Return the inclusive (low, high) number range for a given difficulty level.

    Maps a human-readable difficulty string to the corresponding numeric bounds
    used when generating the secret number and validating guesses.

    Args:
        difficulty: One of "Easy", "Normal", or "Hard". Any unrecognized value
            falls back to the Normal range.

    Returns:
        A tuple ``(low, high)`` where both endpoints are inclusive.

        - "Easy"   → (1, 20)
        - "Hard"   → (1, 50)
        - "Normal" / default → (1, 100)
    """
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str) -> tuple[bool, int | None, str | None]:
    """Parse and validate raw user input into an integer guess.

    Accepts plain integers as well as decimal strings (e.g. "7.0"), silently
    truncating the fractional part so that minor formatting variations from
    different input methods are handled gracefully.

    Args:
        raw: The raw string value submitted by the user. ``None`` and empty
            strings are treated as missing input.

    Returns:
        A three-element tuple ``(ok, guess_int, error_message)``:

        - ``ok`` (bool): ``True`` when parsing succeeded, ``False`` otherwise.
        - ``guess_int`` (int | None): The parsed integer value on success,
          ``None`` on failure.
        - ``error_message`` (str | None): A human-readable error description on
          failure, ``None`` on success.

    Examples:
        >>> parse_guess("42")
        (True, 42, None)
        >>> parse_guess("3.0")
        (True, 3, None)
        >>> parse_guess("")
        (False, None, 'Enter a guess.')
        >>> parse_guess("abc")
        (False, None, 'That is not a number.')
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except ValueError:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess: int, secret: int) -> tuple[str, str]:
    """Compare a player's guess against the secret number and return a result.

    Both arguments must be integers so that numeric ordering is correct.
    A previous string-comparison fallback was removed because lexicographic
    ordering produces wrong directional hints (e.g. "9" > "10").

    Args:
        guess: The integer value the player submitted.
        secret: The hidden target integer the player is trying to identify.

    Returns:
        A two-element tuple ``(outcome, message)``:

        - ``outcome`` (str): One of ``"Win"``, ``"Too High"``, or ``"Too Low"``.
          Callers should use this value for scoring and game-state logic.
        - ``message`` (str): A short, emoji-decorated string suitable for
          displaying directly to the player.

    Examples:
        >>> check_guess(42, 42)
        ('Win', '🎉 Correct!')
        >>> check_guess(50, 42)
        ('Too High', '📉 Go LOWER!')
        >>> check_guess(10, 42)
        ('Too Low', '📈 Go HIGHER!')
    """
    if guess == secret:
        return "Win", "🎉 Correct!"

    # FIX: Removed string-comparison fallback that gave wrong directional
    # hints (e.g., "9" > "10" alphabetically); it masked the type mismatch
    # in app.py instead of fixing it at the source.
    if guess > secret:
        return "Too High", "📉 Go LOWER!"
    return "Too Low", "📈 Go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    """Calculate and return an updated score based on the result of a single guess.

    Scoring rules:
    - **Win**: Awards ``100 - 10 * attempt_number`` points, with a minimum of
      10 points so that late wins still reward the player.  ``attempt_number``
      is 1-indexed (first guess = 1), so a first-attempt win yields 90 points.
    - **Too High / Too Low**: Deducts 5 points as a penalty for an incorrect
      guess, regardless of direction.
    - **Any other outcome**: Score is returned unchanged (no-op).

    Args:
        current_score: The player's score before this guess is evaluated.
        outcome: The result string returned by :func:`check_guess`.
            Expected values are ``"Win"``, ``"Too High"``, or ``"Too Low"``.
        attempt_number: The 1-indexed number of the current attempt within the
            round (1 = first guess, 2 = second guess, etc.).

    Returns:
        The player's new integer score after applying the outcome's point delta.

    Examples:
        >>> update_score(0, "Win", 1)
        90
        >>> update_score(90, "Too High", 2)
        85
        >>> update_score(85, "Win", 3)
        155
    """
    if outcome == "Win":
        # FIX: Removed +1 offset; first-attempt wins scored 80 instead of 90.
        points = max(100 - 10 * attempt_number, 10)
        return current_score + points

    if outcome == "Too High":
        # FIX: Removed even-attempt bonus that rewarded overshooting the
        # target; adding points for a wrong guess was an illogical glitch.
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score
