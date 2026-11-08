import React from 'react';
import { Microscope, Sparkles } from 'lucide-react';

export const SplashLoader: React.FC = () => {
  return (
    <div className="fixed inset-0 bg-[#FBFDFB] flex flex-col items-center justify-center z-50">
      <div className="text-center max-w-sm px-6">
        {/* Animated Brand Emblem */}
        <div className="relative mx-auto w-16 h-16 mb-5">
          <div className="absolute inset-0 rounded-2xl bg-[#E8F3EC] animate-ping opacity-30" />
          <div className="relative w-16 h-16 rounded-2xl bg-[#153822] text-white flex items-center justify-center shadow-md">
            <Microscope className="w-8 h-8 text-[#A6E1BA]" strokeWidth={2} />
          </div>
        </div>

        {/* Title & Tagline */}
        <h1 className="text-[20px] font-bold text-[#112619] tracking-tight">
          FoodSure AI
        </h1>
        <p className="text-[13px] font-medium text-[#486353] mt-1 mb-6">
          Intelligent Food Quality Screening
        </p>

        {/* Refined Indeterminate Loading Line */}
        <div className="w-48 h-1 bg-[#E1ECE4] rounded-full mx-auto overflow-hidden relative">
          <div className="absolute inset-y-0 bg-[#153822] w-1/3 rounded-full animate-[shimmer_1.4s_infinite_ease-in-out]" />
        </div>

        <p className="text-[11px] text-[#718C7E] mt-3 font-medium">
          Initializing ATR-FTIR Spectroscopic Engine...
        </p>
      </div>

      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-150%); }
          100% { transform: translateX(350%); }
        }
      `}</style>
    </div>
  );
};
