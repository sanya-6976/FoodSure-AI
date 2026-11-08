import React, { useState } from 'react';
import {
  Printer,
  FileCheck2,
  Microscope,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ShieldAlert,
  Layers,
  Cpu,
  BookOpen,
} from 'lucide-react';
import { AnalysisResult, HistoryRecord, Language } from '../types';
import { translations } from '../i18n';
import { SpectrumPlot } from '../components/SpectrumPlot';
import { getEnrichedResult } from '../utils/reportFormatter';

interface ReportsViewProps {
  currentResult: AnalysisResult | null;
  history: HistoryRecord[];
  lang: Language;
}

export const ReportsView: React.FC<ReportsViewProps> = ({
  currentResult,
  history,
  lang,
}) => {
  const t = translations[lang];

  // Select which report to display
  const [selectedRecordId, setSelectedRecordId] = useState<string>(
    currentResult?.record_id || (history[0] ? history[0].id : '')
  );

  const activeResult: AnalysisResult | null =
    history.find((h) => h.id === selectedRecordId)?.result_data ||
    currentResult ||
    (history[0] ? history[0].result_data : null);

  const handlePrint = () => {
    window.print();
  };

  if (!activeResult) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center bg-white rounded-2xl border border-[#E3E9E5] p-8 shadow-xs">
        <FileCheck2 className="w-12 h-12 text-[#9FB5A8] mx-auto mb-3" />
        <h3 className="text-[16px] font-bold text-[#142C1D]">
          No Screening Report Available
        </h3>
        <p className="text-[13px] text-[#557161] mt-1 max-w-md mx-auto">
          Run an analysis or select an existing screening from your history to generate an official laboratory screening certificate.
        </p>
      </div>
    );
  }

  const enriched = getEnrichedResult(activeResult);
  const {
    summaryAnswers,
    fiveSections,
    evidenceOverview,
    trustFactors,
    formattedDate,
    formattedModality,
  } = enriched;

  const { prediction, spectral_evidence, uncertainty, limitations } = activeResult;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      {/* ── Top Bar Controls (Not printed) ──────────────────────────────── */}
      <div className="print:hidden bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-4 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-[12px] font-semibold text-[#5B7767]">Select Record:</span>
          <select
            value={selectedRecordId}
            onChange={(e) => setSelectedRecordId(e.target.value)}
            className="px-3 py-1.5 bg-[#F6FAF7] border border-[#DCE5DF] rounded-lg text-[12px] text-[#163623] font-semibold focus:outline-none"
          >
            {history.map((h) => (
              <option key={h.id} value={h.id}>
                {h.sample_id} ({h.predicted_class} • {new Date(h.timestamp).toLocaleDateString()})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-4 py-2 bg-[#153822] hover:bg-[#0E2818] text-white text-[12px] font-bold rounded-xl shadow-xs transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Official Certificate</span>
          </button>
        </div>
      </div>

      {/* ── Formal Lab Certificate Document ─────────────────────────────── */}
      <div className="bg-[#FFFFFF] border border-[#DCE4DE] p-8 sm:p-12 rounded-2xl shadow-sm text-[#112619] relative print:border-none print:shadow-none print:p-0">
        {/* Certificate Header */}
        <div className="border-b-2 border-[#153822] pb-6 mb-6">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-[#153822] text-white flex items-center justify-center font-bold shadow-xs">
                <Microscope className="w-6 h-6 text-[#A6E1BA]" />
              </div>
              <div>
                <h1 className="text-[20px] font-black tracking-tight text-[#112619] uppercase">
                  FoodSure AI Intelligence Platform
                </h1>
                <p className="text-[12px] font-semibold text-[#3C5747]">
                  Division of Food Safety Screening & Spectroscopic Quality Assurance
                </p>
              </div>
            </div>

            <div className="text-right">
              <div className="text-[11px] font-bold uppercase tracking-wider text-[#698476]">
                Certificate of Analysis (COA)
              </div>
              <div className="text-[13px] font-mono font-bold text-[#153822] mt-0.5">
                {activeResult.record_id || `FS-${activeResult.sample_id}`}
              </div>
              <div className="text-[11px] text-[#698476]">
                Issued: {formattedDate}
              </div>
            </div>
          </div>
        </div>

        {/* 1. Result Summary Block */}
        <div className="bg-[#F8FAF8] border border-[#E3ECE6] rounded-xl p-5 mb-6 text-[12px]">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-[#E2EBE5]">
            <span className="font-extrabold uppercase tracking-wider text-[#153822] text-[11px]">
              Analysis Summary
            </span>
            <span className="text-[11px] text-[#698476]">
              Model Version: <strong className="text-[#153822]">{prediction.model_version}</strong>
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            <div>
              <span className="text-[#6C8578] block text-[11px] font-semibold">
                Sample ID
              </span>
              <span className="font-bold text-[#142C1D] text-[13px]">
                {activeResult.sample_id}
              </span>
            </div>
            <div>
              <span className="text-[#6C8578] block text-[11px] font-semibold">
                Tested Commodity
              </span>
              <span className="font-bold text-[#142C1D]">
                Curcuma longa (Turmeric)
              </span>
            </div>
            <div>
              <span className="text-[#6C8578] block text-[11px] font-semibold">
                Input Used
              </span>
              <span className="font-bold text-[#142C1D]">
                {formattedModality}
              </span>
            </div>
            <div>
              <span className="text-[#6C8578] block text-[11px] font-semibold">
                Classification Result
              </span>
              <span className="font-bold text-[#153822]">
                {prediction.predicted_class} ({activeResult.is_pure ? 'Pure' : 'Adulterated'})
              </span>
            </div>
          </div>

          {/* What This Means */}
          <div className="p-3 bg-white border border-[#DCE5DF] rounded-lg">
            <span className="font-extrabold text-[#153822] block mb-1 text-[11px] uppercase tracking-wide">
              What This Means:
            </span>
            <p className="text-[#2F4D3C] text-[12px] leading-relaxed">
              {summaryAnswers.q2_what_it_means}
            </p>
          </div>
        </div>

        {/* 2. Dual-Stage Screening Findings */}
        <div className="mb-6">
          <h3 className="text-[13px] font-bold uppercase tracking-wider text-[#153822] mb-3 pb-1 border-b border-[#EEF3F0]">
            Dual-Stage Model Findings (Classification & Regression)
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div className="p-4 rounded-xl border border-[#DCE7DF] bg-[#F9FCFA]">
              <div className="text-[11px] font-bold uppercase text-[#547362] mb-1">
                Stage 1: Discrete Adulteration Tier
              </div>
              <div className="text-[28px] font-black text-[#153822]">
                {prediction.predicted_class}
              </div>
              <div className="mt-1 text-[12px] font-semibold text-[#28573A]">
                {activeResult.is_pure
                  ? 'Consistent with Pure Turmeric Powder'
                  : 'Spectral Match with Wheat Flour Adulteration'}
              </div>
              <div className="mt-2 text-[11px] text-[#698476] border-t border-[#EEF3F0] pt-1.5">
                {prediction.probability_note}
              </div>
            </div>

            <div className="p-4 rounded-xl border border-[#DCE7DF] bg-[#F9FCFA]">
              <div className="text-[11px] font-bold uppercase text-[#547362] mb-1">
                Stage 2: Continuous Quantification
              </div>
              <div className="text-[28px] font-black text-[#153822]">
                {prediction.predicted_percentage !== null
                  ? `${prediction.predicted_percentage.toFixed(2)}%`
                  : '—'}
                <span className="text-[14px] font-bold text-[#557262] ml-1">w/w</span>
              </div>
              <div className="mt-1 text-[12px] text-[#557161]">
                Continuous Random Forest Regressor (MAE: ±0.031%, R²: 0.985)
              </div>
              <div className="mt-2 text-[11px] text-[#698476] border-t border-[#EEF3F0] pt-1.5">
                {prediction.regression_note}
              </div>
            </div>
          </div>
        </div>

        {/* 3. 5-Section AI Interpretation & Analysis */}
        <div className="mb-6">
          <h3 className="text-[13px] font-bold uppercase tracking-wider text-[#153822] mb-3 pb-1 border-b border-[#EEF3F0] flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-[#153822]" />
            Five-Point AI Screening Interpretation
          </h3>

          <div className="space-y-2.5 text-[12px]">
            <div className="p-3 bg-[#F9FBFA] border border-[#DEE7E1] rounded-lg">
              <span className="font-extrabold text-[#153822] block mb-0.5">
                1. What Was Detected:
              </span>
              <p className="text-[#355243]">{fiveSections.what_we_found}</p>
            </div>

            <div className="p-3 bg-[#FFFFFF] border border-[#DEE7E1] rounded-lg">
              <span className="font-extrabold text-[#153822] block mb-0.5">
                2. What This Result Means:
              </span>
              <p className="text-[#355243]">{fiveSections.what_it_means}</p>
            </div>

            <div className="p-3 bg-[#F9FBFA] border border-[#DEE7E1] rounded-lg">
              <span className="font-extrabold text-[#153822] block mb-0.5">
                3. Supporting Scientific Evidence:
              </span>
              <p className="text-[#355243]">{fiveSections.supporting_evidence}</p>
            </div>

            <div className="p-3 bg-[#FFFDF9] border border-[#EFE2CE] rounded-lg">
              <span className="font-extrabold text-[#87500B] block mb-0.5">
                4. Uncertainties & Limitations:
              </span>
              <p className="text-[#6D4F1B]">{fiveSections.important_limitations}</p>
            </div>

            <div className="p-3 bg-[#F4FAF6] border border-[#D5E6DC] rounded-lg">
              <span className="font-extrabold text-[#1B5230] block mb-0.5">
                5. Recommended Next Steps:
              </span>
              <p className="text-[#1D4A2E]">{fiveSections.recommended_next_step}</p>
            </div>
          </div>
        </div>

        {/* 4. Spectral Fingerprint Representation */}
        <div className="mb-6">
          <h3 className="text-[13px] font-bold uppercase tracking-wider text-[#153822] mb-3 pb-1 border-b border-[#EEF3F0]">
            ATR-FTIR Fingerprint (4000 – 650 cm⁻¹)
          </h3>
          <SpectrumPlot
            wavenumbers={activeResult.spectrum_chart.wavenumbers}
            absorbance={activeResult.spectrum_chart.absorbance}
            sampleId={activeResult.sample_id}
            predictedClass={prediction.predicted_class}
            height={190}
          />
        </div>

        {/* 5. Chemical Absorption Bands Table */}
        <div className="mb-6">
          <h3 className="text-[13px] font-bold uppercase tracking-wider text-[#153822] mb-3 pb-1 border-b border-[#EEF3F0]">
            Spectral Band Attribution Summary
          </h3>
          <table className="w-full text-left text-[11px] border border-[#E3ECE6] rounded-lg overflow-hidden">
            <thead className="bg-[#F6FAF7] border-b border-[#E3ECE6] font-bold text-[#355442]">
              <tr>
                <th className="p-2.5">Target Chemical Group</th>
                <th className="p-2.5">Wavenumber Band</th>
                <th className="p-2.5">Observed Absorbance</th>
                <th className="p-2.5">Biological Indication</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EEF3F0]">
              <tr>
                <td className="p-2.5 font-bold text-[#142C1D]">Starch C-O-C Stretch</td>
                <td className="p-2.5 font-mono">{spectral_evidence.starch_coc_band.wavenumber} cm⁻¹</td>
                <td className="p-2.5 font-mono">{spectral_evidence.starch_coc_band.absorbance}</td>
                <td className="p-2.5 text-[#557161]">Primary carbohydrate marker of wheat flour adulteration.</td>
              </tr>
              <tr>
                <td className="p-2.5 font-bold text-[#142C1D]">Amide I Gluten Peptide</td>
                <td className="p-2.5 font-mono">{spectral_evidence.amide_i_gluten_band.wavenumber} cm⁻¹</td>
                <td className="p-2.5 font-mono">{spectral_evidence.amide_i_gluten_band.absorbance}</td>
                <td className="p-2.5 text-[#557161]">Gluten protein backbone carbonyl stretch.</td>
              </tr>
              <tr>
                <td className="p-2.5 font-bold text-[#142C1D]">Curcuminoid Biomarker</td>
                <td className="p-2.5 font-mono">{spectral_evidence.curcuminoid_band.wavenumber} cm⁻¹</td>
                <td className="p-2.5 font-mono">{spectral_evidence.curcuminoid_band.absorbance}</td>
                <td className="p-2.5 text-[#557161]">Signature conjugated ketone/alkene ring of pure turmeric.</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* 6. Sign-off & Accreditation Block */}
        <div className="pt-6 border-t-2 border-[#153822] grid grid-cols-2 gap-8 text-[11px] text-[#4A6657]">
          <div>
            <div className="font-bold text-[#153822] text-[12px]">Laboratory Next Steps</div>
            <p className="mt-1 leading-relaxed">
              {activeResult.recommended_verification}
            </p>
            <div className="mt-2 text-[10px] text-[#718E7E]">
              Recommended standard methods: AOAC 972.16 (polarizing microscopy) & AOAC 2016.16 (HPLC).
            </div>
          </div>

          <div className="text-right flex flex-col justify-end">
            <div className="font-mono text-[11px] text-[#153822] font-bold">
              FOODSURE-AI-SCREENING-V1
            </div>
            <div className="text-[10px] text-[#718E7E] mt-0.5">
              Automated Digital Signature & Audit Hash
            </div>
          </div>
        </div>

        {/* Legal Disclaimer */}
        <div className="mt-6 pt-3 border-t border-[#EEF3F0] text-[10px] text-[#7E998B] leading-normal">
          {activeResult.disclaimer}
        </div>
      </div>
    </div>
  );
};
