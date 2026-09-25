import api from "./api";


export interface VoiceTranscriptionResponse {
  text: string;
}


function extensionFromMime(
  mimeType: string
) {

  if (
    mimeType.includes(
      "ogg"
    )
  ) {

    return "ogg";

  }


  if (
    mimeType.includes(
      "mp4"
    )
  ) {

    return "m4a";

  }


  return "webm";
}


export async function transcribeVoice(
  audioBlob: Blob
): Promise<string> {

  const formData =
    new FormData();


  const extension =
    extensionFromMime(
      audioBlob.type
    );


  formData.append(
    "file",
    audioBlob,
    `voice-input.${extension}`
  );


  const response =
    await api.post<
      VoiceTranscriptionResponse
    >(
      "/voice/transcribe",
      formData,
      {
        headers: {
          "Content-Type":
            "multipart/form-data",
        },
      }
    );


  return response.data.text;
}
