"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface VoiceButtonProps {
  onCommand: (command: string) => void;
  label: string;
  voiceText?: string;
  className?: string;
}

export default function VoiceButton({ 
  onCommand, 
  label, 
  voiceText,
  className = "bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
}: VoiceButtonProps) {
  const [listening, setListening] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const onCommandRef = useRef(onCommand);

  // Keep the ref updated with the latest onCommand
  useEffect(() => {
    onCommandRef.current = onCommand;
  }, [onCommand]);

  useEffect(() => {
    if (typeof window !== "undefined" && "webkitSpeechRecognition" in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition;
      const recog = new SpeechRecognition();
      recog.continuous = false;
      recog.interimResults = false;
      recog.lang = "en-US";
      
      recog.onresult = (event: any) => {
        const command = event.results[0][0].transcript.toLowerCase().trim();
        console.log("Voice command received:", command);
        onCommandRef.current(command);
        setListening(false);
      };
      
      recog.onerror = (event: any) => {
        console.error("Speech recognition error:", event.error);
        setError(`Voice error: ${event.error}`);
        setListening(false);
      };
      
      recog.onend = () => {
        setListening(false);
      };
      
      setRecognition(recog);
    } else {
      console.warn("webkitSpeechRecognition not available in this browser");
    }
  }, []);

  const startListening = useCallback(() => {
    if (recognition) {
      setError(null);
      setListening(true);
      recognition.start();
    }
  }, [recognition]);

  // Check if browser supports speech recognition
  const supportsSpeechRecognition = typeof window !== "undefined" && "webkitSpeechRecognition" in window;

  return (
    <div className="w-full">
      <button
        onClick={startListening}
        disabled={listening || !recognition}
        className={`${className} ${listening ? "animate-pulse" : ""}`}
      >
        {listening ? "Listening..." : label}
      </button>
      {!supportsSpeechRecognition && (
        <p className="text-xs text-yellow-600 mt-1">
          Voice recognition requires Chrome/Edge browser
        </p>
      )}
      {error && (
        <p className="text-xs text-red-600 mt-1">{error}</p>
      )}
    </div>
  );
}