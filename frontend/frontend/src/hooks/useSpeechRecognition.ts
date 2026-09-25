import {
  useEffect,
  useRef,
  useState,
} from "react";


interface SpeechRecognitionAlternativeLike {
  transcript: string;
  confidence: number;
}


interface SpeechRecognitionResultLike {
  readonly isFinal: boolean;
  readonly length: number;

  [index: number]:
    SpeechRecognitionAlternativeLike;
}


interface SpeechRecognitionResultListLike {
  readonly length: number;

  [index: number]:
    SpeechRecognitionResultLike;
}


interface SpeechRecognitionEventLike
  extends Event {

  readonly resultIndex: number;

  readonly results:
    SpeechRecognitionResultListLike;
}


interface SpeechRecognitionErrorEventLike
  extends Event {

  readonly error: string;
}


interface SpeechRecognitionLike
  extends EventTarget {

  continuous: boolean;

  interimResults: boolean;

  lang: string;

  maxAlternatives: number;

  onstart:
    | (() => void)
    | null;

  onend:
    | (() => void)
    | null;

  onresult:
    | ((
        event:
          SpeechRecognitionEventLike
      ) => void)
    | null;

  onerror:
    | ((
        event:
          SpeechRecognitionErrorEventLike
      ) => void)
    | null;

  start(): void;

  stop(): void;

  abort(): void;
}


interface SpeechRecognitionConstructorLike {

  new():
    SpeechRecognitionLike;
}


declare global {

  interface Window {

    SpeechRecognition?:
      SpeechRecognitionConstructorLike;

    webkitSpeechRecognition?:
      SpeechRecognitionConstructorLike;
  }
}


interface UseSpeechRecognitionOptions {

  onTranscript:
    (text: string) => void;

  lang?: string;
}


export function useSpeechRecognition({
  onTranscript,
  lang = "en-US",
}: UseSpeechRecognitionOptions) {

  const recognitionRef =
    useRef<
      SpeechRecognitionLike | null
    >(
      null
    );


  const onTranscriptRef =
    useRef(
      onTranscript
    );


  const [
    isSupported,
    setIsSupported,
  ] = useState(false);


  const [
    isListening,
    setIsListening,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  useEffect(() => {

    onTranscriptRef.current =
      onTranscript;

  }, [
    onTranscript,
  ]);


  useEffect(() => {

    const Recognition =
      window.SpeechRecognition
      || window.webkitSpeechRecognition;


    if (
      !Recognition
    ) {

      setIsSupported(
        false
      );

      setError(
        "Voice input is not supported in this browser. Please use Chrome or Edge."
      );

      return;
    }


    setIsSupported(
      true
    );


    const recognition =
      new Recognition();


    recognition.lang =
      lang;

    recognition.continuous =
      true;

    recognition.interimResults =
      true;

    recognition.maxAlternatives =
      1;


    recognition.onstart =
      () => {

        setError("");

        setIsListening(
          true
        );

      };


    recognition.onresult =
      (
        event:
          SpeechRecognitionEventLike
      ) => {

        let transcript = "";


        for (
          let index = 0;

          index
          < event.results.length;

          index += 1
        ) {

          const result =
            event.results[
              index
            ];


          const alternative =
            result[0];


          if (
            !alternative
          ) {

            continue;
          }


          const currentText =
            alternative.transcript
              .trim();


          if (
            !currentText
          ) {

            continue;
          }


          transcript += (
            transcript
            ? ` ${currentText}`
            : currentText
          );

        }


        if (
          transcript.trim()
        ) {

          onTranscriptRef.current(
            transcript.trim()
          );

        }

      };


    recognition.onerror =
      (
        event:
          SpeechRecognitionErrorEventLike
      ) => {

        const code =
          event.error;


        if (
          code === "not-allowed"
          || code
          === "service-not-allowed"
        ) {

          setError(
            "Microphone permission was denied."
          );

        } else if (
          code === "audio-capture"
        ) {

          setError(
            "No microphone was detected."
          );

        } else if (
          code === "no-speech"
        ) {

          setError(
            "No speech was detected."
          );

        } else if (
          code === "network"
        ) {

          setError(
            "Speech recognition network error."
          );

        } else if (
          code !== "aborted"
        ) {

          setError(
            `Voice input error: ${code}`
          );

        }


        if (
          code !== "aborted"
        ) {

          setIsListening(
            false
          );

        }

      };


    recognition.onend =
      () => {

        setIsListening(
          false
        );

      };


    recognitionRef.current =
      recognition;


    return () => {

      try {

        recognition.abort();

      } catch {

        // Already stopped.

      }


      recognitionRef.current =
        null;

    };

  }, [
    lang,
  ]);


  const startListening =
    () => {

      const recognition =
        recognitionRef.current;


      if (
        !recognition
        || isListening
      ) {

        return;

      }


      setError("");


      try {

        recognition.start();

      } catch {

        setError(
          "Voice input could not start."
        );

      }

    };


  const stopListening =
    () => {

      const recognition =
        recognitionRef.current;


      if (
        !recognition
      ) {

        return;

      }


      try {

        recognition.stop();

      } catch {

        // Safe no-op.

      }

    };


  return {
    isSupported,
    isListening,
    error,
    startListening,
    stopListening,
  };
}
