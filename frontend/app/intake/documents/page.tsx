"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import ProgressStepper from "../../components/ProgressStepper";
import VoiceFeedback from "../../components/VoiceFeedback";
import VoiceButton from "../../components/VoiceButton";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function DocumentIntake() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsedSpec, setParsedSpec] = useState<any>(null);
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
    if (mounted) {
      setVoiceText("Upload a quote or inventory document, or say 'Skip' to continue without documents.");
    }
  }, [mounted]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobId || !file) {
      setError("Missing job_id or file");
      return;
    }
    setLoading(true);
    setError(null);
    setParsedSpec(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}/documents`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || "Document upload failed");
      }
      const data = await res.json();
      setParsedSpec(data.spec);
      setVoiceText("Document uploaded successfully. Taking you to confirm page.");
      setTimeout(() => {
        window.location.href = `/intake/confirm?job_id=${jobId}`;
      }, 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setVoiceText("Failed to upload document. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    if (jobId) {
      setVoiceText("Skipping documents. Taking you to confirm page.");
      setTimeout(() => {
        window.location.href = `/intake/confirm?job_id=${jobId}`;
      }, 1000);
    }
  };

  const handleVoiceCommand = useCallback((command: string) => {
    if (command.includes("skip") || command.includes("next")) {
      handleSkip();
    } else if (command.includes("upload") || command.includes("submit")) {
      const form = document.querySelector("form");
      if (form) form.dispatchEvent(new Event("submit", { cancelable: true }));
    }
  }, [handleSkip]);

  // Keep the ref updated
  useEffect(() => {
    onCommandRef.current = handleVoiceCommand;
  }, [handleVoiceCommand]);

  if (!mounted || !jobId) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
        <VoiceFeedback text="Loading document upload page..." />
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Document Upload</h1>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-4">
      <VoiceFeedback text={voiceText} />
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
        <ProgressStepper currentStep={2} />
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Document Upload</h1>
        <p className="text-gray-600 mb-6">
          Upload a quote or inventory document for this moving job.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full border border-gray-300 rounded-lg p-3"
            accept=".txt,.pdf,.docx"
          />
          <button
            type="submit"
            disabled={loading || !file}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            {loading ? "Uploading..." : "Upload Document"}
          </button>
          
          <button
            type="button"
            onClick={handleSkip}
            disabled={loading}
            className="w-full bg-gray-300 hover:bg-gray-400 text-gray-700 font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            Skip Documents
          </button>
          
          <VoiceButton
            onCommand={handleVoiceCommand}
            label="Say 'Skip' or 'Upload' (Voice)"
            className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          />
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
        </form>

        {parsedSpec && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 text-green-700 rounded">
            <p className="font-medium mb-2">Document parsed successfully!</p>
            <div className="text-sm">
              <p>Origin: {parsedSpec.origin || "Not found"}</p>
              <p>Destination: {parsedSpec.destination || "Not found"}</p>
              <p>Distance: {parsedSpec.distance_miles ? `${parsedSpec.distance_miles} miles` : "Not found"}</p>
              <p>Bedrooms: {parsedSpec.home?.bedrooms ?? "Not found"}</p>
              <p>Inventory: {parsedSpec.inventory?.length > 0 ? parsedSpec.inventory.map((i: any) => i.item).join(", ") : "Not found"}</p>
            </div>
            <p className="text-sm mt-2">Redirecting to confirm page...</p>
          </div>
        )}
      </div>
    </div>
  );
}