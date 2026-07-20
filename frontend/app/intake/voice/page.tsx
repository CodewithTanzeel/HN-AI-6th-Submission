"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import ProgressStepper from "../../components/ProgressStepper";
import VoiceFeedback from "../../components/VoiceFeedback";
import VoiceButton from "../../components/VoiceButton";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const HAS_ELEVENLABS_KEY = !!process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY;

export default function VoiceIntake() {
  const [transcript, setTranscript] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<any>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const [voiceText, setVoiceText] = useState("");
  const onCommandRef = useRef<(command: string) => void>(() => {});

  useEffect(() => {
    setMounted(true);
    const params = new URLSearchParams(window.location.search);
    setJobId(params.get("job_id"));
  }, []);

  useEffect(() => {
    if (HAS_ELEVENLABS_KEY && jobId) {
      fetch(`${API_BASE}/api/jobs/${jobId}/voice/session`)
        .then((res) => res.json())
        .then((data) => setSession(data))
        .catch(() => {});
    }
  }, [jobId]);

  useEffect(() => {
    if (mounted) {
      setVoiceText(HAS_ELEVENLABS_KEY 
        ? "Please speak with the AI agent about your move details. Include origin, destination, move date, and home size."
        : "Please describe your move. Include origin, destination, move date, and home size.");
    }
  }, [mounted, HAS_ELEVENLABS_KEY]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobId) {
      setError("Missing job_id");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}/voice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript }),
      });
      if (!res.ok) throw new Error("Voice intake failed");
      setVoiceText("Details saved. Taking you to documents page.");
      setTimeout(() => {
        window.location.href = `/intake/documents?job_id=${jobId}`;
      }, 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setVoiceText("Failed to save details. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceCommand = useCallback((command: string) => {
    if (command.includes("submit") || command.includes("next") || command.includes("continue")) {
      const form = document.querySelector("form");
      if (form) form.dispatchEvent(new Event("submit", { cancelable: true }));
    }
  }, []);

  // Keep the ref updated
  useEffect(() => {
    onCommandRef.current = handleVoiceCommand;
  }, [handleVoiceCommand]);

  if (!mounted || !jobId) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
        <VoiceFeedback text="Loading voice intake page..." />
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Voice Intake</h1>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
      <VoiceFeedback text={voiceText} />
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
        <ProgressStepper currentStep={1} />
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Voice Intake</h1>
        <p className="text-gray-600 mb-6">
          {HAS_ELEVENLABS_KEY
            ? "Use the voice widget below to speak with our AI agent, or enter text manually."
            : "Describe your move details below."}
        </p>

        {HAS_ELEVENLABS_KEY && session && (
          <div className="mb-6">
            <iframe
              src={session.widget_url}
              width="100%"
              height="400"
              style={{ border: "1px solid #e5e7eb", borderRadius: "8px" }}
              allow="microphone"
            />
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            className="w-full border border-gray-300 rounded-lg p-3 h-40"
            placeholder="Example: Moving from Rock Hill to Charlotte, 45 miles, 2 bedroom apartment, 2 flights of stairs"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            {loading ? "Processing..." : "Submit Voice Transcript"}
          </button>
          
          <VoiceButton
            onCommand={handleVoiceCommand}
            label="Say 'Submit' (Voice)"
            className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          />
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}