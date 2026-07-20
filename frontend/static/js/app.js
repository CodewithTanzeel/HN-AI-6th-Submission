const NegotiatorAPI = {
  async createJob() {
    const res = await fetch("/api/jobs", { method: "POST" });
    if (!res.ok) throw new Error("Failed to create job");
    return res.json();
  },
  async submitVoice(jobId, transcript) {
    const res = await fetch(`/api/jobs/${jobId}/voice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript }),
    });
    if (!res.ok) throw new Error("Voice intake failed");
    return res.json();
  },
  async uploadDocument(jobId, file) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`/api/jobs/${jobId}/documents`, { method: "POST", body: form });
    if (!res.ok) throw new Error("Document upload failed");
    return res.json();
  },
  async getSpec(jobId) {
    const res = await fetch(`/api/jobs/${jobId}/spec`);
    if (!res.ok) throw new Error("Failed to load spec");
    return res.json();
  },
  async confirmSpec(jobId) {
    const res = await fetch(`/api/jobs/${jobId}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail?.message || "Confirm failed");
    }
    return res.json();
  },
  async startCalls(jobId) {
    const res = await fetch(`/api/jobs/${jobId}/calls`, { method: "POST" });
    if (!res.ok) throw new Error("Calls failed");
    return res.json();
  },
  async getCalls(jobId) {
    const res = await fetch(`/api/jobs/${jobId}/calls`);
    if (!res.ok) throw new Error("Failed to load calls");
    return res.json();
  },
  async negotiate(jobId) {
    const res = await fetch(`/api/jobs/${jobId}/negotiate`, { method: "POST" });
    if (!res.ok) throw new Error("Negotiation failed");
    return res.json();
  },
  async getReport(jobId) {
    const res = await fetch(`/api/jobs/${jobId}/report`);
    if (!res.ok) throw new Error("Report failed");
    return res.json();
  },
};
