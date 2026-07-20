"use client";

import { useEffect, useRef } from "react";

interface VoiceFeedbackProps {
  text: string;
  autoPlay?: boolean;
  onEnd?: () => void;
}

export default function VoiceFeedback({ text, autoPlay = true, onEnd }: VoiceFeedbackProps) {
  const hasSpoken = useRef(false);

  useEffect(() => {
    if (autoPlay && text && !hasSpoken.current && typeof window !== "undefined") {
      hasSpoken.current = true;
      
      // Use Web Speech API for text-to-speech
      if ("speechSynthesis" in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 1;
        
        if (onEnd) {
          utterance.onend = () => onEnd();
        }
        
        window.speechSynthesis.speak(utterance);
      }
    }
  }, [text, autoPlay, onEnd]);

  return null; // This component doesn't render anything visible
}