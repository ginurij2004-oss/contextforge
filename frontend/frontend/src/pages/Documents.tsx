import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  deleteDocument,
  getDocuments,
  uploadDocument,
  type DocumentItem,
} from "../services/documents";

import {
  useTheme,
} from "../theme/ThemeContext";

import {
  useAuth,
} from "../context/AuthContext";

import "./Documents.css";


export default function Documents() {

  const navigate =
    useNavigate();


  const {
    theme,
    setTheme,
  } = useTheme();


  const {
    logout,
  } = useAuth();


  const fileInputRef =
    useRef<HTMLInputElement | null>(
      null
    );


  const [
    documents,
    setDocuments,
  ] = useState<DocumentItem[]>([]);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    refreshing,
    setRefreshing,
  ] = useState(false);


  const [
    uploading,
    setUploading,
  ] = useState(false);


  const [
    uploadProgress,
    setUploadProgress,
  ] = useState(0);


  const [
    uploadFilename,
    setUploadFilename,
  ] = useState("");


  const [
    dragActive,
    setDragActive,
  ] = useState(false);


  const [
    search,
    setSearch,
  ] = useState("");


  const [
    error,
    setError,
  ] = useState("");


  const [
    successMessage,
    setSuccessMessage,
  ] = useState("");


  const [
    documentToDelete,
    setDocumentToDelete,
  ] = useState<DocumentItem | null>(
    null
  );


  const [
    deleting,
    setDeleting,
  ] = useState(false);


  const [
    mobileSidebarOpen,
    setMobileSidebarOpen,
  ] = useState(false);


  // ======================================================
  // Initial Load
  // ======================================================

  useEffect(() => {

    loadDocuments();

  }, []);


  // ======================================================
  // Load Documents
  // ======================================================

  const loadDocuments =
    async (
      manual = false
    ) => {

      try {

        if (
          manual
        ) {

          setRefreshing(
            true
          );

        } else {

          setLoading(
            true
          );

        }


        setError("");


        const data =
          await getDocuments();


        setDocuments(
          data
        );


      } catch (error: any) {

        console.error(
          "DOCUMENT LOAD ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Failed to load documents."
        );


      } finally {

        setLoading(
          false
        );

        setRefreshing(
          false
        );

      }

    };


  // ======================================================
  // Validate PDF
  // ======================================================

  const validateFile =
    (
      file: File
    ) => {

      const extension =
        file.name
          .split(".")
          .pop()
          ?.toLowerCase();


      if (
        extension !== "pdf"
      ) {

        setError(
          "Only PDF files are supported."
        );

        return false;

      }


      setError("");

      return true;

    };


  // ======================================================
  // Upload
  // ======================================================

  const handleUpload =
    async (
      file: File
    ) => {

      if (
        uploading
        || !validateFile(
          file
        )
      ) {

        return;

      }


      try {

        setUploading(
          true
        );

        setUploadProgress(
          0
        );

        setUploadFilename(
          file.name
        );

        setError("");

        setSuccessMessage("");


        const result =
          await uploadDocument(
            file,
            (
              progress
            ) =>
              setUploadProgress(
                progress
              )
          );


        setSuccessMessage(
          (
            `${result.filename} uploaded successfully. `
            + `${result.pages} pages and `
            + `${result.chunks} knowledge chunks indexed.`
          )
        );


        await loadDocuments();


      } catch (error: any) {

        console.error(
          "DOCUMENT UPLOAD ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Document upload failed."
        );


      } finally {

        setUploading(
          false
        );

        setUploadProgress(
          0
        );

        setUploadFilename(
          ""
        );


        if (
          fileInputRef.current
        ) {

          fileInputRef.current.value =
            "";

        }

      }

    };


  // ======================================================
  // File Input
  // ======================================================

  const handleFileChange =
    (
      event:
        ChangeEvent<HTMLInputElement>
    ) => {

      const file =
        event.target
          .files?.[0];


      if (
        file
      ) {

        handleUpload(
          file
        );

      }

    };


  // ======================================================
  // Drag Events
  // ======================================================

  const handleDragOver =
    (
      event:
        DragEvent<HTMLDivElement>
    ) => {

      event.preventDefault();

      setDragActive(
        true
      );

    };


  const handleDragLeave =
    (
      event:
        DragEvent<HTMLDivElement>
    ) => {

      event.preventDefault();

      setDragActive(
        false
      );

    };


  const handleDrop =
    (
      event:
        DragEvent<HTMLDivElement>
    ) => {

      event.preventDefault();

      setDragActive(
        false
      );


      const file =
        event.dataTransfer
          .files?.[0];


      if (
        file
      ) {

        handleUpload(
          file
        );

      }

    };


  // ======================================================
  // Delete
  // ======================================================

  const confirmDelete =
    async () => {

      if (
        !documentToDelete
        || deleting
      ) {

        return;

      }


      try {

        setDeleting(
          true
        );

        setError("");


        await deleteDocument(
          documentToDelete.id
        );


        setDocuments(
          (
            previous
          ) =>
            previous.filter(
              (
                document
              ) =>
                document.id
                !== documentToDelete.id
            )
        );


        setSuccessMessage(
          "Document deleted successfully."
        );


        setDocumentToDelete(
          null
        );


      } catch (error: any) {

        console.error(
          "DOCUMENT DELETE ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Failed to delete document."
        );


      } finally {

        setDeleting(
          false
        );

      }

    };


  // ======================================================
  // Filter Documents
  // ======================================================

  const filteredDocuments =
    useMemo(
      () => {

        const query =
          search
            .trim()
            .toLowerCase();


        if (
          !query
        ) {

          return documents;

        }


        return documents.filter(
          (
            document
          ) =>
            document.filename
              .toLowerCase()
              .includes(
                query
              )
        );

      },
      [
        documents,
        search,
      ]
    );


  // ======================================================
  // Stats
  // ======================================================

  const readyCount =
    documents.filter(
      (
        document
      ) =>
        document.status
        === "ready"
    ).length;


  const processingCount =
    documents.filter(
      (
        document
      ) =>
        document.status
        === "processing"
    ).length;


  const failedCount =
    documents.filter(
      (
        document
      ) =>
        document.status
        === "failed"
    ).length;


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
    loading
  ) {

    return (

      <div className="documents-loading">

        <div className="documents-loading-logo">
          C
        </div>

        <span>
          Loading documents...
        </span>

      </div>

    );

  }


  // ======================================================
  // UI
  // ======================================================

  return (

    <div className="documents-shell">


      {/* Mobile Overlay */}

      {
        mobileSidebarOpen
        && (

          <button
            type="button"

            className="documents-mobile-overlay"

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
          ? "documents-sidebar open"
          : "documents-sidebar"
        }
      >


        <div className="documents-brand">

          <div className="documents-logo">
            C
          </div>


          <div>

            <strong>
              ContextForge
            </strong>

            <span>
              Enterprise AI
            </span>

          </div>


          <button
            type="button"

            className="documents-sidebar-close"

            onClick={() =>
              setMobileSidebarOpen(
                false
              )
            }
          >
            ×
          </button>

        </div>


        <nav className="documents-navigation">


          <button
            type="button"

            onClick={() =>
              navigate(
                "/"
              )
            }
          >

            <span>
              ✦
            </span>

            AI Workspace

          </button>


          <button
            type="button"

            className="active"
          >

            <span>
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

            <span>
              ◩
            </span>

            Analytics

          </button>


        </nav>


        <div className="documents-sidebar-summary">

          <span className="documents-summary-label">
            Knowledge base
          </span>


          <div>

            <strong>
              {
                readyCount
              }
            </strong>

            <span>
              Ready documents
            </span>

          </div>


          <div>

            <strong>
              {
                processingCount
              }
            </strong>

            <span>
              Processing
            </span>

          </div>


        </div>


        <div className="documents-sidebar-footer">


          <div className="documents-online">

            <span />

            ContextForge online

          </div>


          <button
            type="button"

            onClick={
              handleLogout
            }
          >

            ↗ Sign out

          </button>


        </div>


      </aside>


      {/* =================================================
          Main
      ================================================= */}

      <main className="documents-main">


        {/* Header */}

        <header className="documents-header">


          <div className="documents-header-main">


            <button
              type="button"

              className="documents-mobile-menu"

              onClick={() =>
                setMobileSidebarOpen(
                  true
                )
              }
            >
              ☰
            </button>


            <div>

              <span className="documents-eyebrow">

                Knowledge

              </span>


              <h1>

                Documents

              </h1>


              <p>

                Upload and manage the knowledge
                ContextForge can search.

              </p>

            </div>

          </div>


          <div className="documents-header-actions">


            <button
              type="button"

              className="documents-refresh"

              disabled={
                refreshing
              }

              onClick={() =>
                loadDocuments(
                  true
                )
              }
            >

              <span
                className={
                  refreshing
                  ? "spin"
                  : ""
                }
              >
                ↻
              </span>

              {
                refreshing
                ? "Refreshing"
                : "Refresh"
              }

            </button>


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


          </div>


        </header>


        {/* Content */}

        <div className="documents-content">


          {
            error
            && (

              <div className="documents-message error">

                <strong>
                  !
                </strong>

                {
                  error
                }

              </div>

            )
          }


          {
            successMessage
            && (

              <div className="documents-message success">

                <strong>
                  ✓
                </strong>

                {
                  successMessage
                }

              </div>

            )
          }


          {/* =================================================
              Upload
          ================================================= */}

          <section className="documents-upload-section">


            <div className="documents-section-heading">

              <div>

                <span>
                  Add knowledge
                </span>

                <h2>
                  Upload a document
                </h2>

                <p>

                  Upload a PDF and ContextForge
                  will extract, chunk and index
                  its content automatically.

                </p>

              </div>

            </div>


            <div
              className={
                dragActive
                ? "documents-dropzone active"
                : "documents-dropzone"
              }

              onDragOver={
                handleDragOver
              }

              onDragLeave={
                handleDragLeave
              }

              onDrop={
                handleDrop
              }
            >


              {
                uploading
                ? (

                  <div className="documents-uploading">


                    <div className="documents-upload-icon processing">

                      ◌

                    </div>


                    <h3>

                      Processing document

                    </h3>


                    <p>

                      {
                        uploadFilename
                      }

                    </p>


                    <div className="documents-progress-track">

                      <div
                        className="documents-progress-fill"

                        style={{
                          width:
                            `${uploadProgress}%`,
                        }}
                      />

                    </div>


                    <span>

                      {
                        uploadProgress < 100
                          ? (
                              `Uploading ${uploadProgress}%`
                            )
                          : (
                              "Upload complete — indexing knowledge..."
                            )
                      }

                    </span>


                  </div>

                )
                : (

                  <div className="documents-drop-content">


                    <div className="documents-upload-icon">

                      ↑

                    </div>


                    <h3>

                      Drop your PDF here

                    </h3>


                    <p>

                      Drag and drop a PDF,
                      or browse from your computer.

                    </p>


                    <button
                      type="button"

                      onClick={() =>
                        fileInputRef.current
                          ?.click()
                      }
                    >

                      Choose PDF

                    </button>


                    <span className="documents-upload-note">

                      PDF documents only

                    </span>


                  </div>

                )
              }


              <input
                ref={
                  fileInputRef
                }

                type="file"

                accept=".pdf,application/pdf"

                hidden

                onChange={
                  handleFileChange
                }
              />


            </div>


          </section>


          {/* =================================================
              Stats
          ================================================= */}

          <section className="documents-stats">


            <DocumentStat
              value={
                documents.length
              }

              label="Total documents"

              icon="◫"
            />


            <DocumentStat
              value={
                readyCount
              }

              label="Ready"

              icon="✓"

              type="ready"
            />


            <DocumentStat
              value={
                processingCount
              }

              label="Processing"

              icon="◷"

              type="processing"
            />


            <DocumentStat
              value={
                failedCount
              }

              label="Failed"

              icon="!"

              type="failed"
            />


          </section>


          {/* =================================================
              Library
          ================================================= */}

          <section className="documents-library">


            <div className="documents-library-header">


              <div>

                <span>
                  Library
                </span>

                <h2>
                  Your documents
                </h2>

              </div>


              <div className="documents-search">

                <span>
                  ⌕
                </span>


                <input
                  type="search"

                  placeholder="Search documents..."

                  value={
                    search
                  }

                  onChange={
                    (
                      event
                    ) =>
                      setSearch(
                        event.target.value
                      )
                  }
                />

              </div>


            </div>


            {
              filteredDocuments.length
              === 0
                ? (

                  <div className="documents-empty">


                    <div>
                      ◫
                    </div>


                    <h3>

                      {
                        search
                          ? "No documents found"
                          : "Your knowledge base is empty"
                      }

                    </h3>


                    <p>

                      {
                        search
                          ? (
                              "Try searching with a different filename."
                            )
                          : (
                              "Upload your first PDF to start asking grounded questions."
                            )
                      }

                    </p>


                    {
                      !search
                      && (

                        <button
                          type="button"

                          onClick={() =>
                            fileInputRef.current
                              ?.click()
                          }
                        >

                          Upload document

                        </button>

                      )
                    }


                  </div>

                )
                : (

                  <div className="documents-list">


                    {
                      filteredDocuments.map(
                        (
                          document
                        ) => (

                          <DocumentRow
                            key={
                              document.id
                            }

                            document={
                              document
                            }

                            onDelete={() =>
                              setDocumentToDelete(
                                document
                              )
                            }
                          />

                        )
                      )
                    }


                  </div>

                )
            }


          </section>


        </div>


      </main>


      {/* =================================================
          Delete Modal
      ================================================= */}

      {
        documentToDelete
        && (

          <div className="document-delete-overlay">


            <div className="document-delete-modal">


              <div className="document-delete-icon">

                !

              </div>


              <h3>

                Delete document?

              </h3>


              <p>

                You are about to permanently
                remove{" "}

                <strong>

                  {
                    documentToDelete.filename
                  }

                </strong>

                {" "}from your ContextForge
                knowledge base.

              </p>


              <div className="document-delete-warning">

                Its stored PDF and Qdrant
                knowledge vectors will also
                be deleted.

              </div>


              <div className="document-delete-actions">


                <button
                  type="button"

                  className="document-delete-cancel"

                  disabled={
                    deleting
                  }

                  onClick={() =>
                    setDocumentToDelete(
                      null
                    )
                  }
                >

                  Cancel

                </button>


                <button
                  type="button"

                  className="document-delete-confirm"

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
                      : "Delete document"
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
// Document Stat
// ==========================================================

function DocumentStat({
  value,
  label,
  icon,
  type = "",
}: {
  value: number;
  label: string;
  icon: string;
  type?:
    | ""
    | "ready"
    | "processing"
    | "failed";
}) {

  return (

    <article
      className={
        `document-stat ${type}`
      }
    >

      <div>

        {
          icon
        }

      </div>


      <div>

        <strong>

          {
            value
          }

        </strong>

        <span>

          {
            label
          }

        </span>

      </div>

    </article>

  );

}


// ==========================================================
// Document Row
// ==========================================================

function DocumentRow({
  document,
  onDelete,
}: {
  document: DocumentItem;
  onDelete: () => void;
}) {

  return (

    <article className="document-row">


      <div className="document-file-icon">

        PDF

      </div>


      <div className="document-main-info">


        <strong>

          {
            document.filename
          }

        </strong>


        <div className="document-meta">


          <span>

            {
              formatDate(
                document.created_at
              )
            }

          </span>


          <span>
            PDF
          </span>


          <DocumentStatus
            status={
              document.status
            }
          />


        </div>


      </div>


      <div className="document-row-actions">


        {
          document.status === "ready"
          && (

            <button
              type="button"

              className="document-use-button"

              title="Use in AI Workspace"

              onClick={() => {

                window.location.href =
                  "/";

              }}
            >

              Ask AI

            </button>

          )
        }


        <button
          type="button"

          className="document-remove-button"

          title="Delete document"

          onClick={
            onDelete
          }
        >

          Delete

        </button>


      </div>


    </article>

  );

}


// ==========================================================
// Status
// ==========================================================

function DocumentStatus({
  status,
}: {
  status: string;
}) {

  const normalized =
    status.toLowerCase();


  return (

    <span
      className={
        (
          "document-status "
          + normalized
        )
      }
    >

      <i />

      {
        capitalize(
          normalized
        )
      }

    </span>

  );

}


// ==========================================================
// Helpers
// ==========================================================

function capitalize(
  value: string
) {

  return (
    value.charAt(0).toUpperCase()
    + value.slice(1)
  );

}


function formatDate(
  value: string
) {

  const date =
    new Date(
      value
    );


  if (
    Number.isNaN(
      date.getTime()
    )
  ) {

    return value;

  }


  return date.toLocaleDateString(
    "en-US",
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    }
  );

}