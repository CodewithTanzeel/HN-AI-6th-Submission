"use client";

const steps = [
  { name: "Create Job", href: "/" },
  { name: "Voice Intake", href: "/intake/voice" },
  { name: "Documents", href: "/intake/documents" },
  { name: "Confirm", href: "/intake/confirm" },
  { name: "Calls", href: "/calls" },
  { name: "Quotes", href: "/quotes" },
  { name: "Negotiate", href: "/negotiate" },
  { name: "Report", href: "/report" },
];

export default function ProgressStepper({ currentStep }: { currentStep: number }) {
  return (
    <div className="w-full mb-8">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.name} className="flex flex-col items-center flex-1">
            <div className="flex items-center w-full">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                  index <= currentStep
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-600"
                }`}
              >
                {index + 1}
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-2 ${
                    index < currentStep ? "bg-blue-600" : "bg-gray-200"
                  }`}
                />
              )}
            </div>
            <span
              className={`text-xs mt-1 text-center ${
                index <= currentStep ? "text-blue-600 font-medium" : "text-gray-500"
              }`}
            >
              {step.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}