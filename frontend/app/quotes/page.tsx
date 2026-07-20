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

export default function Quotes() {
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);
  const [voiceText, setVoiceText] = useState("");
  const jobId = getJobId();

  useEffect(() => {
    if (!jobId) {
      setLoading(false);
      return;
    }
    fetch(`${API_BASE}/api/jobs/${jobId}/calls`)
      .then((res) => res.json())
      .then((data) => {
        setQuotes(data.quotes || []);
        setLoading(false);
        
        // Auto-speak quotes
        if (data.quotes && data.quotes.length > 0) {
          const firstQuote = data.quotes[0];
          setVoiceText(`Loaded ${data.quotes.length} quotes. The first quote from ${firstQuote.vendor_name} is ${firstQuote.total.toFixed(2)} dollars. Say 'Next' to continue.`);
        }
      })
      .catch(() => setLoading(false));
  }, [jobId]);

  const handleVoiceCommand = (command: string) => {
    if (command.includes("next") || command.includes("negotiate") || command.includes("proceed")) {
      if (jobId) {
        window.location.href = `/negotiate?job_id=${jobId}`;
      }
    }
  };

  if (!jobId) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
        <VoiceFeedback text="Missing job ID. Please create a job first." />
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Quotes</h1>
          <p className="text-gray-600">Missing job_id. Please create a job first.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
      <VoiceFeedback text={voiceText} />
      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl p-8">
        <ProgressStepper currentStep={5} />
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Compare Quotes</h1>
        <p className="text-gray-600 mb-6">
          Review itemized fees from all moving companies.
        </p>

        {loading ? (
          <div className="text-center text-gray-600">Loading quotes...</div>
        ) : quotes.length === 0 ? (
          <div className="text-center text-gray-600">No quotes yet. Start calls first.</div>
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
      </div>
    </div>
  );
}