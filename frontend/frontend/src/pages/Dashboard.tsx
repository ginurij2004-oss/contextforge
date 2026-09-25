import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";

import {
  useNavigate,
} from "react-router-dom";

import {
  createConversation,
  deleteConversation,
  getConversations,
  getMessages,
  renameConversation,
  sendChatMessage,
  type ChatMessage,
  type ChatMode,
  type Conversation,
} from "../services/chat";

import {
  getDocuments,
  type DocumentItem,
} from "../services/documents";

import {
  useTheme,
} from "../theme/ThemeContext";

import {
  useAuth,
} from "../context/AuthContext";

import {
  useVoiceRecorder,
} from "../hooks/useVoiceRecorder";

import {
  transcribeVoice,
} from "../services/voice";

import AICompanion from "../components/AICompanion";
import "../components/AICompanion.css";

import "./Dashboard.css";


export default function Dashboard() {

  const navigate =
    useNavigate();


  const {
    theme,
    setTheme,
  } = useTheme();


  const {
    logout,
  } = useAuth();


  const bottomRef =
    useRef<HTMLDivElement | null>(
      null
    );


  const [
    conversations,
    setConversations,
  ] = useState<Conversation[]>([]);


  const [
    conversationId,
    setConversationId,
  ] = useState<number | null>(
    null
  );


  const [
    messages,
    setMessages,
  ] = useState<ChatMessage[]>([]);


  const [
    documents,
    setDocuments,
  ] = useState<DocumentItem[]>([]);


  const [
    mode,
    setMode,
  ] = useState<ChatMode>(
    "chat"
  );


  const [
    selectedDocumentId,
    setSelectedDocumentId,
  ] = useState<number | null>(
    null
  );


  const [
    input,
    setInput,
  ] = useState("");


  // ======================================================
  // Voice Input
  // ======================================================

  const [
    voiceProcessing,
    setVoiceProcessing,
  ] = useState(false);


  const [
    voiceError,
    setVoiceError,
  ] = useState("");


  const handleVoiceReady =
    async (
      audioBlob: Blob
    ) => {

      try {

        setVoiceProcessing(
          true
        );

        setVoiceError("");


        const transcript =
          await transcribeVoice(
            audioBlob
          );


        const cleaned =
          transcript.trim();


        if (
          !cleaned
        ) {

          setVoiceError(
            "No speech was detected. Please try again."
          );

          return;

        }


        setInput(
          (
            previous
          ) => {

            const existing =
              previous.trim();


            if (
              !existing
            ) {

              return cleaned;

            }


            return (
              `${existing} ${cleaned}`
            );

          }
        );


      } catch (error: any) {

        console.error(
          "VOICE TRANSCRIPTION ERROR:",
          error
        );


        setVoiceError(
          error?.response
            ?.data
            ?.detail
          || "Could not transcribe your voice."
        );


      } finally {

        setVoiceProcessing(
          false
        );

      }

    };


  const {
    isSupported:
      voiceSupported,

    isRecording,

    error:
      recorderError,

    startRecording,

    stopRecording,
  } = useVoiceRecorder({

    onRecordingReady:
      handleVoiceReady,

    silenceTimeoutMs:
      1400,

    maxRecordingMs:
      30000,

  });


  const handleVoiceToggle =
    () => {

      if (
        isRecording
      ) {

        stopRecording();

        return;

      }


      setVoiceError("");

      startRecording();

    };


  const [
    loading,
    setLoading,
  ] = useState(false);


  const [
    initialLoading,
    setInitialLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  const [
    mobileSidebarOpen,
    setMobileSidebarOpen,
  ] = useState(false);


  // ======================================================
  // Conversation Menu State
  // ======================================================

  const [
    menuConversationId,
    setMenuConversationId,
  ] = useState<number | null>(
    null
  );


  const [
    editingConversationId,
    setEditingConversationId,
  ] = useState<number | null>(
    null
  );


  const [
    editingTitle,
    setEditingTitle,
  ] = useState("");


  const [
    renaming,
    setRenaming,
  ] = useState(false);


  const [
    conversationToDelete,
    setConversationToDelete,
  ] = useState<Conversation | null>(
    null
  );


  const [
    deleting,
    setDeleting,
  ] = useState(false);


  // ======================================================
  // Initial Load
  // ======================================================

  useEffect(() => {

    initialize();

  }, []);


  // ======================================================
  // Auto Scroll
  // ======================================================

  useEffect(() => {

    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });

  }, [
    messages,
    loading,
  ]);


  // ======================================================
  // Close Conversation Menu
  // ======================================================

  useEffect(() => {

    if (
      menuConversationId === null
    ) {

      return;

    }


    const handleOutsideClick =
      (
        event: MouseEvent
      ) => {

        const target =
          event.target as HTMLElement;


        if (
          target.closest(
            ".cf-conversation-menu-area"
          )
        ) {

          return;

        }


        setMenuConversationId(
          null
        );

      };


    document.addEventListener(
      "mousedown",
      handleOutsideClick
    );


    return () => {

      document.removeEventListener(
        "mousedown",
        handleOutsideClick
      );

    };

  }, [
    menuConversationId,
  ]);


  // ======================================================
  // Escape Delete Modal
  // ======================================================

  useEffect(() => {

    if (
      !conversationToDelete
    ) {

      return;

    }


    const handleKeyDown =
      (
        event: KeyboardEvent
      ) => {

        if (
          event.key === "Escape"
        ) {

          setConversationToDelete(
            null
          );

        }

      };


    document.addEventListener(
      "keydown",
      handleKeyDown
    );


    return () => {

      document.removeEventListener(
        "keydown",
        handleKeyDown
      );

    };

  }, [
    conversationToDelete,
  ]);


  // ======================================================
  // Initialize
  // ======================================================

  const initialize =
    async () => {

      try {

        setInitialLoading(
          true
        );

        setError("");


        const [
          conversationData,
          documentData,
        ] = await Promise.all([
          getConversations(),
          getDocuments(),
        ]);


        setConversations(
          conversationData
        );


        setDocuments(
          documentData.filter(
            (
              document
            ) =>
              document.status
              === "ready"
          )
        );


        if (
          conversationData.length > 0
        ) {

          const firstConversation =
            conversationData[0];


          setConversationId(
            firstConversation.id
          );


          const messageData =
            await getMessages(
              firstConversation.id
            );


          setMessages(
            messageData
          );


          restoreConversationMode(
            messageData
          );

        }


      } catch (error) {

        console.error(
          "DASHBOARD INIT ERROR:",
          error
        );


        setError(
          "Failed to load ContextForge."
        );


      } finally {

        setInitialLoading(
          false
        );

      }

    };


  // ======================================================
  // Restore Mode
  // ======================================================

  const restoreConversationMode =
    (
      data: ChatMessage[]
    ) => {

      if (
        data.length === 0
      ) {

        return;

      }


      const latest =
        data[
          data.length - 1
        ];


      if (
        latest.mode
      ) {

        setMode(
          latest.mode
        );

      }


      setSelectedDocumentId(
        latest.document_id
        ?? null
      );

    };


  // ======================================================
  // Open Conversation
  // ======================================================

  const openConversation =
    async (
      id: number
    ) => {

      if (
        editingConversationId
        === id
      ) {

        return;

      }


      try {

        setError("");

        setMenuConversationId(
          null
        );


        setConversationId(
          id
        );


        const data =
          await getMessages(
            id
          );


        setMessages(
          data
        );


        restoreConversationMode(
          data
        );


        setMobileSidebarOpen(
          false
        );


      } catch (error) {

        console.error(
          "LOAD CONVERSATION ERROR:",
          error
        );


        setError(
          "Failed to load conversation."
        );

      }

    };


  // ======================================================
  // Create Conversation
  // ======================================================

  const handleNewConversation =
    async () => {

      try {

        setError("");

        setMenuConversationId(
          null
        );


        const conversation =
          await createConversation();


        setConversations(
          (
            previous
          ) => [
            conversation,
            ...previous,
          ]
        );


        setConversationId(
          conversation.id
        );


        setMessages([]);

        setInput("");

        setMode(
          "chat"
        );


        setSelectedDocumentId(
          null
        );


        setMobileSidebarOpen(
          false
        );


      } catch (error) {

        console.error(
          "CREATE CONVERSATION ERROR:",
          error
        );


        setError(
          "Failed to create conversation."
        );

      }

    };


  // ======================================================
  // Start Rename
  // ======================================================

  const startRename =
    (
      conversation: Conversation
    ) => {

      setMenuConversationId(
        null
      );


      setEditingConversationId(
        conversation.id
      );


      setEditingTitle(
        conversation.title
      );

    };


  // ======================================================
  // Cancel Rename
  // ======================================================

  const cancelRename =
    () => {

      setEditingConversationId(
        null
      );

      setEditingTitle("");

    };


  // ======================================================
  // Save Rename
  // ======================================================

  const saveRename =
    async (
      conversationIdToRename: number
    ) => {

      const cleanedTitle =
        editingTitle.trim();


      if (
        !cleanedTitle
        || renaming
      ) {

        return;

      }


      try {

        setRenaming(
          true
        );

        setError("");


        const updatedConversation =
          await renameConversation(
            conversationIdToRename,
            cleanedTitle
          );


        setConversations(
          (
            previous
          ) =>
            previous.map(
              (
                conversation
              ) => {

                if (
                  conversation.id
                  === updatedConversation.id
                ) {

                  return updatedConversation;

                }


                return conversation;

              }
            )
        );


        setEditingConversationId(
          null
        );


        setEditingTitle("");


      } catch (error: any) {

        console.error(
          "RENAME CONVERSATION ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Failed to rename conversation."
        );


      } finally {

        setRenaming(
          false
        );

      }

    };


  // ======================================================
  // Ask Delete
  // ======================================================

  const requestDelete =
    (
      conversation: Conversation
    ) => {

      setMenuConversationId(
        null
      );


      setConversationToDelete(
        conversation
      );

    };


  // ======================================================
  // Confirm Delete
  // ======================================================

  const confirmDelete =
    async () => {

      if (
        !conversationToDelete
        || deleting
      ) {

        return;

      }


      const deletedId =
        conversationToDelete.id;


      try {

        setDeleting(
          true
        );

        setError("");


        await deleteConversation(
          deletedId
        );


        const remainingConversations =
          conversations.filter(
            (
              conversation
            ) =>
              conversation.id
              !== deletedId
          );


        setConversations(
          remainingConversations
        );


        setConversationToDelete(
          null
        );


        // --------------------------------------------------
        // If active conversation was deleted
        // --------------------------------------------------

        if (
          conversationId
          === deletedId
        ) {

          if (
            remainingConversations.length
            > 0
          ) {

            const nextConversation =
              remainingConversations[0];


            setConversationId(
              nextConversation.id
            );


            const nextMessages =
              await getMessages(
                nextConversation.id
              );


            setMessages(
              nextMessages
            );


            restoreConversationMode(
              nextMessages
            );

          } else {

            setConversationId(
              null
            );

            setMessages([]);

            setMode(
              "chat"
            );

            setSelectedDocumentId(
              null
            );

          }

        }


      } catch (error: any) {

        console.error(
          "DELETE CONVERSATION ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Failed to delete conversation."
        );


      } finally {

        setDeleting(
          false
        );

      }

    };


  // ======================================================
  // Send Message
  // ======================================================

  const handleSubmit =
    async (
      event: FormEvent
    ) => {

      event.preventDefault();


      if (
        isRecording
      ) {

        stopRecording();

        return;

      }


      const content =
        input.trim();


      if (
        !content
        || loading
      ) {

        return;

      }


      try {

        setLoading(
          true
        );

        setError("");


        let activeConversationId =
          conversationId;


        if (
          activeConversationId
          === null
        ) {

          const newConversation =
            await createConversation();


          activeConversationId =
            newConversation.id;


          setConversationId(
            newConversation.id
          );


          setConversations(
            (
              previous
            ) => [
              newConversation,
              ...previous,
            ]
          );

        }


        setInput("");


        const response =
          await sendChatMessage(

            activeConversationId,

            content,

            mode,

            mode === "chat"
              ? null
              : selectedDocumentId
          );


        setMessages(
          (
            previous
          ) => [

            ...previous,

            response.user_message,

            response.assistant_message,

          ]
        );


        const updated =
          await getConversations();


        setConversations(
          updated
        );


      } catch (error: any) {

        console.error(
          "SEND MESSAGE ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Failed to send message."
        );


      } finally {

        setLoading(
          false
        );

      }

    };


  // ======================================================
  // Change Mode
  // ======================================================

  const changeMode =
    (
      newMode: ChatMode
    ) => {

      setMode(
        newMode
      );


      if (
        newMode === "chat"
      ) {

        setSelectedDocumentId(
          null
        );

      }

    };


  // ======================================================
  // Logout
  // ======================================================

  const handleLogout =
    () => {

      logout();

      navigate(
        "/login"
      );

    };


  // ======================================================
  // Loading
  // ======================================================

  if (
    initialLoading
  ) {

    return (

      <div className="cf-dashboard-loading">

        <div className="cf-dashboard-loading-logo">

          C

        </div>

        <span>
          Preparing your workspace...
        </span>

      </div>

    );

  }


  return (

    <div className="cf-dashboard">


      {/* =================================================
          Mobile Overlay
      ================================================= */}

      {
        mobileSidebarOpen
        && (

          <button
            type="button"

            className="cf-mobile-overlay"

            onClick={() =>
              setMobileSidebarOpen(
                false
              )
            }
          />

        )
      }


      {/* =================================================
          Sidebar
      ================================================= */}

      <aside
        className={
          mobileSidebarOpen
          ? "cf-sidebar cf-sidebar-open"
          : "cf-sidebar"
        }
      >


        <div className="cf-sidebar-brand">

          <div className="cf-sidebar-logo">
            C
          </div>


          <div className="cf-sidebar-brand-copy">

            <strong>
              ContextForge
            </strong>

            <span>
              Enterprise AI
            </span>

          </div>


          <button
            type="button"

            className="cf-sidebar-mobile-close"

            onClick={() =>
              setMobileSidebarOpen(
                false
              )
            }
          >
            ×
          </button>

        </div>


        <button
          type="button"

          className="cf-new-chat"

          onClick={
            handleNewConversation
          }
        >

          <span className="cf-new-chat-icon">
            +
          </span>

          New conversation

        </button>


        <nav className="cf-sidebar-nav">


          <button
            type="button"
            className="active"
          >

            <span className="cf-nav-icon">
              ✦
            </span>

            AI Workspace

          </button>


          <button
            type="button"

            onClick={() =>
              navigate(
                "/documents"
              )
            }
          >

            <span className="cf-nav-icon">
              ◫
            </span>

            Documents

          </button>


          <button
            type="button"

            onClick={() =>
              navigate(
                "/analytics"
              )
            }
          >

            <span className="cf-nav-icon">
              ◩
            </span>

            Analytics

          </button>


          <button
            type="button"

            onClick={() =>
              navigate(
                "/actions"
              )
            }
          >

            <span className="cf-nav-icon">
              ⚡
            </span>

            Action Center

          </button>


          <button
            type="button"

            onClick={() =>
              navigate(
                "/automations"
              )
            }
          >

            <span className="cf-nav-icon">
              ⟳
            </span>

            Automations

          </button>


          <button
            type="button"

            onClick={() =>
              navigate(
                "/operations"
              )
            }
          >

            <span className="cf-nav-icon">
              ◎
            </span>

            Operations

          </button>


        </nav>


        <div className="cf-sidebar-section-title">

          Recent conversations

        </div>


        {/* =================================================
            Conversation List
        ================================================= */}

        <div className="cf-conversation-list">


          {
            conversations.length
            === 0
            ? (

              <div className="cf-no-conversations">

                Start your first conversation.

              </div>

            )
            : (

              conversations.map(
                (
                  conversation
                ) => {

                  const isEditing =
                    editingConversationId
                    === conversation.id;


                  return (

                    <div
                      key={
                        conversation.id
                      }

                      className={
                        (
                          conversationId
                          === conversation.id

                          ? "cf-conversation-wrapper active"

                          : "cf-conversation-wrapper"
                        )
                      }
                    >


                      {
                        isEditing
                        ? (

                          /* =================================
                             Inline Rename
                          ================================= */

                          <div className="cf-conversation-rename">


                            <input
                              autoFocus

                              value={
                                editingTitle
                              }

                              maxLength={120}

                              onChange={
                                (
                                  event
                                ) =>
                                  setEditingTitle(
                                    event.target.value
                                  )
                              }

                              onKeyDown={
                                (
                                  event
                                ) => {

                                  if (
                                    event.key
                                    === "Enter"
                                  ) {

                                    event.preventDefault();


                                    saveRename(
                                      conversation.id
                                    );

                                  }


                                  if (
                                    event.key
                                    === "Escape"
                                  ) {

                                    cancelRename();

                                  }

                                }
                              }
                            />


                            <button
                              type="button"

                              className="cf-rename-save"

                              disabled={
                                renaming
                                || !editingTitle.trim()
                              }

                              onClick={() =>
                                saveRename(
                                  conversation.id
                                )
                              }
                            >

                              {
                                renaming
                                ? "..."
                                : "✓"
                              }

                            </button>


                            <button
                              type="button"

                              className="cf-rename-cancel"

                              onClick={
                                cancelRename
                              }
                            >
                              ×
                            </button>


                          </div>

                        )
                        : (

                          <>
                            {/* Main Conversation Button */}

                            <button
                              type="button"

                              className="cf-conversation-main"

                              onClick={() =>
                                openConversation(
                                  conversation.id
                                )
                              }
                            >

                              <span className="cf-conversation-dot">
                                ◌
                              </span>


                              <span className="cf-conversation-name">

                                {
                                  conversation.title
                                }

                              </span>

                            </button>


                            {/* Three Dot Menu */}

                            <div className="cf-conversation-menu-area">


                              <button
                                type="button"

                                className="cf-conversation-menu-button"

                                aria-label="Conversation options"

                                onClick={
                                  (
                                    event
                                  ) => {

                                    event.stopPropagation();


                                    setMenuConversationId(
                                      (
                                        current
                                      ) =>
                                        current
                                        === conversation.id

                                        ? null

                                        : conversation.id
                                    );

                                  }
                                }
                              >

                                •••

                              </button>


                              {
                                menuConversationId
                                === conversation.id
                                && (

                                  <div className="cf-conversation-menu">


                                    <button
                                      type="button"

                                      onClick={() =>
                                        startRename(
                                          conversation
                                        )
                                      }
                                    >

                                      <span>
                                        ✎
                                      </span>

                                      Rename

                                    </button>


                                    <button
                                      type="button"

                                      className="danger"

                                      onClick={() =>
                                        requestDelete(
                                          conversation
                                        )
                                      }
                                    >

                                      <span>
                                        ♢
                                      </span>

                                      Delete

                                    </button>


                                  </div>

                                )
                              }


                            </div>

                          </>

                        )
                      }


                    </div>

                  );

                }
              )

            )
          }


        </div>


        <div className="cf-sidebar-footer">


          <div className="cf-system-online">

            <span className="cf-online-dot" />

            ContextForge online

          </div>


          <button
            type="button"

            onClick={
              handleLogout
            }
          >

            <span className="cf-nav-icon">
              ↗
            </span>

            Sign out

          </button>


        </div>


      </aside>


      {/* =================================================
          Workspace
      ================================================= */}

      <main className="cf-workspace">


        <header className="cf-workspace-header">


          <div className="cf-header-left">


            <button
              type="button"

              className="cf-mobile-menu"

              onClick={() =>
                setMobileSidebarOpen(
                  true
                )
              }
            >
              ☰
            </button>


            <div>

              <span className="cf-header-eyebrow">
                Workspace
              </span>


              <h1>
                AI Workspace
              </h1>


              <p>
                Turn knowledge into answers,
                insights and actions.
              </p>

            </div>


          </div>


          <div className="cf-theme-toggle">


            <button
              type="button"

              className={
                theme === "dark"
                ? "active"
                : ""
              }

              onClick={() =>
                setTheme(
                  "dark"
                )
              }
            >

              Dark

            </button>


            <button
              type="button"

              className={
                theme === "light"
                ? "active"
                : ""
              }

              onClick={() =>
                setTheme(
                  "light"
                )
              }
            >

              Light

            </button>


          </div>


        </header>


        {/* =================================================
            Mode Toolbar
        ================================================= */}

        <div className="cf-workspace-toolbar">


          <div className="cf-mode-tabs">


            <button
              type="button"

              className={
                mode === "chat"
                ? "active"
                : ""
              }

              onClick={() =>
                changeMode(
                  "chat"
                )
              }
            >

              <span>
                ✦
              </span>

              General AI

            </button>


            <button
              type="button"

              className={
                mode === "documents"
                ? "active"
                : ""
              }

              onClick={() =>
                changeMode(
                  "documents"
                )
              }
            >

              <span>
                ◫
              </span>

              Knowledge

            </button>


            <button
              type="button"

              className={
                mode === "agent"
                ? "active agent"
                : ""
              }

              onClick={() =>
                changeMode(
                  "agent"
                )
              }
            >

              <span>
                ⚡
              </span>

              Agent

            </button>


          </div>


          {
            mode !== "chat"
            && (

              <KnowledgeDropdown
                documents={
                  documents
                }

                selectedDocumentId={
                  selectedDocumentId
                }

                onSelect={
                  setSelectedDocumentId
                }
              />

            )
          }


        </div>


        {/* =================================================
            Messages
        ================================================= */}

        <section className="cf-messages">


          <div className="cf-messages-inner">


            {
              messages.length
              === 0
              ? (

                <WorkspaceEmptyState
                  mode={
                    mode
                  }
                />

              )
              : (

                messages.map(
                  (
                    message
                  ) => (

                    <ChatMessageCard
                      key={
                        message.id
                      }

                      message={
                        message
                      }
                    />

                  )
                )

              )
            }


            {
              loading
              && (

                <div className="cf-thinking-message">

                  <div className="cf-ai-avatar">
                    C
                  </div>


                  <div className="cf-thinking-content">

                    <span>
                      ContextForge is thinking
                    </span>


                    <div className="cf-thinking-dots">

                      <i />
                      <i />
                      <i />

                    </div>

                  </div>

                </div>

              )
            }


            <div
              ref={
                bottomRef
              }
            />


          </div>


        </section>


        {/* =================================================
            Error
        ================================================= */}

        {
          error
          && (

            <div className="cf-chat-error">

              <strong>
                !
              </strong>

              <span>
                {
                  error
                }
              </span>

            </div>

          )
        }


        {/* =================================================
            Composer
        ================================================= */}

        <footer className="cf-composer-area">


          <div className="cf-composer-container">


            <form
              className="cf-composer"

              onSubmit={
                handleSubmit
              }
            >


              <div className="cf-composer-icon">

                {
                  mode === "agent"
                  ? "⚡"
                  : (
                      mode
                      === "documents"
                      ? "◫"
                      : "✦"
                    )
                }

              </div>


              <textarea
                value={
                  input
                }

                onChange={
                  (
                    event
                  ) =>
                    setInput(
                      event.target.value
                    )
                }

                onKeyDown={
                  (
                    event
                  ) => {

                    if (
                      event.key
                      === "Enter"

                      &&

                      !event.shiftKey
                    ) {

                      event.preventDefault();


                      event.currentTarget
                        .form
                        ?.requestSubmit();

                    }

                  }
                }

                placeholder={
                  getInputPlaceholder(
                    mode
                  )
                }

                rows={1}

                disabled={
                  loading
                }
              />


              <button
                type="button"

                className={
                  isRecording
                  ? "cf-voice-button recording"
                  : "cf-voice-button"
                }

                onClick={
                  handleVoiceToggle
                }

                disabled={
                  loading
                  || voiceProcessing
                  || !voiceSupported
                }

                title={
                  !voiceSupported
                  ? "Voice recording is not supported in this browser"
                  : (
                      isRecording
                      ? "Stop recording"
                      : "Start voice input"
                    )
                }

                aria-label={
                  isRecording
                  ? "Stop voice recording"
                  : "Start voice recording"
                }
              >

                {
                  voiceProcessing
                  ? (
                      <span className="cf-voice-spinner" />
                    )
                  : (
                      isRecording
                      ? (
                          <svg
                            viewBox="0 0 24 24"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <rect
                              x="7"
                              y="7"
                              width="10"
                              height="10"
                              rx="2"
                            />
                          </svg>
                        )
                      : (
                          <svg
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.9"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            aria-hidden="true"
                          >
                            <rect
                              x="9"
                              y="3"
                              width="6"
                              height="11"
                              rx="3"
                            />

                            <path
                              d="M5.5 10.5a6.5 6.5 0 0 0 13 0"
                            />

                            <path
                              d="M12 17v4"
                            />

                            <path
                              d="M9 21h6"
                            />
                          </svg>
                        )
                    )
                }

              </button>


              <button
                type="submit"

                className="cf-send-button"

                disabled={
                  loading
                  || voiceProcessing
                  || isRecording
                  || !input.trim()
                }

                title={
                  input.trim()
                  ? "Send message"
                  : "Type or speak a message first"
                }
              >

                <span className="cf-send-label">
                  Send
                </span>

                <span className="cf-send-arrow">
                  ↑
                </span>

              </button>


            </form>


            <div className="cf-composer-meta">


              {
                isRecording
                && (
                  <span className="cf-voice-status">
                    <i />
                    Listening...
                  </span>
                )
              }


              {
                voiceProcessing
                && (
                  <span className="cf-voice-processing">
                    Transcribing speech...
                  </span>
                )
              }


              {
                (
                  voiceError
                  || recorderError
                )
                && !isRecording
                && !voiceProcessing
                && (
                  <span className="cf-voice-error">
                    {
                      voiceError
                      || recorderError
                    }
                  </span>
                )
              }


              <span>

                {
                  mode === "chat"
                  ? "✦ General AI"
                  : (
                      mode === "documents"
                      ? "◫ Grounded knowledge mode"
                      : "⚡ Agent tools enabled"
                    )
                }

              </span>


              {
                mode !== "chat"
                && (

                  <span>

                    {
                      selectedDocumentId
                      ? "Selected document only"
                      : "All documents"
                    }

                  </span>

                )
              }


            </div>


          </div>


        </footer>


      </main>


      {/* =================================================
          Delete Confirmation Modal
      ================================================= */}

      {
        conversationToDelete
        && (

          <div className="cf-delete-modal-overlay">


            <div className="cf-delete-modal">


              <div className="cf-delete-modal-icon">

                !

              </div>


              <h3>

                Delete conversation?

              </h3>


              <p>

                You are about to permanently delete{" "}

                <strong>
                  {
                    conversationToDelete.title
                  }
                </strong>

                . This will also delete its
                messages and saved source citations.

              </p>


              <div className="cf-delete-modal-warning">

                This action cannot be undone.

              </div>


              <div className="cf-delete-modal-actions">


                <button
                  type="button"

                  className="cf-delete-cancel"

                  disabled={
                    deleting
                  }

                  onClick={() =>
                    setConversationToDelete(
                      null
                    )
                  }
                >

                  Cancel

                </button>


                <button
                  type="button"

                  className="cf-delete-confirm"

                  disabled={
                    deleting
                  }

                  onClick={
                    confirmDelete
                  }
                >

                  {
                    deleting
                    ? "Deleting..."
                    : "Delete conversation"
                  }

                </button>


              </div>


            </div>


          </div>

        )
      }


    </div>

  );

}


// ==========================================================
// Knowledge Dropdown
// ==========================================================

function KnowledgeDropdown({
  documents,
  selectedDocumentId,
  onSelect,
}: {
  documents: DocumentItem[];
  selectedDocumentId: number | null;
  onSelect: (id: number | null) => void;
}) {

  const navigate =
    useNavigate();


  const [
    open,
    setOpen,
  ] = useState(false);


  const dropdownRef =
    useRef<HTMLDivElement | null>(
      null
    );


  const selected =
    documents.find(
      (
        document
      ) =>
        document.id
        === selectedDocumentId
    );


  useEffect(() => {

    const handleOutside =
      (
        event: MouseEvent
      ) => {

        if (
          dropdownRef.current

          &&

          !dropdownRef.current.contains(
            event.target as Node
          )
        ) {

          setOpen(
            false
          );

        }

      };


    document.addEventListener(
      "mousedown",
      handleOutside
    );


    return () => {

      document.removeEventListener(
        "mousedown",
        handleOutside
      );

    };

  }, []);


  return (

    <div
      className="cf-knowledge-dropdown"

      ref={
        dropdownRef
      }
    >


      <button
        type="button"

        className={
          open
          ? "cf-knowledge-trigger open"
          : "cf-knowledge-trigger"
        }

        onClick={() =>
          setOpen(
            (
              previous
            ) =>
              !previous
          )
        }
      >


        <div className="cf-knowledge-trigger-icon">
          ◫
        </div>


        <div className="cf-knowledge-trigger-text">

          <span>
            Knowledge source
          </span>


          <strong>

            {
              selected
              ? selected.filename
              : "All documents"
            }

          </strong>

        </div>


        <div
          className={
            open
            ? "cf-dropdown-arrow open"
            : "cf-dropdown-arrow"
          }
        >
          ⌄
        </div>


      </button>


      {
        open
        && (

          <div className="cf-knowledge-menu">


            <div className="cf-knowledge-menu-header">

              <strong>
                Select knowledge source
              </strong>

              <span>
                Choose where ContextForge should search.
              </span>

            </div>


            <div className="cf-knowledge-options">


              <button
                type="button"

                className={
                  selectedDocumentId
                  === null

                  ? "cf-knowledge-option selected"

                  : "cf-knowledge-option"
                }

                onClick={() => {

                  onSelect(
                    null
                  );

                  setOpen(
                    false
                  );

                }}
              >

                <div className="cf-option-icon all">
                  ✦
                </div>


                <div className="cf-option-text">

                  <strong>
                    All documents
                  </strong>

                  <span>
                    Search your complete knowledge base
                  </span>

                </div>


                {
                  selectedDocumentId
                  === null
                  && (

                    <div className="cf-option-check">
                      ✓
                    </div>

                  )
                }

              </button>


              {
                documents.length
                === 0
                ? (

                  <div className="cf-dropdown-empty">

                    No ready documents available.

                  </div>

                )
                : (

                  documents.map(
                    (
                      document
                    ) => {

                      const isSelected =
                        document.id
                        === selectedDocumentId;


                      return (

                        <button
                          type="button"

                          key={
                            document.id
                          }

                          className={
                            isSelected
                            ? "cf-knowledge-option selected"
                            : "cf-knowledge-option"
                          }

                          onClick={() => {

                            onSelect(
                              document.id
                            );

                            setOpen(
                              false
                            );

                          }}
                        >

                          <div className="cf-option-icon pdf">
                            PDF
                          </div>


                          <div className="cf-option-text">

                            <strong>
                              {
                                document.filename
                              }
                            </strong>

                            <span>
                              Ready for AI search
                            </span>

                          </div>


                          {
                            isSelected
                            && (

                              <div className="cf-option-check">
                                ✓
                              </div>

                            )
                          }

                        </button>

                      );

                    }
                  )

                )
              }


            </div>


            {/* ===============================================
                Upload Document Shortcut
            =============================================== */}

            <div className="cf-knowledge-menu-footer">


              <button
                type="button"

                className="cf-upload-document-option"

                onClick={() => {

                  setOpen(
                    false
                  );

                  navigate(
                    "/documents"
                  );

                }}
              >


                <div className="cf-upload-document-icon">

                  +

                </div>


                <div className="cf-upload-document-copy">

                  <strong>

                    Upload document

                  </strong>

                  <span>

                    Add a new PDF to your knowledge base

                  </span>

                </div>


                <span className="cf-upload-document-arrow">

                  →

                </span>


              </button>


            </div>


          </div>

        )
      }


    </div>

  );

}


// ==========================================================
// Empty State
// ==========================================================

function WorkspaceEmptyState({
  mode,
}: {
  mode: ChatMode;
}) {

  let icon = "✦";

  let eyebrow =
    "General AI";

  let title =
    "What can I help you with?";

  let description =
    (
      "Ask a question, explore an idea, "
      + "or use ContextForge as your AI workspace."
    );


  if (
    mode === "documents"
  ) {

    icon = "◫";

    eyebrow =
      "Knowledge";

    title =
      "Ask your knowledge base";

    description =
      (
        "Search your uploaded documents "
        + "and receive grounded answers with sources."
      );

  }


  if (
    mode === "agent"
  ) {

    icon = "⚡";

    eyebrow =
      "Agent";

    title =
      "Delegate the work";

    description =
      (
        "Search documents, analyze information "
        + "and turn insights into structured actions."
      );

  }


  return (

    <div className="cf-empty-workspace">

      <div className="cf-empty-companion">
        <AICompanion
          variant="workspace"
        />

        <span className="cf-empty-mode-icon">
          {
            icon
          }
        </span>
      </div>


      <span className="cf-empty-eyebrow">
        {
          eyebrow
        }
      </span>


      <h2>
        {
          title
        }
      </h2>


      <p>
        {
          description
        }
      </p>


      <div className="cf-empty-suggestions">


        {
          mode === "chat"
          && (
            <>
              <span>Explain a concept</span>
              <span>Brainstorm ideas</span>
              <span>Solve a problem</span>
            </>
          )
        }


        {
          mode === "documents"
          && (
            <>
              <span>Summarize a document</span>
              <span>Find a detail</span>
              <span>Compare information</span>
            </>
          )
        }


        {
          mode === "agent"
          && (
            <>
              <span>Analyze and recommend</span>
              <span>Identify problems</span>
              <span>Create an action plan</span>
            </>
          )
        }


      </div>

    </div>

  );

}


// ==========================================================
// Message Card
// ==========================================================

function ChatMessageCard({
  message,
}: {
  message: ChatMessage;
}) {

  const isAssistant =
    message.role
    === "assistant";


  const [
    copied,
    setCopied,
  ] = useState(false);


  const handleCopyResponse =
    async () => {

      try {

        await copyTextToClipboard(
          message.content
        );


        setCopied(
          true
        );


        window.setTimeout(
          () => {

            setCopied(
              false
            );

          },
          1600
        );


      } catch (error) {

        console.error(
          "COPY RESPONSE ERROR:",
          error
        );

      }

    };


  return (

    <article
      className={
        isAssistant
        ? "cf-message assistant"
        : "cf-message user"
      }
    >


      {
        isAssistant
        && (

          <div className="cf-ai-avatar">
            C
          </div>

        )
      }


      <div className="cf-message-column">


        <div className="cf-message-meta">


          <strong>

            {
              isAssistant
              ? "ContextForge"
              : "You"
            }

          </strong>


          {
            isAssistant
            && (

              <div className="cf-message-meta-actions">


                <button
                  type="button"

                  className={
                    copied
                    ? "cf-copy-response copied"
                    : "cf-copy-response"
                  }

                  onClick={
                    handleCopyResponse
                  }

                  title="Copy response"
                >

                  <span>

                    {
                      copied
                      ? "✓"
                      : "⧉"
                    }

                  </span>


                  {
                    copied
                    ? "Copied"
                    : "Copy"
                  }

                </button>


                <div className="cf-message-badges">


                  {
                    message.mode
                    === "documents"
                    && (

                      <span className="cf-badge">

                        ◫ Knowledge

                      </span>

                    )
                  }


                  {
                    message.mode
                    === "agent"
                    && (

                      <span className="cf-badge agent">

                        ⚡ Agent

                      </span>

                    )
                  }


                  {
                    message.confidence
                    && (

                      <span
                        className={
                          (
                            "cf-confidence "
                            + message.confidence
                          )
                        }
                      >

                        <i />

                        {
                          capitalize(
                            message.confidence
                          )
                        }

                      </span>

                    )
                  }


                </div>


              </div>

            )
          }


        </div>


        <div className="cf-message-bubble">


          <div className="cf-message-content">

            {
              renderMessage(
                message.content
              )
            }

          </div>


          {
            isAssistant

            &&

            message.used_tools
              ?.length > 0

            && (

              <MessageSection
                title="Tools used"
              >

                <div className="cf-tools">

                  {
                    message.used_tools.map(
                      (
                        tool,
                        index
                      ) => (

                        <span
                          key={
                            `${tool}-${index}`
                          }
                        >

                          ⚙{" "}
                          {
                            formatToolName(
                              tool
                            )
                          }

                        </span>

                      )
                    )
                  }

                </div>

              </MessageSection>

            )
          }


          {
            isAssistant

            &&

            message.sources
              ?.length > 0

            && (

              <MessageSection
                title="Sources"
              >

                <div className="cf-sources">

                  {
                    message.sources.map(
                      (
                        source,
                        index
                      ) => (

                        <div
                          className="cf-source-card"

                          key={
                            (
                              `${source.document_id}-`
                              + `${source.page}-`
                              + `${index}`
                            )
                          }
                        >

                          <div className="cf-source-file-icon">
                            PDF
                          </div>


                          <div className="cf-source-info">

                            <strong>
                              {
                                source.filename
                              }
                            </strong>


                            <div>

                              {
                                source.page
                                !== null

                                &&

                                source.page
                                !== undefined

                                && (

                                  <span>

                                    Page {
                                      source.page
                                    }

                                  </span>

                                )
                              }


                              {
                                source.score
                                !== null

                                &&

                                source.score
                                !== undefined

                                && (

                                  <span>

                                    {
                                      (
                                        source.score
                                        * 100
                                      )
                                      .toFixed(
                                        0
                                      )
                                    }
                                    % match

                                  </span>

                                )
                              }

                            </div>

                          </div>

                        </div>

                      )
                    )
                  }

                </div>

              </MessageSection>

            )
          }


          {
            isAssistant

            &&

            message.action_items
              ?.length > 0

            && (

              <MessageSection
                title="Action items"
              >

                <div className="cf-action-items">

                  {
                    message.action_items.map(
                      (
                        action,
                        index
                      ) => (

                        <div
                          className="cf-action-item"

                          key={
                            index
                          }
                        >

                          <div className="cf-action-number">

                            {
                              index + 1
                            }

                          </div>


                          <div className="cf-action-info">


                            <div className="cf-action-heading">

                              <strong>
                                {
                                  action.title
                                }
                              </strong>


                              <span
                                className={
                                  (
                                    "cf-priority "
                                    + action.priority
                                  )
                                }
                              >
                                {
                                  action.priority
                                }
                              </span>

                            </div>


                            <p>
                              {
                                action.description
                              }
                            </p>

                          </div>

                        </div>

                      )
                    )
                  }

                </div>

              </MessageSection>

            )
          }


        </div>


        {
          isAssistant

          &&

          message.latency_ms
          !== null

          &&

          message.latency_ms
          !== undefined

          && (

            <span className="cf-response-time">

              {
                (
                  message.latency_ms
                  / 1000
                )
                .toFixed(
                  2
                )
              }
              s response

            </span>

          )
        }


      </div>

    </article>

  );

}


// ==========================================================
// Message Section
// ==========================================================

function MessageSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {

  return (

    <div className="cf-message-section">

      <span className="cf-message-section-title">
        {
          title
        }
      </span>

      {
        children
      }

    </div>

  );

}


// ==========================================================
// Message Formatter
// ==========================================================

function renderMessage(
  content: string
) {

  return (

    <ReactMarkdown
      remarkPlugins={[
        remarkGfm,
        remarkBreaks,
      ]}
      components={{

        a: ({
          children,
          ...props
        }) => (

          <a
            {...props}
            target="_blank"
            rel="noopener noreferrer"
          >

            {
              children
            }

          </a>

        ),


        pre: ({
          children,
        }) => (

          <MarkdownCodeBlock>

            {
              children
            }

          </MarkdownCodeBlock>

        ),


        code: ({
          children,
          className,
          ...props
        }) => {

          const isBlock =
            Boolean(
              className
            );


          if (
            isBlock
          ) {

            return (

              <code
                {...props}
                className={
                  className
                }
              >

                {
                  children
                }

              </code>

            );

          }


          return (

            <code
              {...props}
              className="cf-inline-code"
            >

              {
                children
              }

            </code>

          );

        },


        table: ({
          children,
        }) => (

          <div className="cf-markdown-table-wrap">

            <table>

              {
                children
              }

            </table>

          </div>

        ),

      }}
    >

      {
        content
      }

    </ReactMarkdown>

  );

}


// ==========================================================
// Markdown Code Block
// ==========================================================

function MarkdownCodeBlock({
  children,
}: {
  children: React.ReactNode;
}) {

  const [
    copied,
    setCopied,
  ] = useState(false);


  const code =
    getReactNodeText(
      children
    )
    .replace(
      /\n$/,
      ""
    );


  const handleCopy =
    async () => {

      try {

        await copyTextToClipboard(
          code
        );


        setCopied(
          true
        );


        window.setTimeout(
          () => {

            setCopied(
              false
            );

          },
          1600
        );


      } catch (error) {

        console.error(
          "COPY CODE ERROR:",
          error
        );

      }

    };


  return (

    <div className="cf-code-block">


      <div className="cf-code-toolbar">


        <span>

          Code

        </span>


        <button
          type="button"

          onClick={
            handleCopy
          }
        >

          {
            copied
            ? "✓ Copied"
            : "⧉ Copy"
          }

        </button>


      </div>


      <pre>

        {
          children
        }

      </pre>


    </div>

  );

}


// ==========================================================
// Clipboard Helper
// ==========================================================

async function copyTextToClipboard(
  text: string
) {

  if (
    navigator.clipboard
    && window.isSecureContext
  ) {

    await navigator.clipboard.writeText(
      text
    );

    return;

  }


  const textarea =
    document.createElement(
      "textarea"
    );


  textarea.value =
    text;


  textarea.style.position =
    "fixed";

  textarea.style.opacity =
    "0";


  document.body.appendChild(
    textarea
  );


  textarea.focus();

  textarea.select();


  document.execCommand(
    "copy"
  );


  document.body.removeChild(
    textarea
  );

}


// ==========================================================
// Extract Text from React Node
// ==========================================================

function getReactNodeText(
  node: React.ReactNode
): string {

  if (
    typeof node === "string"
    || typeof node === "number"
  ) {

    return String(
      node
    );

  }


  if (
    Array.isArray(
      node
    )
  ) {

    return node
      .map(
        getReactNodeText
      )
      .join("");

  }


  if (
    node
    && typeof node === "object"
    && "props" in node
  ) {

    const element =
      node as React.ReactElement<{
        children?: React.ReactNode;
      }>;


    return getReactNodeText(
      element.props.children
    );

  }


  return "";

}


// ==========================================================
// Helpers
// ==========================================================

function formatToolName(
  value: string
) {

  return (
    value
      .replace(
        /_/g,
        " "
      )
      .replace(
        /\b\w/g,
        (
          character
        ) =>
          character
            .toUpperCase()
      )
  );

}


function getInputPlaceholder(
  mode: ChatMode
) {

  if (
    mode === "documents"
  ) {

    return (
      "Ask anything from your knowledge base..."
    );

  }


  if (
    mode === "agent"
  ) {

    return (
      "Ask the agent to analyze, search or create an action plan..."
    );

  }


  return (
    "Ask ContextForge anything..."
  );

}


function capitalize(
  value: string
) {

  return (
    value
      .charAt(0)
      .toUpperCase()
    +
    value.slice(1)
  );

}