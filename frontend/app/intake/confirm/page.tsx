"use client";

import { useState, useEffect } from "react";
import ProgressStepper from "../../components/ProgressStepper";
import VoiceFeedback from "../../components/VoiceFeedback";
import VoiceButton from "../../components/VoiceButton";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function ConfirmSpec() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<string[] | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [spec, setSpec] = useState<any>(null);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const [voiceText, setVoiceText] = useState("");

  useEffect(() => {
    setMounted(true);
    const params = new URLSearchParams(window.location.search);
    setJobId(params.get("job_id"));
  }, []);

  useEffect(() => {
    if (jobId) {
      // Set initial voice instruction
      setVoiceText("Please review your move details. Say 'Confirm' to proceed or 'Back' to edit.");
      
      fetch(`${API_BASE}/api/jobs/${jobId}/spec`)
        .then((res) => res.json())
        .then((data) => {
          setSpec(data.spec);
          setMissingFields(data.missing_fields || []);
          
          // Auto-speak the spec details
          if (data.spec) {
            const s = data.spec;
            setVoiceText(`Please review your move details. Origin: ${s.origin || "Not set"}. Destination: ${s.destination || "Not set"}. Distance: ${s.distance_miles ? `${s.distance_miles} miles` : "Not set"}. Say 'Confirm' to proceed.`);
          }
        })
        .catch(() => {});
    }
  }, [jobId]);

  const handleConfirm = async () => {
    if (!jobId) {
      setError("Missing job_id");
      return;
    }
    setLoading(true);
    setError(null);
    setErrorDetails(null);
    try {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        const errorData = await res.json();
        if (res.status === 400 && errorData.missing) {
          setError("Spec incomplete - missing required fields");
          setErrorDetails(errorData.missing);
          setVoiceText(`Missing required fields: ${errorData.missing.join(", ")}. Please go back and add more details.`);
        } else {
          throw new Error(errorData.message || "Confirm failed");
        }
        return;
      }
      setConfirmed(true);
      setVoiceText("Job confirmed! Taking you to call moving companies.");
      setTimeout(() => {
        window.location.href = `/calls?job_id=${jobId}`;
      }, 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setVoiceText("Failed to confirm. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceCommand = (command: string) => {
    if (command.includes("confirm") || command.includes("proceed") || command.includes("yes")) {
      handleConfirm();
    } else if (command.includes("back") || command.includes("edit")) {
      if (jobId) {
        window.location.href = `/intake/documents?job_id=${jobId}`;
      }
    }
  };

  if (!mounted || !jobId) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
        <VoiceFeedback text="Loading confirm page..." />
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Confirm Spec</h1>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
      <VoiceFeedback text={voiceText} />
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
        <ProgressStepper currentStep={3} />
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Confirm Job Spec</h1>
        <p className="text-gray-600 mb-6">
          Review your moving job details and confirm to proceed with gathering quotes.
        </p>

        {spec && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Job Details</h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-500">Origin:</span>
                <span className="ml-2 font-medium">{spec.origin || "Not set"}</span>
              </div>
              <div>
                <span className="text-gray-500">Destination:</span>
                <span className="ml-2 font-medium">{spec.destination || "Not set"}</span>
              </div>
              <div>
                <span className="text-gray-500">Distance:</span>
                <span className="ml-2 font-medium">{spec.distance_miles ? `${spec.distance_miles} miles` : "Not set"}</span>
              </div>
              <div>
                <span className="text-gray-500">Move Date:</span>
                <span className="ml-2 font-medium">{spec.move_date || "Not set"}</span>
              </div>
              <div>
                <span className="text-gray-500">Bedrooms:</span>
                <span className="ml-2 font-medium">{spec.home?.bedrooms ?? "Not set"}</span>
              </div>
              <div>
                <span className="text-gray-500">Inventory:</span>
                <span className="ml-2 font-medium">
                  {spec.inventory?.length > 0 
                    ? spec.inventory.map((i: any) => i.item).join(", ")
                    : "Not set"}
                </span>
              </div>
            </div>
          </div>
        )}

        {missingFields.length > 0 && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 text-yellow-700 rounded">
            <p className="font-medium mb-1">Missing required fields:</p>
            <ul className="list-disc list-inside text-sm">
              {missingFields.map((field) => (
                <li key={field}>{field}</li>
              ))}
            </ul>
            <a
              href={`/intake/documents?job_id=${jobId}`}
              className="mt-2 inline-block text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              ← Go back to upload documents
            </a>
          </div>
        )}

        {confirmed ? (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
            ✓ Confirmed! Redirecting to calls...
          </div>
        ) : (
          <div className="space-y-4">
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              {loading ? "Confirming..." : "Confirm & Proceed"}
            </button>
            
            <VoiceButton
              onCommand={handleVoiceCommand}
              label="Say 'Confirm' (Voice)"
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            />
            
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
                {errorDetails && (
                  <ul className="mt-2 list-disc list-inside text-sm">
                    {errorDetails.map((field) => (
                      <li key={field}>{field}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}