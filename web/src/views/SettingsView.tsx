import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  Globe,
  Bell,
  Sliders,
  Building,
  Save,
  CheckCircle2,
} from 'lucide-react';
import { Language, NavPage } from '../types';
import { translations } from '../i18n';

interface SettingsViewProps {
  lang: Language;
  onSetLang: (lang: Language) => void;
  onNavigate: (page: NavPage) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  lang,
  onSetLang,
  onNavigate,
}) => {
  const t = translations[lang];
  const [saved, setSaved] = useState(false);
  const [depth, setDepth] = useState('detailed');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [labName, setLabName] = useState('National Agro-Food Analysis Lab');
  const [analystName, setAnalystName] = useState('Dr. S. Sharma');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* ── Top Header ─────────────────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-[20px] font-bold text-[#112619] tracking-tight">
            Platform Configuration & Preferences
          </h2>
          <p className="text-[13px] text-[#557161] mt-0.5">
            Configure linguistic localization, analysis reporting depth, and laboratory metadata.
          </p>
        </div>

        {saved && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[12px] font-semibold bg-[#E5F5EB] text-[#1E7D46] animate-in fade-in">
            <CheckCircle2 className="w-4 h-4" />
            Preferences Saved
          </span>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6 text-[12px]">
        {/* Localization & Language */}
        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[#EEF3F0]">
            <Globe className="w-4 h-4 text-[#153822]" />
            <h3 className="text-[14px] font-bold text-[#132B1D]">
              Language & Localization
            </h3>
          </div>

          <div>
            <label className="block font-bold text-[#1F3D2B] mb-2">
              Platform Interface Language
            </label>
            <div className="grid grid-cols-2 gap-3 max-w-md">
              <button
                type="button"
                onClick={() => onSetLang('en')}
                className={`p-3 rounded-xl border text-left font-semibold transition-all ${
                  lang === 'en'
                    ? 'bg-[#EBF5EE] border-[#153822] text-[#153822] ring-1 ring-[#153822]'
                    : 'bg-[#F9FCFA] border-[#DCE5DF] text-[#4E6A5A] hover:bg-[#EEF5F0]'
                }`}
              >
                <div className="text-[13px] font-bold">English</div>
                <div className="text-[11px] font-normal text-[#607D6E]">Default Scientific Interface</div>
              </button>

              <button
                type="button"
                onClick={() => onSetLang('hi')}
                className={`p-3 rounded-xl border text-left font-semibold transition-all ${
                  lang === 'hi'
                    ? 'bg-[#EBF5EE] border-[#153822] text-[#153822] ring-1 ring-[#153822]'
                    : 'bg-[#F9FCFA] border-[#DCE5DF] text-[#4E6A5A] hover:bg-[#EEF5F0]'
                }`}
              >
                <div className="text-[13px] font-bold">हिन्दी (Hindi)</div>
                <div className="text-[11px] font-normal text-[#607D6E]">भारतीय खाद्य अनुसंधान इंटरफ़ेस</div>
              </button>
            </div>
          </div>
        </div>

        {/* AI Synthesis Reporting Depth */}
        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[#EEF3F0]">
            <Sliders className="w-4 h-4 text-[#153822]" />
            <h3 className="text-[14px] font-bold text-[#132B1D]">
              Reporting & Explanation Depth
            </h3>
          </div>

          <div className="space-y-3">
            <label className="block font-bold text-[#1F3D2B]">
              Default AI Report Depth
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { id: 'executive', title: 'Executive Summary', desc: 'Concise commercial screening verdict and status badges.' },
                { id: 'detailed', title: 'Detailed Scientific', desc: 'Full biochemical reasoning and peak band explanations.' },
                { id: 'technical', title: 'Laboratory Audit', desc: 'Exhaustive wavenumber attribution and wet-lab protocols.' },
              ].map((opt) => (
                <div
                  key={opt.id}
                  onClick={() => setDepth(opt.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    depth === opt.id
                      ? 'bg-[#EBF5EE] border-[#153822] text-[#153822] ring-1 ring-[#153822]'
                      : 'bg-[#F9FCFA] border-[#DCE5DF] text-[#4E6A5A] hover:bg-[#EEF5F0]'
                  }`}
                >
                  <div className="text-[13px] font-bold text-[#132B1D]">{opt.title}</div>
                  <div className="text-[11px] text-[#557161] mt-1">{opt.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Laboratory Identification */}
        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[#EEF3F0]">
            <Building className="w-4 h-4 text-[#153822]" />
            <h3 className="text-[14px] font-bold text-[#132B1D]">
              Laboratory & Sign-Off Details
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block font-bold text-[#1F3D2B] mb-1">
                Laboratory / Institution Name
              </label>
              <input
                type="text"
                value={labName}
                onChange={(e) => setLabName(e.target.value)}
                className="w-full px-3 py-2 bg-[#F7FAF8] border border-[#D8E3DC] rounded-lg text-[#142C1D] font-medium focus:bg-white focus:border-[#153822] focus:outline-none transition-all"
              />
            </div>

            <div>
              <label className="block font-bold text-[#1F3D2B] mb-1">
                Quality Analyst / Lead Evaluator
              </label>
              <input
                type="text"
                value={analystName}
                onChange={(e) => setAnalystName(e.target.value)}
                className="w-full px-3 py-2 bg-[#F7FAF8] border border-[#D8E3DC] rounded-lg text-[#142C1D] font-medium focus:bg-white focus:border-[#153822] focus:outline-none transition-all"
              />
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            className="flex items-center gap-2 px-6 py-2.5 bg-[#153822] hover:bg-[#0E2818] text-white text-[13px] font-bold rounded-xl shadow-xs transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>Save Preferences</span>
          </button>
        </div>
      </form>
    </div>
  );
};
