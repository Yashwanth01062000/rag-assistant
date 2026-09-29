import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = "http://127.0.0.1:8000";
const HISTORY_KEY = "legal-rag-chat-history-v3";
const ACTIVE_DOCUMENT_KEY = "legal-rag-active-document-v1";

/* =========================================================
   ICONS
========================================================= */

function Icon({ name, size = 18 }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
  };

  const paths = {
    upload: (
      <>
        <path d="M12 16V4" />
        <path d="m7 9 5-5 5 5" />
        <path d="M5 20h14" />
      </>
    ),

    file: (
      <>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
        <path d="M14 2v6h6" />
        <path d="M8 13h8M8 17h6" />
      </>
    ),

    send: (
      <>
        <path d="m22 2-7 20-4-9-9-4Z" />
        <path d="M22 2 11 13" />
      </>
    ),

    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),

    plus: (
      <>
        <path d="M12 5v14M5 12h14" />
      </>
    ),

    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),

    trash: (
      <>
        <path d="M3 6h18" />
        <path d="M8 6V4h8v2" />
        <path d="M19 6l-1 15H6L5 6" />
        <path d="M10 11v6M14 11v6" />
      </>
    ),

    home: (
      <>
        <path d="m3 10 9-7 9 7" />
        <path d="M5 9v11h14V9" />
        <path d="M9 20v-6h6v6" />
      </>
    ),

    x: (
      <>
        <path d="m6 6 12 12M18 6 6 18" />
      </>
    ),

    check: <path d="m5 12 4 4L19 6" />,

    shield: (
      <>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),

    chevron: <path d="m9 18 6-6-6-6" />,

    history: (
      <>
        <path d="M3 12a9 9 0 1 0 3-6.7" />
        <path d="M3 4v5h5" />
        <path d="M12 7v5l3 2" />
      </>
    ),
  };

  return <svg {...common}>{paths[name]}</svg>;
}

/* =========================================================
   LOCAL STORAGE HELPERS
========================================================= */

function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);

    if (!raw) {
      /*
       * Try the previous version too.
       * This allows existing chats from the older UI
       * to remain available.
       */
      const oldRaw = localStorage.getItem("legal-rag-chat-history-v2");

      if (!oldRaw) return [];

      const oldParsed = JSON.parse(oldRaw);

      if (!Array.isArray(oldParsed)) {
        return [];
      }

      return oldParsed.map(normalizeHistoryItem).filter(Boolean);
    }

    const parsed = JSON.parse(raw);

    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.map(normalizeHistoryItem).filter(Boolean);
  } catch {
    return [];
  }
}

function normalizeHistoryItem(item) {
  if (!item || typeof item !== "object") {
    return null;
  }

  /*
   * New format:
   *
   * {
   *   id,
   *   title,
   *   messages: [...]
   * }
   */

  if (Array.isArray(item.messages)) {
    return {
      ...item,
      messages: item.messages.map((message) => ({
        id: message.id || `message-${Date.now()}-${Math.random()}`,
        question: message.question || "",
        answer: message.answer || "",
        sources: Array.isArray(message.sources)
          ? message.sources
          : [],
        chunks: Array.isArray(message.chunks)
          ? message.chunks
          : [],
        error: message.error || "",
        loading: false,
      })),
    };
  }

  /*
   * Old format:
   *
   * {
   *   question,
   *   answer,
   *   sources,
   *   chunks
   * }
   *
   * Convert it into the new continuous-chat format.
   */

  if (item.question) {
    return {
      id: item.id || `chat-${Date.now()}-${Math.random()}`,
      title: item.title || item.question.slice(0, 70),
      document: item.document || null,
      createdAt: item.createdAt || Date.now(),
      timeLabel:
        item.timeLabel ||
        new Date(item.createdAt || Date.now()).toLocaleString([], {
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
        }),
      messages: [
        {
          id: `message-${item.id || Date.now()}`,
          question: item.question,
          answer: item.answer || "",
          sources: Array.isArray(item.sources)
            ? item.sources
            : [],
          chunks: Array.isArray(item.chunks)
            ? item.chunks
            : [],
          error: "",
          loading: false,
        },
      ],
    };
  }

  return null;
}

function saveHistory(history) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  } catch {
    // Ignore localStorage errors.
  }
}

function loadActiveDocument() {
  try {
    const raw = localStorage.getItem(ACTIVE_DOCUMENT_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveActiveDocument(document) {
  try {
    if (document) {
      localStorage.setItem(
        ACTIVE_DOCUMENT_KEY,
        JSON.stringify(document)
      );
    } else {
      localStorage.removeItem(ACTIVE_DOCUMENT_KEY);
    }
  } catch {
    // Ignore localStorage errors.
  }
}

/* =========================================================
   BRAND
========================================================= */

function Brand() {
  return (
    <div className="brand-wrap">
      <div className="brand-mark">
        <span className="brand-orbit orbit-one" />
        <span className="brand-orbit orbit-two" />
        <span className="brand-core">L</span>
      </div>

      <div>
        <div className="brand-name">
          Legal Document Assistant
        </div>

        <div className="brand-subtitle">
          RAG-powered legal knowledge workspace
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   UPLOAD PAGE
========================================================= */

function UploadPage({ onUploaded }) {
  const inputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  function chooseFile(selected) {
    setError("");

    if (!selected) {
      return;
    }

    if (
      selected.type !== "application/pdf" &&
      !selected.name.toLowerCase().endsWith(".pdf")
    ) {
      setError("Please select a PDF file.");
      return;
    }

    if (selected.size > 25 * 1024 * 1024) {
      setError("PDF must be 25 MB or smaller.");
      return;
    }

    setFile(selected);
  }

  async function upload() {
    if (!file || uploading) {
      return;
    }

    setUploading(true);
    setError("");

    try {
      const form = new FormData();
      form.append("file", file);

      const response = await fetch(
        `${API_URL}/api/documents/upload`,
        {
          method: "POST",
          body: form,
        }
      );

      let data = null;

      try {
        data = await response.json();
      } catch {
        throw new Error(
          "The backend returned an invalid response."
        );
      }

      if (!response.ok) {
        throw new Error(
          data?.detail || "PDF upload failed."
        );
      }

      onUploaded(data);
    } catch (err) {
      setError(
        err.message ||
          "Unable to upload the PDF. Make sure FastAPI is running."
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="app-shell upload-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="topbar">
        <Brand />

        <div className="status-pill">
          <span className="status-dot" />
          Local legal knowledge base
        </div>
      </header>

      <main className="upload-main">
        <div className="upload-eyebrow">
          <span className="eyebrow-line" />
          LEGAL DOCUMENT INTELLIGENCE
          <span className="eyebrow-line" />
        </div>

        <div className="upload-icon">
          <Icon name="file" size={34} />
        </div>

        <h1>
          Upload your <span>legal PDF.</span>
        </h1>

        <p className="upload-description">
          Upload a document and the assistant will extract its text,
          create searchable legal chunks, and open a workspace with
          the PDF on the left and grounded chat on the right.
        </p>

        <div
          className={`drop-zone ${dragging ? "dragging" : ""} ${
            file ? "has-file" : ""
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            chooseFile(e.dataTransfer.files?.[0]);
          }}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              inputRef.current?.click();
            }
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            hidden
            onChange={(e) =>
              chooseFile(e.target.files?.[0])
            }
          />

          <div className="drop-icon">
            <Icon name="upload" size={25} />
          </div>

          {file ? (
            <>
              <strong>{file.name}</strong>
              <span>
                {formatBytes(file.size)} · PDF selected
              </span>
              <small>
                Click to choose a different PDF
              </small>
            </>
          ) : (
            <>
              <strong>
                Drag & drop your PDF here
              </strong>

              <span>
                or click to browse from your computer
              </span>

              <small>
                Maximum file size: 25 MB
              </small>
            </>
          )}
        </div>

        {error && (
          <div className="upload-error">
            {error}
          </div>
        )}

        <button
          className="continue-button"
          disabled={!file || uploading}
          onClick={upload}
          type="button"
        >
          {uploading ? (
            <span className="button-spinner" />
          ) : (
            <Icon name="upload" size={17} />
          )}

          {uploading
            ? "Processing PDF..."
            : "Upload & Continue"}
        </button>

        <div className="upload-features">
          <span>
            <Icon name="shield" size={15} />
            Grounded answers
          </span>

          <span>
            <Icon name="search" size={15} />
            Semantic retrieval
          </span>

          <span>
            <Icon name="file" size={15} />
            Page citations
          </span>
        </div>
      </main>
    </div>
  );
}

/* =========================================================
   FILE SIZE
========================================================= */

function formatBytes(bytes) {
  if (!bytes) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];

  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );

  return `${(
    bytes / Math.pow(1024, index)
  ).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

/* =========================================================
   HISTORY PANEL
========================================================= */

function HistoryPanel({
  history,
  activeId,
  onSelect,
  onDelete,
  onClear,
  onNewChat,
  onClose,
}) {
  return (
    <div className="history-panel">
      <div className="history-panel-head">
        <div>
          <div className="panel-kicker">
            CHAT HISTORY
          </div>

          <span>
            {history.length} saved conversation
            {history.length === 1 ? "" : "s"}
          </span>
        </div>

        <button
          className="icon-button"
          onClick={onClose}
          type="button"
        >
          <Icon name="x" size={17} />
        </button>
      </div>

      <button
        className="history-new-button"
        onClick={onNewChat}
        type="button"
      >
        <Icon name="plus" size={16} />
        New chat
      </button>

      <div className="history-scroll">
        {history.length === 0 ? (
          <div className="history-empty-small">
            <Icon name="clock" size={20} />

            <p>No previous chats yet.</p>

            <span>
              Your questions will appear here after
              you ask them.
            </span>
          </div>
        ) : (
          history.map((item) => (
            <div
              className={`history-row ${
                activeId === item.id
                  ? "active"
                  : ""
              }`}
              key={item.id}
            >
              <button
                className="history-row-main"
                onClick={() =>
                  onSelect(item.id)
                }
                type="button"
              >
                <Icon name="history" size={15} />

                <span>
                  <strong>
                    {item.title}
                  </strong>

                  <small>
                    {item.messages?.length || 0} question
                    {item.messages?.length === 1
                      ? ""
                      : "s"}{" "}
                    · {item.timeLabel}
                  </small>
                </span>
              </button>

              <button
                className="history-row-delete"
                onClick={() =>
                  onDelete(item.id)
                }
                title="Delete chat"
                type="button"
              >
                <Icon name="trash" size={14} />
              </button>
            </div>
          ))
        )}
      </div>

      {history.length > 0 && (
        <button
          className="history-clear"
          onClick={onClear}
          type="button"
        >
          <Icon name="trash" size={14} />
          Clear chat history
        </button>
      )}
    </div>
  );
}

/* =========================================================
   PDF VIEWER
========================================================= */

function PdfViewer({
  document,
  page,
  onBack,
}) {
  if (!document) {
    return null;
  }

  const baseUrl = `${API_URL}${document.file_url}`;

  const viewerUrl = page
    ? `${baseUrl}#page=${page}`
    : baseUrl;

  return (
    <section className="pdf-panel">
      <div className="pdf-panel-head">
        <div className="pdf-document-info">
          <div className="pdf-file-icon">
            <Icon name="file" size={19} />
          </div>

          <div>
            <strong title={document.filename}>
              {document.filename}
            </strong>

            <span>
              {document.page_count} page
              {document.page_count === 1
                ? ""
                : "s"}{" "}
              · {document.chunk_count} searchable chunks
            </span>
          </div>
        </div>

        <button
          className="change-pdf-button"
          onClick={onBack}
          type="button"
        >
          Change PDF
        </button>
      </div>

      <div className="pdf-viewer-wrap">
        <iframe
          key={viewerUrl}
          src={viewerUrl}
          title={document.filename}
          className="pdf-viewer"
        />
      </div>
    </section>
  );
}

/* =========================================================
   SOURCE CARD
========================================================= */

function SourceCard({
  source,
  onClick,
}) {
  return (
    <button
      className="source-card"
      onClick={() => onClick(source)}
      type="button"
    >
      <span className="source-icon">
        <Icon name="file" size={17} />
      </span>

      <span className="source-copy">
        <strong>
          {source.document ||
            "Legal Document"}
        </strong>

        <small>
          Page {source.page}
          {source.page_end &&
          source.page_end !== source.page
            ? `–${source.page_end}`
            : ""}
        </small>

        <em>
          {source.section ||
            "Referenced section"}
        </em>
      </span>

      <Icon name="chevron" size={15} />
    </button>
  );
}

/* =========================================================
   SINGLE MESSAGE
========================================================= */

function ChatMessage({
  message,
  onSourceClick,
  onEvidenceClick,
  onCopy,
  copiedId,
}) {
  const isLoading = message.loading;
  const hasError = Boolean(message.error);

  return (
    <div
      className="chat-message"
      data-message-id={message.id}
    >
      {/* USER QUESTION */}
      <div className="question-bubble">
        <span>YOU</span>
        <div>{message.question}</div>
      </div>

      {/* LOADING */}
      {isLoading ? (
        <div className="answer-box loading-box">
          <span className="button-spinner" />
          Searching the uploaded document...
        </div>
      ) : hasError ? (
        /* ERROR */
        <div className="answer-box error-box">
          <strong>
            Unable to complete the request
          </strong>

          <p>{message.error}</p>
        </div>
      ) : (
        <>
          {/* ANSWER */}
          <div className="answer-box">
            <div className="answer-box-head">
              <div className="grounded-label">
                <span className="status-dot" />
                GROUNDED ANSWER
              </div>

              <button
                className="copy-answer"
                onClick={() =>
                  onCopy(
                    message.id,
                    message.answer
                  )
                }
                type="button"
              >
                {copiedId === message.id ? (
                  <Icon name="check" size={14} />
                ) : (
                  <Icon name="file" size={14} />
                )}

                {copiedId === message.id
                  ? "Copied"
                  : "Copy"}
              </button>
            </div>

            <p>
              {message.answer ||
                "No answer was returned."}
            </p>
          </div>

          {/* SOURCES */}
          {message.sources?.length > 0 && (
            <div className="sources-section">
              <div className="results-section-head">
                <div>
                  <div className="panel-kicker">
                    CITATIONS
                  </div>

                  <h3>
                    Document evidence
                  </h3>
                </div>

                <span>
                  {message.sources.length} source
                  {message.sources.length === 1
                    ? ""
                    : "s"}
                </span>
              </div>

              <div className="source-list">
                {message.sources.map(
                  (source, index) => (
                    <SourceCard
                      key={`${
                        source.chunk_id ||
                        "source"
                      }-${index}`}
                      source={source}
                      onClick={onSourceClick}
                    />
                  )
                )}
              </div>
            </div>
          )}

          {/* RETRIEVAL TRACE */}
          {message.chunks?.length > 0 && (
            <div className="evidence-section">
              <div className="results-section-head">
                <div>
                  <div className="panel-kicker">
                    RETRIEVAL TRACE
                  </div>

                  <h3>
                    Retrieved evidence
                  </h3>
                </div>

                <span>
                  {message.chunks.length} chunks
                </span>
              </div>

              {message.chunks
                .slice(0, 4)
                .map((chunk, index) => (
                  <button
                    className="evidence-card"
                    key={
                      chunk.chunk_id ||
                      `${message.id}-${index}`
                    }
                    onClick={() =>
                      onEvidenceClick(
                        chunk
                      )
                    }
                    type="button"
                  >
                    <div className="evidence-card-top">
                      <span>
                        {String(
                          index + 1
                        ).padStart(2, "0")}
                      </span>

                      <span>
                        {Math.round(
                          (chunk.score || 0) *
                            100
                        )}
                        % match · Page{" "}
                        {chunk.page}
                      </span>
                    </div>

                    <strong>
                      {chunk.section ||
                        "Legal document section"}
                    </strong>

                    <p>
                      {chunk.text}
                    </p>
                  </button>
                ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* =========================================================
   CHAT WORKSPACE
========================================================= */

function ChatWorkspace({
  document,
  history,
  setHistory,
  onChangeDocument,
}) {
  /*
   * IMPORTANT:
   *
   * inputText = ONLY the textarea.
   *
   * messages = ONLY the conversation.
   *
   * They are completely separate.
   */
  const [inputText, setInputText] =
    useState("");

  const [messages, setMessages] =
    useState([]);

  const [activeId, setActiveId] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [historyOpen, setHistoryOpen] =
    useState(false);

  const [sourcePage, setSourcePage] =
    useState(null);

  const [copiedId, setCopiedId] =
    useState(null);

  const textareaRef = useRef(null);

  const documentHistory = history.filter(
    (item) =>
      item.document?.document_id ===
      document.document_id
  );

  const hasConversation =
    messages.length > 0;

  /* =======================================================
     RESET WHEN DOCUMENT CHANGES
  ======================================================= */

  useEffect(() => {
    setActiveId(null);
    setInputText("");
    setMessages([]);
    setLoading(false);
    setError("");
    setSourcePage(null);
    setCopiedId(null);
    setHistoryOpen(false);
  }, [document.document_id]);

  /* =======================================================
     NEW CHAT
  ======================================================= */

  function resetChat() {
    setActiveId(null);
    setInputText("");
    setMessages([]);
    setLoading(false);
    setError("");
    setSourcePage(null);
    setCopiedId(null);
    setHistoryOpen(false);

    setTimeout(() => {
      textareaRef.current?.focus();
    }, 80);
  }

  /* =======================================================
     SELECT SAVED CHAT
  ======================================================= */

  function selectHistory(id) {
    const item = history.find(
      (entry) => entry.id === id
    );

    if (!item) {
      return;
    }

    const restoredMessages =
      Array.isArray(item.messages)
        ? item.messages.map(
            (message) => ({
              ...message,
              loading: false,
            })
          )
        : [];

    setActiveId(item.id);

    /*
     * IMPORTANT:
     *
     * We restore the conversation into
     * messages, NOT into inputText.
     *
     * Therefore the textarea stays empty.
     */
    setMessages(restoredMessages);

    setInputText("");
    setError("");
    setCopiedId(null);
    setHistoryOpen(false);

    /*
     * If the last message has a source,
     * show its first source page.
     */
    const lastMessage =
      restoredMessages[
        restoredMessages.length - 1
      ];

    const firstSource =
      lastMessage?.sources?.[0];

    setSourcePage(
      firstSource?.page || null
    );
  }

  /* =======================================================
     DELETE CHAT
  ======================================================= */

  function deleteChat(id) {
    const next = history.filter(
      (item) => item.id !== id
    );

    setHistory(next);
    saveHistory(next);

    if (activeId === id) {
      resetChat();
    }
  }

  /* =======================================================
     CLEAR HISTORY
  ======================================================= */

  function clearHistory() {
    if (!documentHistory.length) {
      return;
    }

    if (
      !window.confirm(
        "Clear all saved chat history for this document?"
      )
    ) {
      return;
    }

    const next = history.filter(
      (item) =>
        item.document?.document_id !==
        document.document_id
    );

    setHistory(next);
    saveHistory(next);

    resetChat();
  }

  /* =======================================================
     SAVE CURRENT CONVERSATION
  ======================================================= */

  function saveConversation(
    conversationId,
    conversationMessages,
    firstQuestion
  ) {
    const existing =
      history.find(
        (item) =>
          item.id === conversationId
      );

    const createdAt =
      existing?.createdAt ||
      Date.now();

    const record = {
      id: conversationId,

      title:
        existing?.title ||
        firstQuestion.slice(0, 70),

      messages: conversationMessages,

      document,

      createdAt,

      timeLabel:
        existing?.timeLabel ||
        new Date(
          createdAt
        ).toLocaleString([], {
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
        }),
    };

    const nextHistory = [
      record,
      ...history.filter(
        (item) =>
          item.id !==
          conversationId
      ),
    ].slice(0, 50);

    setHistory(nextHistory);
    saveHistory(nextHistory);
  }

  /* =======================================================
     ASK QUESTION
  ======================================================= */

  async function askQuestion(e) {
    e?.preventDefault();

    /*
     * Read from input ONLY.
     */
    const q = inputText.trim();

    if (!q || loading) {
      return;
    }

    /*
     * IMPORTANT:
     *
     * Clear ONLY the input box.
     *
     * This does NOT touch messages.
     */
    setInputText("");

    setError("");
    setLoading(true);
    setCopiedId(null);

    /*
     * Create a new conversation if needed.
     */
    const conversationId =
      activeId ||
      `chat-${Date.now()}-${Math.random()
        .toString(36)
        .slice(2, 8)}`;

    if (!activeId) {
      setActiveId(conversationId);
    }

    /*
     * Create a temporary message immediately.
     *
     * This means Question 1 stays visible
     * even while the backend is processing it.
     */
    const messageId = `message-${Date.now()}-${Math.random()
      .toString(36)
      .slice(2, 8)}`;

    const pendingMessage = {
      id: messageId,
      question: q,
      answer: "",
      sources: [],
      chunks: [],
      loading: true,
      error: "",
    };

    /*
     * Preserve ALL previous messages.
     */
    const conversationWithPending = [
      ...messages,
      pendingMessage,
    ];

    setMessages(
      conversationWithPending
    );

    try {
      const response = await fetch(
        `${API_URL}/api/ask`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            question: q,
            top_k: 6,
            document_id:
              document.document_id,
          }),
        }
      );

      let data;

      try {
        data = await response.json();
      } catch {
        throw new Error(
          "The backend returned an invalid response."
        );
      }

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Unable to get an answer."
        );
      }

      const nextAnswer =
        data.answer ||
        "No answer was returned.";

      const nextSources =
        Array.isArray(data.sources)
          ? data.sources
          : [];

      const nextChunks =
        Array.isArray(
          data.retrieved_chunks
        )
          ? data.retrieved_chunks
          : [];

      /*
       * Replace ONLY the pending message.
       *
       * Previous messages remain untouched.
       */
      const completedMessage = {
        id: messageId,
        question: q,
        answer: nextAnswer,
        sources: nextSources,
        chunks: nextChunks,
        loading: false,
        error: "",
      };

      const finalMessages =
        conversationWithPending.map(
          (message) =>
            message.id === messageId
              ? completedMessage
              : message
        );

      setMessages(finalMessages);

      /*
       * Save the COMPLETE conversation.
       */
      saveConversation(
        conversationId,
        finalMessages,
        q
      );

      /*
       * Show the first citation page
       * for the newly answered question.
       */
      if (nextSources.length > 0) {
        setSourcePage(
          nextSources[0].page ||
            null
        );
      }
    } catch (err) {
      const messageText =
        err.message ||
        "The API could not be reached. Make sure FastAPI is running.";

      const failedMessage = {
        id: messageId,
        question: q,
        answer: "",
        sources: [],
        chunks: [],
        loading: false,
        error: messageText,
      };

      const finalMessages =
        conversationWithPending.map(
          (message) =>
            message.id === messageId
              ? failedMessage
              : message
        );

      setMessages(finalMessages);

      /*
       * Save the conversation even when
       * this particular question fails.
       */
      saveConversation(
        conversationId,
        finalMessages,
        q
      );

      setError(messageText);
    } finally {
      setLoading(false);

      /*
       * Put cursor back into the EMPTY input.
       */
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 50);
    }
  }

  /* =======================================================
     COPY ANSWER
  ======================================================= */

  async function copyAnswer(
    messageId,
    answer
  ) {
    if (!answer) {
      return;
    }

    try {
      await navigator.clipboard.writeText(
        answer
      );

      setCopiedId(messageId);

      setTimeout(() => {
        setCopiedId(null);
      }, 1500);
    } catch {
      setError(
        "Unable to copy the answer."
      );
    }
  }

  /* =======================================================
     SOURCE PAGE
  ======================================================= */

  function handleSourceClick(source) {
    if (source?.page) {
      setSourcePage(source.page);
    }
  }

  function handleEvidenceClick(chunk) {
    if (chunk?.page) {
      setSourcePage(chunk.page);
    }
  }

  /* =======================================================
     QUICK QUESTION
  ======================================================= */

  function useQuickQuestion(text) {
    setInputText(text);

    setTimeout(() => {
      textareaRef.current?.focus();
    }, 50);
  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (
    <div className="app-shell workspace-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="topbar workspace-topbar">
        <div className="workspace-brand-left">
          <button
            className="home-button"
            onClick={onChangeDocument}
            type="button"
            title="Upload another PDF"
          >
            <Icon
              name="home"
              size={17}
            />
          </button>

          <Brand />
        </div>

        <div className="workspace-header-right">
          <div className="document-pill">
            <Icon
              name="file"
              size={14}
            />

            {document.document_name}
          </div>

          <div className="status-pill">
            <span className="status-dot" />
            Ready
          </div>
        </div>
      </header>

      {/* =================================================
          MAIN WORKSPACE
      ================================================= */}

      <main className="workspace-main">

        {/* LEFT SIDE — PDF */}
        <PdfViewer
          document={document}
          page={sourcePage}
          onBack={onChangeDocument}
        />

        {/* RIGHT SIDE — CHAT */}
        <section className="chat-panel">

          {/* CHAT HEADER */}
          <div className="chat-panel-head">
            <div>
              <div className="panel-kicker">
                DOCUMENT CHAT
              </div>

              <h1>
                Ask about this PDF
              </h1>
            </div>

            <div className="chat-actions">
              <button
                className="new-chat-button"
                onClick={resetChat}
                type="button"
              >
                <Icon
                  name="plus"
                  size={15}
                />

                New chat
              </button>

              <button
                className="history-button"
                onClick={() =>
                  setHistoryOpen(true)
                }
                type="button"
              >
                <Icon
                  name="history"
                  size={15}
                />

                History

                <span>
                  {documentHistory.length}
                </span>
              </button>
            </div>
          </div>

          {/* HISTORY OVERLAY */}
          {historyOpen && (
            <div className="history-overlay">
              <HistoryPanel
                history={
                  documentHistory
                }
                activeId={activeId}
                onSelect={
                  selectHistory
                }
                onDelete={
                  deleteChat
                }
                onClear={
                  clearHistory
                }
                onNewChat={
                  resetChat
                }
                onClose={() =>
                  setHistoryOpen(false)
                }
              />
            </div>
          )}

          {/* =================================================
              CHAT CONTENT
          ================================================= */}

          <div className="chat-content">

            {/* EMPTY CHAT */}
            {!hasConversation ? (
              <div className="chat-empty-state">
                <div className="chat-empty-icon">
                  <Icon
                    name="search"
                    size={25}
                  />
                </div>

                <h2>
                  Ask anything in this document
                </h2>

                <p>
                  Questions are answered only
                  from the uploaded PDF.
                  Retrieved evidence is shown
                  with document, page, and
                  section citations.
                </p>

                <div className="quick-questions">
                  <button
                    onClick={() =>
                      useQuickQuestion(
                        "What are the main fees or payment terms?"
                      )
                    }
                    type="button"
                  >
                    What are the main fees
                    or payment terms?
                  </button>

                  <button
                    onClick={() =>
                      useQuickQuestion(
                        "What are the key obligations in this document?"
                      )
                    }
                    type="button"
                  >
                    What are the key
                    obligations?
                  </button>

                  <button
                    onClick={() =>
                      useQuickQuestion(
                        "What happens if the agreement is terminated?"
                      )
                    }
                    type="button"
                  >
                    What happens on
                    termination?
                  </button>
                </div>
              </div>
            ) : (

              /* =================================================
                 CONTINUOUS CHAT
              ================================================= */

              <div className="chat-results">

                {messages.map(
                  (message) => (
                    <ChatMessage
                      key={message.id}
                      message={message}
                      onSourceClick={
                        handleSourceClick
                      }
                      onEvidenceClick={
                        handleEvidenceClick
                      }
                      onCopy={
                        copyAnswer
                      }
                      copiedId={
                        copiedId
                      }
                    />
                  )
                )}

                {error && !messages.some(
                  (message) =>
                    message.error ===
                    error
                ) && (
                  <div className="answer-box error-box">
                    <strong>
                      Unable to complete
                      the request
                    </strong>

                    <p>{error}</p>
                  </div>
                )}

              </div>
            )}
          </div>

          {/* =================================================
              INPUT COMPOSER
          ================================================= */}

          <form
            className="chat-composer"
            onSubmit={askQuestion}
          >
            <div className="composer-search">
              <Icon
                name="search"
                size={19}
              />
            </div>

            <textarea
              ref={textareaRef}

              /*
               * IMPORTANT:
               *
               * This is inputText only.
               *
               * It has NO connection to
               * messages[0].question,
               * messages[1].question, etc.
               */
              value={inputText}

              onChange={(e) =>
                setInputText(
                  e.target.value
                )
              }

              placeholder="Ask a question about this document..."

              rows={1}

              onKeyDown={(e) => {
                if (
                  e.key === "Enter" &&
                  !e.shiftKey
                ) {
                  e.preventDefault();
                  askQuestion(e);
                }
              }}
            />

            <button
              className="ask-button"
              disabled={
                !inputText.trim() ||
                loading
              }
              type="submit"
            >
              {loading ? (
                <span className="button-spinner" />
              ) : (
                <Icon
                  name="send"
                  size={15}
                />
              )}

              {loading
                ? "Searching"
                : "Ask"}
            </button>
          </form>

          <div className="composer-hint">
            Enter to ask · Shift + Enter
            for a new line · Answers are
            grounded in the uploaded PDF
          </div>
        </section>
      </main>
    </div>
  );
}

/* =========================================================
   APP
========================================================= */

function App() {
  const [document, setDocument] =
    useState(loadActiveDocument);

  const [history, setHistory] =
    useState(loadHistory);

  useEffect(() => {
    saveHistory(history);
  }, [history]);

  useEffect(() => {
    saveActiveDocument(document);
  }, [document]);

  function handleUploaded(data) {
    setDocument(data);
  }

  function changeDocument() {
    setDocument(null);
  }

  return document ? (
    <ChatWorkspace
      document={document}
      history={history}
      setHistory={setHistory}
      onChangeDocument={
        changeDocument
      }
    />
  ) : (
    <UploadPage
      onUploaded={handleUploaded}
    />
  );
}

/* =========================================================
   START APP
========================================================= */

createRoot(
  document.getElementById("root")
).render(<App />);