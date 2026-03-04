import random
import time
import streamlit as st
from logic_utils import get_range_for_difficulty, parse_guess, check_guess, update_score


def show_rolling_animation(final_number, attempt_num, prev_guess, low):
    """Counts from the previous guess to the current guess, then locks in."""
    placeholder = st.empty()
    start = prev_guess if prev_guess is not None else low
    direction = "↑" if final_number >= start else "↓"
    steps = 22
    for i in range(steps):
        # Linear interpolation from start toward final_number (stops just short)
        t = i / steps  # 0.0 … ~0.955, never reaches 1.0 so final frame stays distinct
        rolling_num = round(start + (final_number - start) * t)
        # Exponential slow-down: fast at start, slow near end
        delay = 0.03 + (i / steps) ** 2 * 0.18
        placeholder.markdown(
            f"""
            <div style="text-align:center; padding:18px 0;
                        background:linear-gradient(135deg,#667eea,#764ba2);
                        border-radius:14px; margin:8px 0;">
              <div style="font-size:12px; color:#c8c8ff; letter-spacing:3px;
                          text-transform:uppercase; margin-bottom:4px;">Attempt #{attempt_num}</div>
              <div style="font-size:88px; font-weight:900; color:white; line-height:1;
                          font-family:monospace; text-shadow:0 4px 18px rgba(0,0,0,0.35);
                          min-width:120px; display:inline-block;">{rolling_num}</div>
              <div style="font-size:11px; color:#b0b0ff; margin-top:6px;">{direction} counting…</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(delay)

    # Final reveal: land on the actual guess
    placeholder.markdown(
        f"""
        <div style="text-align:center; padding:18px 0;
                    background:linear-gradient(135deg,#f093fb,#f5576c);
                    border-radius:14px; margin:8px 0;
                    box-shadow:0 6px 28px rgba(240,93,251,0.35);">
          <div style="font-size:12px; color:#ffe0e0; letter-spacing:3px;
                      text-transform:uppercase; margin-bottom:4px;">Attempt #{attempt_num} — Locked In</div>
          <div style="font-size:88px; font-weight:900; color:white; line-height:1;
                      font-family:monospace; text-shadow:0 4px 18px rgba(0,0,0,0.35);
                      min-width:120px; display:inline-block;">{final_number}</div>
          <div style="font-size:11px; color:#ffe0e0; margin-top:6px;">✓ submitted</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(0.8)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

if "prev_guess" not in st.session_state:
    st.session_state.prev_guess = None

st.subheader("Make a guess")

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.score = 0
    st.session_state.history = []
    st.session_state.status = "playing"
    st.session_state.prev_guess = None
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

if submit:
    # FIX: Merged two submit blocks and moved attempt increment inside the valid-guess branch.
    # Claude Code identified that invalid inputs were still consuming attempts in the original split-block structure.
    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        show_rolling_animation(guess_int, st.session_state.attempts, st.session_state.prev_guess, low)
        st.session_state.prev_guess = guess_int

        # FIX: Replaced alternating str/int cast with direct int secret.
        # Claude Code traced the type mismatch that caused wrong comparison hints every other attempt.
        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

if "debug_open" not in st.session_state:
    st.session_state.debug_open = True

with st.expander("Developer Debug Info", expanded=st.session_state.debug_open):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
