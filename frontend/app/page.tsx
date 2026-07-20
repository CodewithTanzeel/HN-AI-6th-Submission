"use client";

import { useState, useEffect } from "react";
import VoiceFeedback from "./components/VoiceFeedback";
import VoiceButton from "./components/VoiceButton";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function createJob() {
  const res = await fetch(`${API_BASE}/api/jobs`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to create job");
  return res.json();
}

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [voiceText, setVoiceText] = useState("");

  const handleCreateJob = async () => {
    setLoading(true);
    setError(null);
    try {
      const job = await createJob();
      setVoiceText("Job created successfully. Taking you to voice intake.");
      setTimeout(() => {
        window.location.href = `/intake/voice?job_id=${job.id}`;
      }, 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setVoiceText("Failed to create job. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceCommand = (command: string) => {
    if (command.includes("create") || command.includes("job") || command.includes("start")) {
      handleCreateJob();
    }
  };

  useEffect(() => {
    // Auto-speak welcome message
    setVoiceText("Welcome to The Negotiator. Say 'Create job' to get started.");
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
      <VoiceFeedback text={voiceText} />
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          The Negotiator
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          Voice-agent system for gathering moving quotes and negotiating the best
          deal.
        </p>
        <div className="space-y-4">
          <button
            onClick={handleCreateJob}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            {loading ? "Creating..." : "Create New Job"}
          </button>
          
          <VoiceButton
            onCommand={handleVoiceCommand}
            label="Or say 'Create job' (Voice)"
            className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          />
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}