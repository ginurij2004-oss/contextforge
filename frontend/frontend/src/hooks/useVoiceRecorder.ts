import {
  useEffect,
  useRef,
  useState,
} from "react";


interface UseVoiceRecorderOptions {

  onRecordingReady:
    (blob: Blob) =>
      void | Promise<void>;

  silenceTimeoutMs?: number;

  maxRecordingMs?: number;

}


type OptionalMediaDevices = {

  getUserMedia?: (
    constraints:
      MediaStreamConstraints
  ) => Promise<MediaStream>;

};


type OptionalNavigator = {

  mediaDevices?:
    OptionalMediaDevices;

};


function getMediaDevices():
  OptionalMediaDevices | undefined {

  if (
    typeof navigator
    === "undefined"
  ) {

    return undefined;

  }


  const optionalNavigator =
    navigator as unknown as OptionalNavigator;


  return (
    optionalNavigator.mediaDevices
  );

}


function browserSupportsVoiceRecording() {

  const mediaDevices =
    getMediaDevices();


  return (
    typeof MediaRecorder
      !== "undefined"

    && typeof (
      mediaDevices
        ?.getUserMedia
    ) === "function"
  );

}


export function useVoiceRecorder({

  onRecordingReady,

  silenceTimeoutMs =
    1400,

  maxRecordingMs =
    30000,

}: UseVoiceRecorderOptions) {


  // ========================================================
  // Refs
  // ========================================================

  const mediaRecorderRef =
    useRef<MediaRecorder | null>(
      null
    );


  const streamRef =
    useRef<MediaStream | null>(
      null
    );


  const chunksRef =
    useRef<Blob[]>([]);


  const audioContextRef =
    useRef<AudioContext | null>(
      null
    );


  const analyserRef =
    useRef<AnalyserNode | null>(
      null
    );


  const animationFrameRef =
    useRef<number | null>(
      null
    );


  const silenceStartedAtRef =
    useRef<number | null>(
      null
    );


  const speechDetectedRef =
    useRef(false);


  const maxTimerRef =
    useRef<number | null>(
      null
    );


  const callbackRef =
    useRef(
      onRecordingReady
    );


  // ========================================================
  // State
  // ========================================================

  const [
    isSupported,
    setIsSupported,
  ] = useState(false);


  const [
    isRecording,
    setIsRecording,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  // ========================================================
  // Keep callback current
  // ========================================================

  useEffect(() => {

    callbackRef.current =
      onRecordingReady;

  }, [
    onRecordingReady,
  ]);


  // ========================================================
  // Stop microphone tracks
  // ========================================================

  const stopTracks =
    () => {

      streamRef.current
        ?.getTracks()
        .forEach(
          (
            track
          ) => {

            track.stop();

          }
        );


      streamRef.current =
        null;

    };


  // ========================================================
  // Clean silence detection resources
  // ========================================================

  const cleanupAudioAnalysis =
    () => {

      if (
        animationFrameRef.current
        !== null
      ) {

        cancelAnimationFrame(
          animationFrameRef.current
        );


        animationFrameRef.current =
          null;

      }


      if (
        maxTimerRef.current
        !== null
      ) {

        window.clearTimeout(
          maxTimerRef.current
        );


        maxTimerRef.current =
          null;

      }


      const audioContext =
        audioContextRef.current;


      if (
        audioContext
        && audioContext.state
          !== "closed"
      ) {

        audioContext.close()
          .catch(
            () => undefined
          );

      }


      audioContextRef.current =
        null;

      analyserRef.current =
        null;

      silenceStartedAtRef.current =
        null;

      speechDetectedRef.current =
        false;

    };


  // ========================================================
  // Stop recording
  // ========================================================

  const stopRecording =
    () => {

      const recorder =
        mediaRecorderRef.current;


      if (
        !recorder
        || recorder.state
          === "inactive"
      ) {

        return;

      }


      cleanupAudioAnalysis();


      try {

        recorder.stop();

      } catch {

        setIsRecording(
          false
        );

        mediaRecorderRef.current =
          null;

        stopTracks();

      }

    };


  // ========================================================
  // Detect browser support + cleanup on unmount
  // ========================================================

  useEffect(() => {

    setIsSupported(
      browserSupportsVoiceRecording()
    );


    return () => {

      const recorder =
        mediaRecorderRef.current;


      if (
        recorder
        && recorder.state
          !== "inactive"
      ) {

        try {

          recorder.stop();

        } catch {

          // Safe cleanup only.

        }

      }


      cleanupAudioAnalysis();

      stopTracks();

    };

  }, []);


  // ========================================================
  // Silence monitoring
  // ========================================================

  const monitorSilence =
    (
      analyser:
        AnalyserNode
    ) => {

      const data =
        new Uint8Array(
          analyser.fftSize
        );


      const check =
        () => {

          if (
            !mediaRecorderRef.current

            || mediaRecorderRef
              .current
              .state
              !== "recording"
          ) {

            return;

          }


          analyser
            .getByteTimeDomainData(
              data
            );


          let sumSquares =
            0;


          for (
            let index = 0;
            index < data.length;
            index += 1
          ) {

            const normalized =
              (
                data[index]
                - 128
              )
              / 128;


            sumSquares +=
              normalized
              * normalized;

          }


          const rms =
            Math.sqrt(
              sumSquares
              / data.length
            );


          const now =
            performance.now();


          const speaking =
            rms > 0.018;


          if (
            speaking
          ) {

            speechDetectedRef.current =
              true;

            silenceStartedAtRef.current =
              null;

          } else if (
            speechDetectedRef.current
          ) {

            if (
              silenceStartedAtRef.current
              === null
            ) {

              silenceStartedAtRef.current =
                now;

            } else if (
              now
              - silenceStartedAtRef.current
              >= silenceTimeoutMs
            ) {

              stopRecording();

              return;

            }

          }


          animationFrameRef.current =
            requestAnimationFrame(
              check
            );

        };


      animationFrameRef.current =
        requestAnimationFrame(
          check
        );

    };


  // ========================================================
  // Start recording
  // ========================================================

  const startRecording =
    async () => {

      if (
        isRecording
      ) {

        return;

      }


      const mediaDevices =
        getMediaDevices();


      if (
        typeof MediaRecorder
          === "undefined"

        || typeof (
          mediaDevices
            ?.getUserMedia
        ) !== "function"
      ) {

        setIsSupported(
          false
        );

        setError(
          "Voice recording is not supported in this browser."
        );

        return;

      }


      try {

        setError("");


        const stream =
          await mediaDevices
            .getUserMedia({
              audio: {

                echoCancellation:
                  true,

                noiseSuppression:
                  true,

                autoGainControl:
                  true,

              },
            });


        streamRef.current =
          stream;


        let mimeType =
          "";


        const preferredTypes = [

          "audio/webm;codecs=opus",

          "audio/webm",

          "audio/ogg;codecs=opus",

          "audio/mp4",

        ];


        for (
          const candidate
          of preferredTypes
        ) {

          if (
            MediaRecorder
              .isTypeSupported(
                candidate
              )
          ) {

            mimeType =
              candidate;

            break;

          }

        }


        const recorder =
          mimeType

            ? new MediaRecorder(
                stream,
                {
                  mimeType,
                }
              )

            : new MediaRecorder(
                stream
              );


        mediaRecorderRef.current =
          recorder;


        chunksRef.current =
          [];


        recorder.ondataavailable =
          (
            event:
              BlobEvent
          ) => {

            if (
              event.data.size
              > 0
            ) {

              chunksRef.current
                .push(
                  event.data
                );

            }

          };


        recorder.onerror =
          () => {

            setError(
              "Microphone recording failed."
            );

          };


        recorder.onstop =
          async () => {

            setIsRecording(
              false
            );


            cleanupAudioAnalysis();


            const recordedType =
              recorder.mimeType
              || mimeType
              || "audio/webm";


            const blob =
              new Blob(
                chunksRef.current,
                {
                  type:
                    recordedType,
                }
              );


            chunksRef.current =
              [];


            stopTracks();


            mediaRecorderRef.current =
              null;


            if (
              blob.size
              < 1000
            ) {

              setError(
                "No usable speech was recorded. Please try again."
              );

              return;

            }


            try {

              await callbackRef.current(
                blob
              );

            } catch (
              callbackError
            ) {

              console.error(
                "VOICE RECORDING CALLBACK ERROR:",
                callbackError
              );

              setError(
                "Could not process the recorded audio."
              );

            }

          };


        recorder.start(
          250
        );


        setIsRecording(
          true
        );


        const audioContext =
          new AudioContext();


        audioContextRef.current =
          audioContext;


        const source =
          audioContext
            .createMediaStreamSource(
              stream
            );


        const analyser =
          audioContext
            .createAnalyser();


        analyser.fftSize =
          2048;


        source.connect(
          analyser
        );


        analyserRef.current =
          analyser;


        monitorSilence(
          analyser
        );


        maxTimerRef.current =
          window.setTimeout(
            () => {

              stopRecording();

            },
            maxRecordingMs
          );


      } catch (
        startError:
          unknown
      ) {

        console.error(
          "VOICE RECORDING START ERROR:",
          startError
        );


        stopTracks();

        cleanupAudioAnalysis();


        const errorName =
          (
            startError
            instanceof DOMException
          )
            ? startError.name
            : "";


        if (
          errorName
          === "NotAllowedError"
        ) {

          setError(
            "Microphone permission was denied. Allow microphone access and try again."
          );

        } else if (
          errorName
          === "NotFoundError"
        ) {

          setError(
            "No microphone was found."
          );

        } else {

          setError(
            "Could not start microphone recording."
          );

        }


        setIsRecording(
          false
        );

      }

    };


  // ========================================================
  // Public API
  // ========================================================

  return {

    isSupported,

    isRecording,

    error,

    startRecording,

    stopRecording,

  };

}
