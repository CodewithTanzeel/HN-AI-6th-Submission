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

interface Quote {
  vendor_id: string;
  vendor_name: string;
  total: number;
  line_items: Array<{ fee_type: string; description: string; amount: number }>;
}

export default function Calls() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [started, setStarted] = useState(false);
  const [voiceText, setVoiceText] = useState("");
  const jobId = getJobId();

  const handleStartCalls = async () => {
    if (!jobId) {
      setError("Missing job_id");
      return;
    }
    setLoading(true);
    setError(null);
    setVoiceText("Calling moving companies. Please wait...");
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}/calls`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Calls failed");
      const data = await res.json();
      setQuotes(data.quotes || []);
      setStarted(true);
      setVoiceText(`Received ${data.quotes?.length || 0} quotes. Say 'Next' to continue.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setVoiceText("Failed to get quotes. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceCommand = (command: string) => {
    if (command.includes("call") || command.includes("start")) {
      handleStartCalls();
    } else if (command.includes("next") || command.includes("proceed") || command.includes("negotiate")) {
      if (started && jobId) {
        window.location.href = `/negotiate?job_id=${jobId}`;
      }
    }
  };

  useEffect(() => {
    if (jobId && !started) {
      fetch(`${API_BASE}/api/jobs/${jobId}/calls`)
        .then((res) => res.json())
        .then((data) => {
          if (data.quotes && data.quotes.length > 0) {
            setQuotes(data.quotes);
            setStarted(true);
            setVoiceText(`Loaded ${data.quotes.length} quotes. Say 'Next' to continue.`);
          }
        })
        .catch(() => {});
    }
  }, [jobId, started]);

  useEffect(() => {
    if (jobId) {
      setVoiceText("Ready to call moving companies. Say 'Call companies' to start.");
    }
  }, [jobId]);

  if (!jobId) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
        <VoiceFeedback text="Missing job ID. Please create a job first." />
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Calls</h1>
          <p className="text-gray-600">Missing job_id. Please create a job first.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
      <VoiceFeedback text={voiceText} />
      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl p-8">
        <ProgressStepper currentStep={4} />
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Moving Quotes</h1>
        <p className="text-gray-600 mb-6">
          We contacted 3 moving companies and gathered itemized quotes.
        </p>

        {!started ? (
          <div className="space-y-4">
            <button
              onClick={handleStartCalls}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              {loading ? "Calling..." : "Start Calls"}
            </button>
            
            <VoiceButton
              onCommand={handleVoiceCommand}
              label="Say 'Call companies' (Voice)"
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            />
          </div>
        ) : (
          <div className="space-y-4">
            {quotes.map((quote) => (
              <div key={quote.vendor_id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-xl font-semibold">{quote.vendor_name}</h3>
                  <span className="text-2xl font-bold text-blue-600">
                    ${quote.total.toFixed(2)}
                  </span>
                </div>
                <div className="space-y-1">
                  {quote.line_items.map((item, idx) => (
                    <div key={idx} className="flex justify-between text-sm text-gray-600">
                      <span>
                        {item.fee_type}: {item.description}
                      </span>
                      <span>${item.amount.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            <a
              href={`/negotiate?job_id=${jobId}`}
              className="block w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors text-center"
            >
              Proceed to Negotiation
            </a>
            
            <VoiceButton
              onCommand={handleVoiceCommand}
              label="Say 'Next' (Voice)"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
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