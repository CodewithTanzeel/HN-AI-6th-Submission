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

interface Report {
  recommended_vendor_id: string;
  ranked_quotes: Array<{
    vendor_id: string;
    vendor_name: string;
    total: number;
    negotiated_total: number;
    red_flags: string[];
  }>;
  summary: string;
}

export default function Report() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [voiceText, setVoiceText] = useState("");
  const jobId = getJobId();

  useEffect(() => {
    if (!jobId) {
      setLoading(false);
      setError("Missing job_id");
      return;
    }
    fetch(`${API_BASE}/api/jobs/${jobId}/report`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load report");
        return res.json();
      })
      .then((data) => {
        setReport(data);
        setLoading(false);
        
        // Auto-speak the report
        if (data.ranked_quotes && data.ranked_quotes.length > 0) {
          const topQuote = data.ranked_quotes[0];
          setVoiceText(`Your recommended mover is ${topQuote.vendor_name} with a total of ${topQuote.negotiated_total.toFixed(2)} dollars. ${data.summary}`);
        }
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Unknown error");
        setLoading(false);
        setVoiceText("Failed to load report. Please try again.");
      });
  }, [jobId]);

  const handleVoiceCommand = (command: string) => {
    if (command.includes("new") || command.includes("start") || command.includes("home")) {
      window.location.href = "/";
    }
  };

  if (!jobId) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
        <VoiceFeedback text="Missing job ID. Please create a job first." />
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Report</h1>
          <p className="text-gray-600">Missing job_id. Please create a job first.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
      <VoiceFeedback text={voiceText} />
      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl p-8">
        <ProgressStepper currentStep={7} />
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Final Report</h1>
        <p className="text-gray-600 mb-6">
          Your ranked recommendation based on quotes and negotiations.
        </p>

        {loading ? (
          <div className="text-center text-gray-600">Loading report...</div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        ) : report ? (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-green-800 mb-2">
                Recommended: {report.ranked_quotes[0]?.vendor_name || "N/A"}
              </h2>
              <p className="text-green-700">{report.summary}</p>
            </div>

            <div className="space-y-4">
              <h3 className="text-xl font-semibold">All Quotes (Ranked)</h3>
              {report.ranked_quotes.map((quote, idx) => (
                <div key={quote.vendor_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <div>
                      <span className="text-lg font-semibold">#{idx + 1} {quote.vendor_name}</span>
                      {report.recommended_vendor_id === quote.vendor_id && (
                        <span className="ml-2 bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                          Recommended
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-600">
                        ${quote.negotiated_total.toFixed(2)}
                      </div>
                      {quote.negotiated_total !== quote.total && (
                        <div className="text-sm text-gray-500 line-through">
                          ${quote.total.toFixed(2)}
                        </div>
                      )}
                    </div>
                  </div>
                  {quote.red_flags.length > 0 && (
                    <div className="mt-2 text-sm text-red-600">
                      ⚠️ {quote.red_flags.join(", ")}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <a
              href="/"
              className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors text-center"
            >
              Start New Job
            </a>
            
            <VoiceButton
              onCommand={handleVoiceCommand}
              label="Say 'Start new job' (Voice)"
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            />
          </div>
        ) : (
          <div className="text-center text-gray-600">No report available.</div>
        )}
      </div>
    </div>
  );
}