import api from "./api";


// ==========================================================
// Types
// ==========================================================

export interface DocumentItem {
  id: number;
  user_id?: number;

  filename: string;

  file_type: string;

  status:
    | "processing"
    | "ready"
    | "failed"
    | string;

  created_at: string;
}


export interface DocumentUploadResponse {
  document_id: number;

  filename: string;

  status: string;

  pages: number;

  chunks: number;
}


// ==========================================================
// Get Documents
// ==========================================================

export async function getDocuments():
  Promise<DocumentItem[]> {

  const response =
    await api.get<DocumentItem[]>(
      "/documents"
    );


  return response.data;
}


// ==========================================================
// Upload Document
// ==========================================================

export async function uploadDocument(
  file: File,
  onProgress?: (
    percentage: number
  ) => void
): Promise<DocumentUploadResponse> {

  const formData =
    new FormData();


  formData.append(
    "file",
    file
  );


  const response =
    await api.post<DocumentUploadResponse>(
      "/documents/upload",
      formData,
      {
        onUploadProgress:
          (
            progressEvent
          ) => {

            if (
              !progressEvent.total
            ) {

              return;
            }


            const percentage =
              Math.round(
                (
                  progressEvent.loaded
                  / progressEvent.total
                )
                * 100
              );


            onProgress?.(
              percentage
            );

          },
      }
    );


  return response.data;
}


// ==========================================================
// Delete Document
// ==========================================================

export async function deleteDocument(
  documentId: number
): Promise<void> {

  await api.delete(
    `/documents/${documentId}`
  );

}