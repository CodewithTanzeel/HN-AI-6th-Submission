"use client";

import { useState, useEffect } from "react";
import ProgressStepper from "../components/ProgressStepper";
import VoiceFeedback from "../components/VoiceFeedback";
import VoiceButton from "../components/VoiceButton";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function getJobId(): string | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  return params.get("job_id");
}

interface Negotiation {
  vendor_id: string;
  vendor_name: string;
  original_total: number;
  negotiated_total: number;
  changed: boolean;
}

export default function Negotiate() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [negotiations, setNegotiations] = useState<Negotiation[]>([]);
  const [done, setDone] = useState(false);
  const [voiceText, setVoiceText] = useState("");
  const jobId = getJobId();

  const handleNegotiate = async () => {
    if (!jobId) {
      setError("Missing job_id");
      return;
    }
    setLoading(true);
    setError(null);
    setVoiceText("Negotiating with moving companies. Please wait...");
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}/negotiate`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Negotiation failed");
      const data = await res.json();
      setNegotiations(data.negotiations || []);
      setDone(true);
      
      const changedCount = data.negotiations?.filter((n: Negotiation) => n.changed).length || 0;
      setVoiceText(`Negotiation complete. ${changedCount} companies reduced their prices. Say 'Next' to view report.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setVoiceText("Negotiation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceCommand = (command: string) => {
    if (command.includes("negotiate") || command.includes("start")) {
      handleNegotiate();
    } else if (command.includes("next") || command.includes("report") || command.includes("view")) {
      if (done && jobId) {
        window.location.href = `/report?job_id=${jobId}`;
      }
    }
  };

  useEffect(() => {
    if (jobId && !done) {
      fetch(`${API_BASE}/api/jobs/${jobId}/report`)
        .then((res) => res.json())
        .then((data) => {
          if (data.negotiations && data.negotiations.length > 0) {
            setNegotiations(data.negotiations);
            setDone(true);
            setVoiceText("Loaded negotiation results. Say 'Next' to view report.");
          }
        })
        .catch(() => {});
    }
  }, [jobId, done]);

  useEffect(() => {
    if (jobId) {
      setVoiceText("Ready to negotiate. Say 'Start negotiation' to begin.");
    }
  }, [jobId]);

  if (!jobId) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
        <VoiceFeedback text="Missing job ID. Please create a job first." />
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Negotiate</h1>
          <p className="text-gray-600">Missing job_id. Please create a job first.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
      <VoiceFeedback text={voiceText} />
      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl p-8">
        <ProgressStepper currentStep={6} />
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Negotiation</h1>
        <p className="text-gray-600 mb-6">
          We will price-match using the best quote as leverage.
        </p>

        {!done ? (
          <div className="space-y-4">
            <button
              onClick={handleNegotiate}
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              {loading ? "Negotiating..." : "Start Negotiation"}
            </button>
            
            <VoiceButton
              onCommand={handleVoiceCommand}
              label="Say 'Start negotiation' (Voice)"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            />
          </div>
        ) : (
          <div className="space-y-4">
            {negotiations.map((n) => (
              <div key={n.vendor_id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-xl font-semibold">{n.vendor_name}</h3>
                  <span className={`text-lg font-semibold ${n.changed ? "text-green-600" : "text-gray-600"}`}>
                    {n.changed ? "Price Reduced" : "No Change"}
                  </span>
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Original: ${n.original_total.toFixed(2)}</span>
                  <span>Negotiated: ${n.negotiated_total.toFixed(2)}</span>
                </div>
              </div>
            ))}
            <a
              href={`/report?job_id=${jobId}`}
              className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors text-center"
            >
              View Final Report
            </a>
            
            <VoiceButton
              onCommand={handleVoiceCommand}
              label="Say 'Next' (Voice)"
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            />
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mt-4">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}