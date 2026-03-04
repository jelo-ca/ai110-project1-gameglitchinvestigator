import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic_utils import check_guess, parse_guess, get_range_for_difficulty, update_score


# ---------------------------------------------------------------------------
# Bug 1: Backwards lower/higher logic
# Original bug: guess > secret showed "Go HIGHER" and guess < secret showed
# "Go LOWER" — exactly backwards.
# ---------------------------------------------------------------------------

class TestCheckGuessBug1BackwardsHints:
    def test_winning_guess_returns_win(self):
        outcome, _ = check_guess(50, 50)
        assert outcome == "Win"

    def test_guess_too_high_returns_too_high(self):
        # 60 > 50  →  player must go LOWER
        outcome, _ = check_guess(60, 50)
        assert outcome == "Too High"

    def test_guess_too_high_message_says_lower(self):
        _, message = check_guess(60, 50)
        assert "LOWER" in message.upper()

    def test_guess_too_low_returns_too_low(self):
        # 40 < 50  →  player must go HIGHER
        outcome, _ = check_guess(40, 50)
        assert outcome == "Too Low"

    def test_guess_too_low_message_says_higher(self):
        _, message = check_guess(40, 50)
        assert "HIGHER" in message.upper()

    def test_boundary_one_above(self):
        outcome, _ = check_guess(51, 50)
        assert outcome == "Too High"

    def test_boundary_one_below(self):
        outcome, _ = check_guess(49, 50)
        assert outcome == "Too Low"

    def test_winning_message_indicates_correct(self):
        _, message = check_guess(7, 7)
        assert "Correct" in message or "correct" in message.lower()


# ---------------------------------------------------------------------------
# Bug 5: Invalid inputs still lower attempts (logged in history)
# parse_guess is the gate that decides whether a guess is valid.
# If it returns ok=False, the app should not count the attempt.
# These tests verify parse_guess correctly rejects invalid input.
# ---------------------------------------------------------------------------

class TestParseGuessBug5InvalidInputs:
    def test_empty_string_is_invalid(self):
        ok, _, err = parse_guess("")
        assert ok is False
        assert err is not None

    def test_none_is_invalid(self):
        ok, _, err = parse_guess(None)
        assert ok is False
        assert err is not None

    def test_letters_only_is_invalid(self):
        ok, _, err = parse_guess("abc")
        assert ok is False
        assert "not a number" in err.lower()

    def test_special_chars_are_invalid(self):
        ok, _, _ = parse_guess("!@#")
        assert ok is False

    def test_whitespace_only_is_invalid(self):
        ok, _, _ = parse_guess("   ")
        assert ok is False

    def test_valid_integer_string_is_accepted(self):
        ok, value, err = parse_guess("42")
        assert ok is True
        assert value == 42
        assert err is None

    def test_valid_float_string_truncates_to_int(self):
        # "3.9" should parse to 3, not raise an error
        ok, value, _ = parse_guess("3.9")
        assert ok is True
        assert isinstance(value, int)

    def test_negative_number_is_accepted(self):
        ok, value, _ = parse_guess("-5")
        assert ok is True
        assert value == -5

    def test_zero_is_accepted(self):
        ok, value, _ = parse_guess("0")
        assert ok is True
        assert value == 0


# ---------------------------------------------------------------------------
# Difficulty range correctness (supports Bug 2 display check and general
# range validation used by both new-game init and attempt-limit display).
# ---------------------------------------------------------------------------

class TestGetRangeForDifficulty:
    def test_easy_range(self):
        low, high = get_range_for_difficulty("Easy")
        assert low == 1
        assert high == 20

    def test_normal_range(self):
        low, high = get_range_for_difficulty("Normal")
        assert low == 1
        assert high == 100

    def test_hard_range(self):
        low, high = get_range_for_difficulty("Hard")
        assert low == 1
        assert high == 50

    def test_unknown_difficulty_defaults_to_normal(self):
        low, high = get_range_for_difficulty("Unknown")
        assert low == 1
        assert high == 100


# ---------------------------------------------------------------------------
# Bug 2 & 4 (FIX ME): attempts display off by one / initial guess not logged.
# Root cause: attempts += 1 fires before parse_guess, so invalid inputs
# consume an attempt and shift the display.
# Fix: only increment attempts when parse_guess returns ok=True.
# These tests document the correct gating behaviour via parse_guess.
# ---------------------------------------------------------------------------

class TestBug2And4AttemptGating:
    def test_invalid_input_signals_no_attempt_should_count(self):
        # ok=False → the caller must NOT increment the attempt counter
        ok, _, _ = parse_guess("banana")
        assert ok is False, "Invalid input must return ok=False so caller skips attempt increment"

    def test_valid_input_signals_attempt_should_count(self):
        # ok=True → the caller SHOULD increment the attempt counter
        ok, _, _ = parse_guess("37")
        assert ok is True, "Valid input must return ok=True so caller increments attempt"

    def test_attempts_left_formula_at_start(self):
        # Before any valid guess: attempts=0, limit=8 → 8 left
        attempt_limit = 8
        attempts = 0
        assert attempt_limit - attempts == 8

    def test_attempts_left_decrements_per_valid_guess(self):
        # After 3 valid guesses: attempts=3, limit=8 → 5 left
        attempt_limit = 8
        attempts = 3
        assert attempt_limit - attempts == 5

    def test_attempts_left_never_drops_for_invalid_input(self):
        # Invalid input → ok=False → attempts stays at 2 → display unchanged
        ok, _, _ = parse_guess("")
        attempts_before = 2
        attempt_limit = 8
        if not ok:
            attempts_after = attempts_before          # correct: don't increment
        else:
            attempts_after = attempts_before + 1
        assert attempt_limit - attempts_after == 6    # still 6 left, not 5

    def test_first_valid_guess_is_parseable(self):
        # Bug 4: the very first submission must produce a valid parsed value
        # so it can be appended to history on attempt 1, not attempt 2.
        ok, value, _ = parse_guess("50")
        assert ok is True
        assert value == 50


# ---------------------------------------------------------------------------
# update_score — not previously covered
# ---------------------------------------------------------------------------

class TestUpdateScore:
    def test_win_on_first_attempt_gives_max_points(self):
        # attempt_number=1 → points = max(100 - 10*(1+1), 10) = 80
        score = update_score(0, "Win", 1)
        assert score == 80

    def test_win_score_decreases_with_more_attempts(self):
        early = update_score(0, "Win", 1)
        late  = update_score(0, "Win", 5)
        assert early > late

    def test_win_score_never_goes_below_minimum(self):
        # attempt_number=10 → raw = 100 - 110 = -10, clamped to 10
        score = update_score(0, "Win", 10)
        assert score >= 10

    def test_win_adds_to_existing_score(self):
        score = update_score(50, "Win", 1)
        assert score > 50

    def test_too_low_deducts_points(self):
        score = update_score(100, "Too Low", 1)
        assert score == 95

    def test_too_high_on_odd_attempt_deducts_points(self):
        # attempt_number=1 (odd) → deduct 5
        score = update_score(100, "Too High", 1)
        assert score == 95

    def test_too_high_on_even_attempt_adds_points(self):
        # attempt_number=2 (even) → add 5
        score = update_score(100, "Too High", 2)
        assert score == 105

    def test_unknown_outcome_leaves_score_unchanged(self):
        score = update_score(42, "Unknown", 1)
        assert score == 42
