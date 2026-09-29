# UI Update — Chat Workspace and Persistent Chat History

The frontend now keeps the existing NASA dark aerospace theme while adding the requested navigation flow:

1. Landing page with a single **Chat with NASA Documents** action.
2. Clicking **Chat** opens a dedicated chat workspace.
3. The chat workspace has **New chat** and **Chat History** in the left sidebar.
4. Before the first question, the workspace shows the original-style hero, search box, How It Works panel, and example questions.
5. After asking a question, the answer and evidence move to the top of the main area and the question composer becomes a sticky bottom input.
6. Source cards remain available on the right side on desktop.
7. Chat history is persisted in browser `localStorage` and restored after page refresh.
8. Clicking a history item restores its question, answer, sources, and retrieved evidence.
9. **New chat** clears the active conversation without deleting saved history.

No backend changes are required for this UI update because history is intentionally stored in the browser. The existing `/api/ask` endpoint remains unchanged.
