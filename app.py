"""Streamlit UI for the Game Glitch Investigator guessing game."""
import random
import time
import streamlit as st
from logic_utils import (
    get_range_for_difficulty,
    parse_guess,
    check_guess,
    update_score,
)


def render_number_bar(
    current_guess,
    history,
    range_low,
    range_high,
    secret=None,
    show_secret=False,
    is_won=False,
):  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    """Render an animated number bar with range, guesses, and current guess."""
    # Filter history to only include valid integer guesses
    valid_history = [g for g in history if isinstance(g, int)]

    # Calculate position percentages
    range_span = max(1, range_high - range_low)

    def clamp_position(value):
        """Keep markers inside the track to avoid edge clipping."""
        raw_pos = ((value - range_low) / range_span) * 100
        return max(3, min(97, raw_pos))

    def get_distance_color(guess_value):
        """Calculate color based on distance from secret (blue=far, red=close)."""
        if secret is None:
            return "#B8A398"
        distance = abs(guess_value - secret)
        # If exact match, return green
        if distance == 0:
            return "#28a745"  # Green for correct guess
        max_distance = range_span
        # Normalize distance to 0-1 (0=exact match, 1=furthest possible)
        normalized = min(distance / max_distance, 1.0)
        # Interpolate from red (close) to blue (far)
        # Red: #E85D75, Blue: #4A90E2
        if normalized < 0.15:
            # Very close: deep red
            return "#D32F2F"
        if normalized < 0.3:
            # Close: red
            return "#E85D75"
        if normalized < 0.5:
            # Medium: orange/pink
            return "#FF9A8B"
        if normalized < 0.7:
            # Far: light blue
            return "#6FA8DC"
        # Very far: blue
        return "#4A90E2"

    # Build markers HTML for previous guesses
    markers_html = ""
    guess_history = valid_history[:-1] if current_guess else valid_history
    for guess in guess_history:
        if isinstance(guess, int):
            pos_percent = clamp_position(guess)
            marker_color = get_distance_color(guess)

            markers_html += (
                f'<div style="position:absolute;left:{pos_percent}%;top:50%;'
                f'transform:translate(-50%,-50%);width:12px;height:12px;'
                f'background:{marker_color};border-radius:50%;z-index:2;'
                f'box-shadow:0 2px 6px rgba(0,0,0,0.15);"></div>'
                f'<div style="position:absolute;left:{pos_percent}%;top:-25px;'
                f'transform:translateX(-50%);font-size:10px;'
                f'color:#6B5E52;font-weight:600;">{guess}</div>'
            )

    # Add secret marker if enabled
    secret_marker = ""
    if show_secret and secret is not None:  # pylint: disable=too-many-branches
        secret_pos = clamp_position(secret)
        secret_marker = (
            f'<div style="position:absolute;left:{secret_pos}%;top:50%;'
            f'transform:translate(-50%,-50%);width:16px;height:16px;'
            f'background:#FF6B6B;border:2px solid #fff;border-radius:50%;'
            f'z-index:4;box-shadow:0 0 10px rgba(255,107,107,0.5);"></div>'
            f'<div style="position:absolute;left:{secret_pos}%;top:-30px;'
            f'transform:translateX(-50%);font-size:9px;'
            f'color:#FF6B6B;font-weight:700;">TARGET {secret}</div>'
        )

    # Current guess marker
    current_marker = ""
    if current_guess is not None:  # pylint: disable=too-many-statements
        current_pos = clamp_position(current_guess)
        current_color = get_distance_color(current_guess)

        # Determine arrow direction based on whether guess needs to go higher or lower
        if secret is not None:
            if current_guess < secret:
                arrow = "&#8593;"  # Need to go higher
            elif current_guess > secret:
                arrow = "&#8595;"  # Need to go lower
            else:
                arrow = "&#9733;"  # Exact match (won)
        else:
            arrow = "&#8595;"  # Default

        current_marker = (
            f'<div style="position:absolute;left:{current_pos}%;top:50%;'
            f'transform:translate(-50%,-50%);width:18px;height:18px;'
            f'background:{current_color};'
            f'border:3px solid #4A4037;border-radius:50%;z-index:3;'
            f'box-shadow:0 4px 12px rgba(255,200,150,0.5);"></div>'
            f'<div style="position:absolute;left:{current_pos}%;top:-35px;'
            f'transform:translateX(-50%);font-size:13px;'
            f'color:#4A4037;font-weight:800;'
            f'text-shadow:0 1px 3px rgba(255,255,255,0.8);">{arrow} {current_guess}</div>'
        )

    # Render the complete number bar
    html = (
        '<div style="background: transparent; border: none; padding: 0; margin: 0;">'
        '<div style="position: relative; min-width: 320px;'
        ' height: 60px; margin: 30px 0; padding: 30px 0;'
        ' background: linear-gradient(to right, #FFDCDC, #FFF2EB, #FFE8CD);'
        ' border-radius: 30px; box-shadow: inset 0 2px 8px rgba(0,0,0,0.1), '
        '0 4px 16px rgba(255,200,150,0.2);">'
        f'<div style="position: absolute; left: 0; top: 50%; '
        f'transform: translate(0,-50%);'
        f' background: #4A4037; color: #FFF9F5; padding: 6px 12px;'
        f' border-radius: 20px; font-weight: 700; font-size: 12px;'
        f' box-shadow: 0 2px 8px rgba(0,0,0,0.2);">{range_low}</div>'
        f'<div style="position: absolute; right: 0; top: 50%; '
        f'transform: translate(0,-50%);'
        f' background: #4A4037; color: #FFF9F5; padding: 6px 12px;'
        f' border-radius: 20px; font-weight: 700; font-size: 12px;'
        f' box-shadow: 0 2px 8px rgba(0,0,0,0.2);">{range_high}</div>'
        f'{markers_html}{secret_marker}{current_marker}'
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def show_rolling_animation(final_number, attempt_num, prev_guess, range_low, is_won=False):
    """Counts from the previous guess to the current guess, then locks in."""
    placeholder = st.empty()
    start = prev_guess if prev_guess is not None else range_low
    direction = "&#8593;" if final_number >= start else "&#8595;"
    steps = 22
    for i in range(steps):
        # Linear interpolation from start toward final_number (stops just short)
        t = i / steps  # 0.0 ... ~0.955, never reaches 1.0 so final frame stays distinct
        rolling_num = round(start + (final_number - start) * t)
        # Exponential slow-down: fast at start, slow near end
        delay = 0.03 + (i / steps) ** 2 * 0.18
        placeholder.markdown(
            f"""
            <div style="text-align:center; padding:18px 0;
                        background:linear-gradient(135deg,#FFE8CD,#FFD6BA);
                        border-radius:14px; margin:8px 0; box-shadow:0 4px 12px rgba(255,200,150,0.3);">
              <div style="font-size:12px; color:#4A4037; letter-spacing:3px;
                          text-transform:uppercase; margin-bottom:4px;">Attempt #{attempt_num}</div>
              <div style="font-size:88px; font-weight:900; color:#4A4037; line-height:1;
                          font-family:monospace; text-shadow:0 2px 8px rgba(255,200,150,0.4);
                          min-width:120px; display:inline-block;">{rolling_num}</div>
              <div style="font-size:11px; color:#4A4037; margin-top:6px;">
                                {direction} counting...</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(delay)

    # Final reveal: land on the actual guess
    final_bg = "linear-gradient(135deg,#90EE90,#98FB98)" if is_won else "linear-gradient(135deg,#FFDCDC,#FFF2EB)"
    final_shadow = "0 6px 20px rgba(40,167,69,0.5)" if is_won else "0 6px 20px rgba(255,180,180,0.35)"
    final_text = "🎉 WINNER! 🎉" if is_won else "success"
    placeholder.markdown(
        f"""
        <div style="text-align:center; padding:18px 0;
                    background:{final_bg};
                    border-radius:14px; margin:8px 0;
                    box-shadow:{final_shadow};">
          <div style="font-size:12px; color:#4A4037; letter-spacing:3px;
                      text-transform:uppercase; margin-bottom:4px;">
                        Attempt #{attempt_num} - locked in</div>
          <div style="font-size:88px; font-weight:900; color:#4A4037; line-height:1;
                      font-family:monospace; text-shadow:0 2px 8px rgba(255,200,150,0.4);
                      min-width:120px; display:inline-block;">{final_number}</div>
          <div style="font-size:11px; color:#4A4037; margin-top:6px;">{final_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(0.8)

st.set_page_config(page_title="Glitchy Guesser", page_icon=":video_game:")

# Apply cozy theme styling
st.markdown("""
    <style>
        /* Cozy color palette */
        :root {
            --cozy-pink: #FFDCDC;
            --cozy-cream: #FFF2EB;
            --cozy-peach: #FFE8CD;
            --cozy-tan: #FFD6BA;
            --text-dark: #4A4037;
        }

        /* Main background */
        .stApp {
            background-color: #FFF9F5;
        }

        /* Text color for Streamlit-rendered content */
        [data-testid="stMarkdownContainer"],
        [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"],
        [data-testid="stCaptionContainer"],
        [data-testid="stNotificationContent"] {
            color: #4A4037 !important;
        }

        /* Headers and titles */
        h1, h2, h3, h4, h5, h6 {
            color: #4A4037 !important;
        }

        /* Labels for inputs */
        [data-testid="stWidgetLabel"] {
            color: #4A4037 !important;
        }

        /* Checkbox and radio styling */
        .stCheckbox > label, .stRadio > label {
            color: #4A4037 !important;
        }

        /* Select dropdown text */
        .stSelectbox label, .stMultiSelect label {
            color: #4A4037 !important;
        }

        /* Button styling */
        .stButton > button {
            background-color: #FFD6BA;
            color: #4A4037 !important;
            border: 2px solid #FFE8CD;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #FFE8CD;
            color: #4A4037 !important;
            box-shadow: 0 4px 12px rgba(255,200,150,0.3);
            transform: translateY(-2px);
        }

        /* Text input styling */
        .stTextInput > div > div > input {
            background-color: #FFF2EB;
            border-color: #FFE8CD;
            border-radius: 8px;
            color: #4A4037 !important;
        }
        .stTextInput > label {
            color: #4A4037 !important;
        }

        /* Remove form border/background */
        [data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
            margin: 0 !important;
        }
        [data-testid="stForm"] > div {
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Form submit button matches regular buttons */
        [data-testid="stFormSubmitButton"] > button {
            background-color: #FFD6BA !important;
            color: #4A4037 !important;
            border: 2px solid #FFE8CD !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }
        [data-testid="stFormSubmitButton"] > button:hover {
            background-color: #FFE8CD !important;
            box-shadow: 0 4px 12px rgba(255,200,150,0.3) !important;
            transform: translateY(-2px) !important;
        }

        /* Centered, normal guess box */
        div[data-testid="stTextInput"] > label {
            text-align: center;
            width: 100%;
            border-radius: 12px !important;
            font-weight: 700;
        }
        div[data-testid="stTextInput"] input {
            width: 100%;
            border-radius: 12px !important;
            border: 2px solid #FFD6BA !important;
            text-align: center !important;
            font-size: 1.2rem !important;
            font-weight: 600 !important;
            line-height: 50px !important;
            color: #4A4037 !important;
            box-shadow: 0 4px 12px rgba(255, 200, 150, 0.2);
            background: linear-gradient(180deg, #FFF2EB 0%, #FFE8CD 100%) !important;
        }

        @media (max-width: 640px) {
            .stButton > button {
                min-height: 2.6rem;
                font-size: 0.95rem;
            }
            .stMetric {
                padding: 0.15rem 0;
            }
        }

        /* Expander styling */
        .stExpander {
            background-color: #FFF2EB;
            border-color: #FFE8CD;
        }
        .stExpander * {
            color: #4A4037 !important;
        }
        .stExpander [data-testid="stMarkdownContainer"] {
            color: #4A4037 !important;
        }

        /* Message boxes */
        .stSuccess, .stError, .stWarning, .stInfo, .stException {
            color: #4A4037 !important;
        }
        .stSuccess > div, .stError > div, .stWarning > div, .stInfo > div {
            color: #4A4037 !important;
        }

        /* Caption text */
        .stCaption {
            color: #4A4037 !important;
        }

        /* Remove Streamlit container styling around number bar */
        [data-testid="stMarkdownContainer"] {
            background: transparent !important;
            border: none !important;
        }

        /* Remove markdown container styling around number bar */
        [data-testid="stMarkdownContainer"] {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Number Guessing Game")
st.caption("A charming guessing game with a little twist...")

# Initialize session state first
if "secret" not in st.session_state:
    st.session_state.secret = None
if "attempts" not in st.session_state:
    st.session_state.attempts = 0
if "score" not in st.session_state:
    st.session_state.score = 100
if "status" not in st.session_state:
    st.session_state.status = "playing"
if "history" not in st.session_state:
    st.session_state.history = []
if "prev_guess" not in st.session_state:
    st.session_state.prev_guess = None
if "show_debug" not in st.session_state:
    st.session_state.show_debug = False
if "last_animation" not in st.session_state:
    st.session_state.last_animation = None
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Normal"
if "settings_expanded" not in st.session_state:
    st.session_state.settings_expanded = False

# Game Settings (no sidebar)
difficulty = st.session_state.difficulty

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 10,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Attempts Left", attempt_limit - st.session_state.attempts)
with col_b:
    st.metric("Current Score", st.session_state.score)
with col_c:
    st.metric("Range", f"{low} - {high}")

# Initialize game if needed
if st.session_state.secret is None:
    st.session_state.secret = random.randint(low, high)

# Game Input Section
st.subheader("Make Your Guess")

# Disable input if game is over
if st.session_state.status != "playing":
    raw_guess = st.text_input(
        "Enter a number:",
        placeholder=f"{low} to {high}",
        key=f"guess_input_{difficulty}",
        disabled=True,
    )
else:
    raw_guess = st.text_input(
        "Enter a number:",
        placeholder=f"{low} to {high}",
        key=f"guess_input_{difficulty}",
    )

# Action buttons: Submit, Settings, New Game
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    submit = st.button("Submit", use_container_width=True, disabled=(st.session_state.status != "playing"))
with col2:
    settings_btn = st.button("Settings", use_container_width=True, key="settings_button")
with col3:
    new_game = st.button("New Game", key="new_game_top", use_container_width=True)

# Settings panel (appears when settings button is clicked)
if settings_btn:
    st.session_state.settings_expanded = not st.session_state.settings_expanded

if st.session_state.settings_expanded:
    with st.expander("⚙️ Game Settings", expanded=True):
        new_difficulty = st.selectbox(
            "Pick your difficulty",
            ["Easy", "Normal", "Hard"],
            index=["Easy", "Normal", "Hard"].index(st.session_state.difficulty),
        )
        
        if new_difficulty != st.session_state.difficulty:
            st.session_state.difficulty = new_difficulty
            st.rerun()
        st.subheader("Developer Options")
        st.checkbox(
            "Show Debug Info",
            key="show_debug",
            help="Display secret number, attempts, and game state information"
        )
        
        # Display debug info if enabled
        if st.session_state.show_debug:
            st.divider()
            st.subheader("Debug Info")
            st.write(f"**Secret:** {st.session_state.secret}")
            st.write(f"**Attempts:** {st.session_state.attempts}")
            st.write(f"**Score:** {st.session_state.score}")
            st.write(f"**Status:** {st.session_state.status}")
            if st.session_state.history:
                st.write(
                    f"**History:** {' -> '.join(str(g) for g in st.session_state.history)}"
                )
            else:
                st.write("**History:** No guesses yet")


if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.score = 100
    st.session_state.history = []
    st.session_state.status = "playing"
    st.session_state.prev_guess = None
    st.success("Fresh start!")
    st.rerun()

# Game Results Section
if submit and st.session_state.status == "playing":
    # FIX: Merged two submit blocks and moved attempt increment inside the
    # valid-guess branch so invalid inputs no longer consume attempts.
    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(f"Oops! {err}")
    elif guess_int < low or guess_int > high:
        # Guess is outside the valid range for this difficulty
        st.error(
            f"Oops! Your guess must be between {low} and {high}."
        )
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        # Store animation data before rerun so it persists
        st.session_state.last_animation = {
            "guess": guess_int,
            "attempt": st.session_state.attempts,
            "prev_guess": st.session_state.prev_guess,
        }
        st.session_state.prev_guess = guess_int

        # FIX: Replaced alternating str/int cast with direct int secret to fix
        # the type mismatch that caused wrong comparison hints every other attempt.
        outcome, message = check_guess(guess_int, st.session_state.secret)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.session_state.status = "won"
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.error(
                "No attempts left! Game over. "
                f"The secret was {st.session_state.secret}."
            )

        # Rerun to update sidebar with new attempt count and score
        st.rerun()

# Show the number bar visualization first (so it stays visible during animation)
if st.session_state.history:
    # Show the last guess as current if we have history
    last_guess = (
        st.session_state.history[-1]
        if isinstance(st.session_state.history[-1], int)
        else None
    )
    render_number_bar(
        last_guess,
        st.session_state.history,
        low,
        high,
        secret=st.session_state.secret,
        is_won=(st.session_state.status == "won"),
    )
else:
    # Show empty bar with just the range
    render_number_bar(None, [], low, high, secret=st.session_state.secret, is_won=False)

# Display the animation if one was stored from the previous submission
if st.session_state.last_animation:
    anim = st.session_state.last_animation
    show_rolling_animation(
        anim["guess"], anim["attempt"], anim["prev_guess"], low,
        is_won=(st.session_state.status == "won")
    )
    st.session_state.last_animation = None  # Clear after displaying

# Display winning message and balloons after animation
if st.session_state.status == "won":
    st.balloons()
    st.success(
        f"🎉 You won! The secret was {st.session_state.secret}. "
        f"Final score: {st.session_state.score}"
    )

st.divider()

st.caption("Made with coziness and a sprinkle of chaos")
