# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- backwards lower/higher logic
- Attempts left displays n+1
- New Game button doesnt work
- Initial guess not logged until 2nd submit
- Invalid inputs still lowers attempts (logged in history)

---

## 2. How did you use AI as a teammate?

I used only Claude for this project as an introduction to using an agent. The AI got simple bug fixes correctly.

The backwards hint logic was fixed almost instantly, with the AI suggesting to switch the inequality signs.

A more misleading suggestion that Claude made was throughout fixing the attempt display. It suggested multiple fixes that led to more bugs and I had to specify that it was only the display that was wrong and not the recorded attempts itself.

The initial pytests made were very standard and used safe edge cases. It does not include extreme cases which I plan to implement later on.

---

## 3. Debugging and testing your fixes

For debugging, I initially tested the feature through running the app and interacting with it. Then I asked the AI to generate tests for the functions that were involved throughout the program.

AI explained the tests and the cases but a little more push can make AI try extreme cases to ensure that the functions work as intended and wont break.

---

## 4. What did you learn about Streamlit and state?

The secret number kept changing because its assignment was written at the top level of the program causing each rerun of Streamlit to call a random number each interaction.

Since Streamlit doesn't host a "live" webpage, it uses "reruns" to update its display. Reruns are like page refreshes with updated values whenever something in the backend changes.

Wrapping the secret number to protect it from being called each rerun kept it stable and consistent throughout a session.

---

## 5. Looking ahead: your developer habits

I'd utilize multiple agents more in future projects. I never realized how organized and efficient it is to create multiple chat session. More specific prompting could also benefit my future workflows.

AI generated code is not perfect, but its really really fast. Its much faster to check the code than writing everything from scratch.

## Stretch (Claude vs Copilot Agent)

I used Claude and Copilot Agents to fix bugs that occured while implementing the stretch features. Claude responded with more complete results, even adding to the idea at times while copilot agents required more specific prompts to complete the bug fixing and feature adding.
