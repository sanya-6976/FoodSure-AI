import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Loader2,
  Microscope,
  Cpu,
  Sparkles,
  ShieldAlert,
  FileCheck2,
} from 'lucide-react';

interface ProcessingModalProps {
  isOpen: boolean;
  sampleId: string;
  hasGeminiKey: boolean;
  onComplete?: () => void;
}

interface Stage {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}

export const ProcessingModal: React.FC<ProcessingModalProps> = ({
  isOpen,
  sampleId,
  hasGeminiKey,
}) => {
  const [currentStageIdx, setCurrentStageIdx] = useState(0);

  const stages: Stage[] = [
    {
      id: 'validation',
      label: 'Input & Range Validation',
      description: 'Checking baseline absorbance and numeric continuity across spectral sweep.',
      icon: <CheckCircle2 className="w-4 h-4" />,
    },
    {
      id: 'schema',
      label: '2,522-Wavenumber Alignment',
      description: 'Aligning infrared frequencies (4000–650 cm⁻¹) with saved training contract.',
      icon: <Microscope className="w-4 h-4" />,
    },
    {
      id: 'inference',
      label: 'Dual-Stage Model Inference',
      description: 'Executing Logistic Regression classifier & Random Forest regressor via PCA (91 components).',
      icon: <Cpu className="w-4 h-4" />,
    },
    {
      id: 'evidence',
      label: 'Chemical Band Peak Attribution',
      description: 'Isolating starch C-O-C bands (~1020 cm⁻¹) and gluten peptide Amide I (~1650 cm⁻¹).',
      icon: <FileCheck2 className="w-4 h-4" />,
    },
    {
      id: 'uncertainty',
      label: 'Boundary & Uncertainty Audit',
      description: 'Evaluating decision hyperplane proximity and out-of-distribution scope.',
      icon: <ShieldAlert className="w-4 h-4" />,
    },
    {
      id: 'ai_synthesis',
      label: hasGeminiKey ? 'Gemini AI Scientific Synthesis' : 'Deterministic Evidence Synthesis',
      description: hasGeminiKey
        ? 'Generating plain-language biochemical interpretation and laboratory verification plan.'
        : 'Compiling structured scientific findings and recommended testing protocols.',
      icon: <Sparkles className="w-4 h-4" />,
    },
  ];

  useEffect(() => {
    if (!isOpen) {
      setCurrentStageIdx(0);
      return;
    }

    // Advance stages naturally to match real backend latency
    const interval = setInterval(() => {
      setCurrentStageIdx((prev) => {
        if (prev < stages.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 450);

    return () => clearInterval(interval);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-[#0F2417]/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in">
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#DCE5DF] shadow-2xl w-full max-w-md p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 pb-4 border-b border-[#EDF3EF]">
          <div className="w-9 h-9 rounded-xl bg-[#E8F3EC] text-[#153822] flex items-center justify-center">
            <Loader2 className="w-5 h-5 animate-spin text-[#153822]" />
          </div>
          <div>
            <h3 className="text-[15px] font-bold text-[#142C1D]">
              Processing FTIR Analysis
            </h3>
            <p className="text-[12px] text-[#557161]">
              Sample: <span className="font-semibold text-[#1B3F28]">{sampleId}</span>
            </p>
          </div>
        </div>

        {/* Processing Stages List */}
        <div className="py-4 space-y-3">
          {stages.map((stage, idx) => {
            const isCompleted = idx < currentStageIdx;
            const isActive = idx === currentStageIdx;
            const isPending = idx > currentStageIdx;

            return (
              <div
                key={stage.id}
                className={`flex items-start gap-3 p-2.5 rounded-xl transition-all ${
                  isActive
                    ? 'bg-[#F2F7F4] border border-[#CFDFD4]'
                    : isCompleted
                    ? 'opacity-80'
                    : 'opacity-40'
                }`}
              >
                <div className="mt-0.5 flex-shrink-0">
                  {isCompleted ? (
                    <div className="w-5 h-5 rounded-full bg-[#1E7D46] text-white flex items-center justify-center">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    </div>
                  ) : isActive ? (
                    <div className="w-5 h-5 rounded-full bg-[#153822] text-white flex items-center justify-center">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    </div>
                  ) : (
                    <div className="w-5 h-5 rounded-full border border-[#BED0C5] bg-white flex items-center justify-center">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#BED0C5]" />
                    </div>
                  )}
                </div>

                <div className="min-w-0">
                  <div
                    className={`text-[12px] font-bold ${
                      isActive
                        ? 'text-[#153822]'
                        : isCompleted
                        ? 'text-[#2D4A39]'
                        : 'text-[#6C8376]'
                    }`}
                  >
                    {stage.label}
                  </div>
                  <div className="text-[11px] text-[#587364] leading-tight mt-0.5">
                    {stage.description}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Note */}
        <div className="pt-3 border-t border-[#EDF3EF] flex items-center justify-between text-[11px] text-[#698476]">
          <span>Dual-stage screening architecture</span>
          <span className="font-semibold text-[#183623]">Leakage-Free</span>
        </div>
      </div>
    </div>
  );
};
