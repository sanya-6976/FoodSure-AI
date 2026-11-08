import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  FileText,
  Download,
  RefreshCw,
  Microscope,
  Cpu,
  Layers,
  ShieldAlert,
  Sparkles,
  BookOpen,
  Info,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Check,
  Eye,
  Code2,
  Activity,
  ArrowRight,
  ShieldCheck,
  Copy,
} from 'lucide-react';
import { AnalysisResult, Language, NavPage } from '../types';
import { translations } from '../i18n';
import { SpectrumPlot } from '../components/SpectrumPlot';
import { getEnrichedResult } from '../utils/reportFormatter';

interface AnalysisResultsViewProps {
  result: AnalysisResult;
  lang: Language;
  onNavigate: (page: NavPage) => void;
  onViewReport: (result: AnalysisResult) => void;
  onNewAnalysis: () => void;
}

export const AnalysisResultsView: React.FC<AnalysisResultsViewProps> = ({
  result,
  lang,
  onNavigate,
  onViewReport,
  onNewAnalysis,
}) => {
  const t = translations[lang];
  const [viewMode, setViewMode] = useState<'simple' | 'technical'>('simple');
  const [glossaryOpen, setGlossaryOpen] = useState<boolean>(false);
  const [copiedJson, setCopiedJson] = useState<boolean>(false);

  const enriched = getEnrichedResult(result);
  const {
    summaryAnswers,
    fiveSections,
    evidenceOverview,
    trustFactors,
    glossaryTerms,
    formattedDate,
    formattedModality,
  } = enriched;

  const { prediction, spectral_evidence, uncertainty, limitations } = result;

  const handleExportJson = () => {
    const dataStr =
      'data:text/json;charset=utf-8,' +
      encodeURIComponent(JSON.stringify(result, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `${result.sample_id}_foodsure_report.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const handleExportMarkdown = () => {
    const md = `# FoodSure AI Quality & Adulteration Screening Report
**Sample ID:** ${result.sample_id}  
**Analysis Date:** ${formattedDate}  
**Input Used:** ${formattedModality}  
**Classification Result:** ${prediction.predicted_class} (${result.is_pure ? 'Pure Turmeric' : 'Adulterated with Wheat Flour'})  
**Estimated Adulteration Level:** ${prediction.predicted_percentage !== null ? prediction.predicted_percentage.toFixed(2) + '% w/w' : 'N/A'}  
**Model Version:** ${prediction.model_version}  

---

## What This Means
${summaryAnswers.q2_what_it_means}

---

## 5-Section AI Analysis & Findings
### 1. What We Found
${fiveSections.what_we_found}

### 2. What It Means
${fiveSections.what_it_means}

### 3. Supporting Evidence
${fiveSections.supporting_evidence}

### 4. Important Limitations
${fiveSections.important_limitations}

### 5. Recommended Next Steps
${fiveSections.recommended_next_step}

---

## Chemical Absorption Bands (ATR-FTIR)
- **Starch C-O-C Band (~1020 cm⁻¹):** ${spectral_evidence.starch_coc_band.wavenumber} cm⁻¹ (Absorbance: ${spectral_evidence.starch_coc_band.absorbance})
- **Amide I Gluten Band (~1650 cm⁻¹):** ${spectral_evidence.amide_i_gluten_band.wavenumber} cm⁻¹ (Absorbance: ${spectral_evidence.amide_i_gluten_band.absorbance})
- **Curcuminoid Biomarker (~1510 cm⁻¹):** ${spectral_evidence.curcuminoid_band.wavenumber} cm⁻¹ (Absorbance: ${spectral_evidence.curcuminoid_band.absorbance})

---

## Recommended Verification Protocol
${result.recommended_verification}

---
*Notice: ${result.disclaimer}*
`;
    const dataStr = 'data:text/markdown;charset=utf-8,' + encodeURIComponent(md);
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `${result.sample_id}_foodsure_report.md`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* ── Top Header & Mode Toggle ────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-5 sm:p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <span className="text-[11px] font-semibold text-[#5A7666]">
              Screening Findings for:
            </span>
            <span className="text-[15px] font-bold text-[#112619]">
              {result.sample_id}
            </span>
            {result.actual_level !== null && (
              <span className="text-[11px] px-2.5 py-0.5 rounded-md bg-[#EDF3EF] text-[#1E4B31] font-semibold border border-[#D5E3DA]">
                Dataset Benchmark Truth: {result.actual_level}%
              </span>
            )}
          </div>
          <h1 className="text-[22px] font-black text-[#112619] tracking-tight">
            Food Quality & Adulteration Report
          </h1>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Simple vs Technical View Toggle */}
          <div className="inline-flex p-1 bg-[#EEF4F0] border border-[#D8E3DC] rounded-xl text-[12px] font-bold">
            <button
              onClick={() => setViewMode('simple')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                viewMode === 'simple'
                  ? 'bg-white text-[#153822] shadow-xs'
                  : 'text-[#567262] hover:text-[#153822]'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Simple View</span>
            </button>
            <button
              onClick={() => setViewMode('technical')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                viewMode === 'technical'
                  ? 'bg-[#153822] text-white shadow-xs'
                  : 'text-[#567262] hover:text-[#153822]'
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Technical View</span>
            </button>
          </div>

          {/* Action Buttons */}
          <button
            onClick={() => onViewReport(result)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-[#153822] hover:bg-[#0E2818] text-white text-[12px] font-bold rounded-xl shadow-xs transition-colors"
          >
            <FileText className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Official Certificate</span>
            <span className="sm:hidden">Certificate</span>
          </button>

          <button
            onClick={handleExportJson}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#F6FAF7] hover:bg-[#EEF5F0] text-[#1E432B] border border-[#DCE5DF] text-[12px] font-semibold rounded-xl transition-colors"
            title="Download JSON Report"
          >
            <Download className="w-3.5 h-3.5" />
            <span>JSON</span>
          </button>

          <button
            onClick={handleExportMarkdown}
            className="flex items-center gap-1.5 px-3 py-2 bg-[#F6FAF7] hover:bg-[#EEF5F0] text-[#1E432B] border border-[#DCE5DF] text-[12px] font-semibold rounded-xl transition-colors"
            title="Download Markdown Report"
          >
            <Download className="w-3.5 h-3.5" />
            <span>MD</span>
          </button>

          <button
            onClick={onNewAnalysis}
            className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-[#F2F7F4] text-[#153822] border border-[#D0DDD4] text-[12px] font-semibold rounded-xl transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Sample</span>
          </button>
        </div>
      </div>

      {/* ── 1. Result Summary Header Block ──────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#DCE6E0] p-6 shadow-xs">
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#EEF3F0]">
          <h2 className="text-[14px] font-bold uppercase tracking-wider text-[#153822] flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#1E7D46]" />
            Analysis Summary
          </h2>
          <span className="text-[11px] font-medium text-[#658172]">
            Model Version: <strong className="text-[#153822]">{prediction.model_version}</strong>
          </span>
        </div>

        {/* Key Summary Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5 mb-5 text-[12px]">
          <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E3ECE7]">
            <span className="text-[11px] font-semibold text-[#668273] block mb-0.5">
              Sample ID
            </span>
            <span className="font-extrabold text-[#112619] text-[14px]">
              {result.sample_id}
            </span>
          </div>

          <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E3ECE7]">
            <span className="text-[11px] font-semibold text-[#668273] block mb-0.5">
              Analysis Date
            </span>
            <span className="font-bold text-[#142C1D] truncate block">
              {formattedDate}
            </span>
          </div>

          <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E3ECE7]">
            <span className="text-[11px] font-semibold text-[#668273] block mb-0.5">
              Input Modality
            </span>
            <span className="font-bold text-[#142C1D] truncate block" title={formattedModality}>
              ATR-FTIR Spectroscopy
            </span>
          </div>

          <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E3ECE7]">
            <span className="text-[11px] font-semibold text-[#668273] block mb-0.5">
              Classification Result
            </span>
            <span className="font-black text-[#153822] text-[14px]">
              {prediction.predicted_class} ({result.is_pure ? 'Pure' : 'Adulterated'})
            </span>
          </div>

          <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#E3ECE7]">
            <span className="text-[11px] font-semibold text-[#668273] block mb-0.5">
              Adulteration Level
            </span>
            <span className="font-black text-[#153822] text-[14px]">
              {prediction.predicted_percentage !== null
                ? `${prediction.predicted_percentage.toFixed(2)}% w/w`
                : 'N/A'}
            </span>
          </div>
        </div>

        {/* "What This Means" Callout */}
        <div className="p-4 bg-[#F5FAF7] border-l-4 border-[#1E7D46] rounded-r-xl border-y border-r border-[#E0EBE4]">
          <h3 className="text-[13px] font-extrabold text-[#163B23] mb-1 flex items-center gap-1.5">
            <Info className="w-4 h-4 text-[#1E7D46]" />
            What this means
          </h3>
          <p className="text-[13px] text-[#294B37] leading-relaxed">
            {summaryAnswers.q2_what_it_means}
          </p>
        </div>
      </div>

      {/* ── 2. Separate Classification & Regression Metric Panels ────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Discrete Classification Card */}
        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-[#5C7969] text-[12px] font-bold uppercase tracking-wider mb-2">
              <span className="flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-[#153822]" />
                Classification (Discrete Pattern)
              </span>
              <span className="text-[11px] font-medium text-[#738F80]">
                Multinomial Logistic Reg
              </span>
            </div>

            <div className="flex items-baseline gap-3 my-3">
              <div className="text-[38px] font-black text-[#112619] tracking-tight leading-none">
                {prediction.predicted_class}
              </div>
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[12px] font-bold ${
                  result.is_pure
                    ? 'bg-[#E5F5EB] text-[#1E7D46]'
                    : 'bg-[#FFF3E0] text-[#B86B14]'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    result.is_pure ? 'bg-[#1E7D46]' : 'bg-[#B86B14]'
                  }`}
                />
                {result.is_pure ? 'Pure Turmeric (0% Adulteration)' : 'Wheat Flour Adulterated'}
              </span>
            </div>

            <p className="text-[12px] text-[#52705F] leading-relaxed">
              Discrete classification matches the complete infrared curve pattern against 7 pre-trained laboratory tiers (0%, 1%, 2%, 3%, 5%, 7%, 9%).
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-[#EEF3F0] text-[11px] text-[#698476]">
            {prediction.probability_note}
          </div>
        </div>

        {/* Continuous Regression Card */}
        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-[#5C7969] text-[12px] font-bold uppercase tracking-wider mb-2">
              <span className="flex items-center gap-1.5">
                <Microscope className="w-4 h-4 text-[#153822]" />
                Regression (Continuous Estimate)
              </span>
              <span className="text-[11px] font-medium text-[#738F80]">
                Random Forest Regressor
              </span>
            </div>

            <div className="flex items-baseline gap-2 my-3">
              <div className="text-[38px] font-black text-[#112619] tracking-tight leading-none">
                {prediction.predicted_percentage !== null
                  ? `${prediction.predicted_percentage.toFixed(2)}%`
                  : '—'}
              </div>
              <span className="text-[14px] font-bold text-[#557262]">w/w concentration</span>
            </div>

            <p className="text-[12px] text-[#52705F] leading-relaxed">
              Continuous quantification independently calculates wheat flour concentration in the sample (Cross-Validation MAE: ±0.031%, R²: 0.985).
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-[#EEF3F0] text-[11px] text-[#698476]">
            {prediction.regression_note}
          </div>
        </div>
      </div>

      {/* ── CONDITIONAL VIEW MODE: SIMPLE VIEW VS TECHNICAL VIEW ──────────── */}
      {viewMode === 'simple' ? (
        <>
          {/* ── 3. Natural 5-Section AI Interpretation ────────────────────── */}
          <div className="bg-[#FFFFFF] rounded-2xl border border-[#DCE5DF] p-6 shadow-xs space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-[#EEF3F0]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#EAF5EE] text-[#153822] flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-[#153822]" />
                </div>
                <div>
                  <h3 className="text-[16px] font-black text-[#112619]">
                    AI Interpretation & Findings
                  </h3>
                  <p className="text-[11px] text-[#62806F]">
                    Plain-language synthesis answering the 5 fundamental food safety questions
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-3.5 text-[13px] leading-relaxed">
              {/* Section 1 */}
              <div className="p-4 bg-[#F8FAF9] rounded-xl border border-[#E2EBE5]">
                <h4 className="text-[12px] font-extrabold text-[#153822] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded-full bg-[#153822] text-white text-[10px] flex items-center justify-center font-bold">1</span>
                  What We Found
                </h4>
                <p className="text-[#2C4837]">{fiveSections.what_we_found}</p>
              </div>

              {/* Section 2 */}
              <div className="p-4 bg-[#FFFFFF] rounded-xl border border-[#E2EBE5]">
                <h4 className="text-[12px] font-extrabold text-[#153822] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded-full bg-[#153822] text-white text-[10px] flex items-center justify-center font-bold">2</span>
                  What It Means
                </h4>
                <p className="text-[#2C4837]">{fiveSections.what_it_means}</p>
              </div>

              {/* Section 3 */}
              <div className="p-4 bg-[#F8FAF9] rounded-xl border border-[#E2EBE5]">
                <h4 className="text-[12px] font-extrabold text-[#153822] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded-full bg-[#153822] text-white text-[10px] flex items-center justify-center font-bold">3</span>
                  Supporting Evidence
                </h4>
                <p className="text-[#2C4837]">{fiveSections.supporting_evidence}</p>
              </div>

              {/* Section 4 */}
              <div className="p-4 bg-[#FFFDF9] rounded-xl border border-[#F0E6D3]">
                <h4 className="text-[12px] font-extrabold text-[#87500B] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded-full bg-[#87500B] text-white text-[10px] flex items-center justify-center font-bold">4</span>
                  Important Limitations
                </h4>
                <p className="text-[#6D4F1B]">{fiveSections.important_limitations}</p>
              </div>

              {/* Section 5 */}
              <div className="p-4 bg-[#F4FAF6] rounded-xl border border-[#D5E6DC]">
                <h4 className="text-[12px] font-extrabold text-[#1B5230] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <span className="w-5 h-5 rounded-full bg-[#1B5230] text-white text-[10px] flex items-center justify-center font-bold">5</span>
                  Recommended Next Steps
                </h4>
                <p className="text-[#1D4A2E]">{fiveSections.recommended_next_step}</p>
              </div>
            </div>
          </div>

          {/* ── 4. Structured Evidence Overview ────────────────────────────── */}
          <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs">
            <h3 className="text-[14px] font-bold uppercase tracking-wider text-[#153822] mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#153822]" />
              Structured Evidence Overview
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 text-[12px]">
              <div className="p-3.5 bg-[#F6FAF7] border border-[#DEE9E2] rounded-xl">
                <span className="text-[11px] font-semibold text-[#5A7A68] block mb-1">
                  Input Validation
                </span>
                <span className="font-extrabold text-[#153822] flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#1E7D46] shrink-0" />
                  <span>{evidenceOverview.input_validation}</span>
                </span>
              </div>

              <div className="p-3.5 bg-[#F6FAF7] border border-[#DEE9E2] rounded-xl">
                <span className="text-[11px] font-semibold text-[#5A7A68] block mb-1">
                  Analyzed Modality
                </span>
                <span className="font-extrabold text-[#153822] flex items-center gap-1.5">
                  <Microscope className="w-4 h-4 text-[#153822] shrink-0" />
                  <span>{evidenceOverview.analyzed_modality}</span>
                </span>
              </div>

              <div className="p-3.5 bg-[#F6FAF7] border border-[#DEE9E2] rounded-xl">
                <span className="text-[11px] font-semibold text-[#5A7A68] block mb-1">
                  Feature Schema Compatibility
                </span>
                <span className="font-extrabold text-[#153822] flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-[#153822] shrink-0" />
                  <span>{evidenceOverview.feature_compatibility}</span>
                </span>
              </div>

              <div className="p-3.5 bg-[#F6FAF7] border border-[#DEE9E2] rounded-xl">
                <span className="text-[11px] font-semibold text-[#5A7A68] block mb-1">
                  Evidence Availability
                </span>
                <span className="font-extrabold text-[#153822] flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-[#1E7D46] shrink-0" />
                  <span>{evidenceOverview.evidence_availability}</span>
                </span>
              </div>
            </div>
          </div>

          {/* ── 5. Simplified Spectrum Curve ───────────────────────────────── */}
          <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs">
            <div className="flex items-center justify-between pb-3 mb-2 border-b border-[#EEF3F0]">
              <div>
                <h3 className="text-[14px] font-bold text-[#142C1D]">
                  Infrared Spectral Fingerprint (ATR-FTIR)
                </h3>
                <p className="text-[11px] text-[#698476]">
                  Full-range absorbance curve from 4000 cm⁻¹ to 650 cm⁻¹ (annotated diagnostic bands)
                </p>
              </div>
            </div>

            <SpectrumPlot
              wavenumbers={result.spectrum_chart.wavenumbers}
              absorbance={result.spectrum_chart.absorbance}
              sampleId={result.sample_id}
              actualLevel={result.actual_level}
              predictedClass={prediction.predicted_class}
              showAnnotations={true}
              height={250}
            />
          </div>

          {/* ── 6. "How Much Should You Trust This Result?" ───────────────── */}
          <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#EEF3F0]">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-[#153822]" />
                <h3 className="text-[15px] font-extrabold text-[#112619]">
                  How Much Should You Trust This Result?
                </h3>
              </div>
              <span className="text-[11px] px-2.5 py-1 rounded-md bg-[#EDF3EF] text-[#224831] font-bold uppercase">
                Audit Status: {uncertainty.status}
              </span>
            </div>

            <p className="text-[12px] text-[#557161]">
              Every machine learning prediction has boundaries. FoodSure AI evaluates input validity, calibration boundaries, and dataset coverage transparently:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {trustFactors.map((factor, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border text-[12px] ${
                    factor.status === 'verified'
                      ? 'bg-[#F6FAF7] border-[#D5E5DC]'
                      : 'bg-[#FFFDF9] border-[#EFE2CE]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-extrabold text-[#163B23] flex items-center gap-1.5">
                      {factor.status === 'verified' ? (
                        <CheckCircle2 className="w-4 h-4 text-[#1E7D46]" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-[#B86B14]" />
                      )}
                      {factor.label}
                    </span>
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                        factor.status === 'verified'
                          ? 'bg-[#E5F5EB] text-[#1E7D46]'
                          : 'bg-[#FDEFD9] text-[#8C520E]'
                      }`}
                    >
                      {factor.status === 'verified' ? 'Verified' : 'Caution'}
                    </span>
                  </div>
                  <p
                    className={
                      factor.status === 'verified' ? 'text-[#3E5C4A]' : 'text-[#6F511E]'
                    }
                  >
                    {factor.explanation}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* ── 7. Collapsible "How to Read This Result" Glossary ─────────── */}
          <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] overflow-hidden shadow-xs">
            <button
              onClick={() => setGlossaryOpen(!glossaryOpen)}
              className="w-full p-5 flex items-center justify-between text-left hover:bg-[#F9FCFA] transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-[#EBF5EE] text-[#153822] flex items-center justify-center">
                  <BookOpen className="w-4 h-4 text-[#153822]" />
                </div>
                <div>
                  <h4 className="text-[14px] font-bold text-[#142C1D]">
                    How to Read This Result (Plain-Language Glossary)
                  </h4>
                  <p className="text-[11px] text-[#698476]">
                    Clear definitions of spectroscopy and machine learning terms used in this report
                  </p>
                </div>
              </div>

              <div className="p-1 rounded-lg bg-[#F0F5F2] text-[#153822]">
                {glossaryOpen ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </div>
            </button>

            {glossaryOpen && (
              <div className="p-6 pt-0 border-t border-[#EEF3F0] grid grid-cols-1 md:grid-cols-2 gap-4 text-[12px] mt-2">
                {glossaryTerms.map((term, i) => (
                  <div key={i} className="p-3 bg-[#F8FAF9] border border-[#DEE7E1] rounded-xl">
                    <span className="font-extrabold text-[#153822] block mb-0.5">
                      {term.term}
                    </span>
                    <p className="text-[#4E6B5A] text-[11px] leading-relaxed">
                      {term.explanation}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      ) : (
        /* ── TECHNICAL VIEW FOR RESEARCHERS & ANALYSTS ───────────────────── */
        <div className="space-y-6">
          {/* Chemical Absorption Bands Table */}
          <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#EEF3F0]">
              <div>
                <h3 className="text-[15px] font-extrabold text-[#142C1D]">
                  Infrared Wavenumber Peak Attribution Table
                </h3>
                <p className="text-[11px] text-[#698476]">
                  Diagnostic spectral biomarkers extracted from the 2,522-point raw ATR-FTIR scan
                </p>
              </div>
              <span className="text-[11px] font-mono text-[#1E7D46] bg-[#E8F3EC] px-2.5 py-0.5 rounded font-bold">
                AUDITED PEAKS
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-[12px] border border-[#E2ECE5] rounded-xl overflow-hidden">
                <thead className="bg-[#F6FAF7] border-b border-[#E2ECE5] font-bold text-[#2A4B37]">
                  <tr>
                    <th className="p-3">Biochemical Marker</th>
                    <th className="p-3">Target Functional Group</th>
                    <th className="p-3">Wavenumber Peak</th>
                    <th className="p-3">Absorbance</th>
                    <th className="p-3">Significance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#EEF3F0]">
                  <tr>
                    <td className="p-3 font-bold text-[#142C1D]">Starch C-O-C Stretch</td>
                    <td className="p-3 text-[#4A6657]">Glycosidic bond polysaccharide ring</td>
                    <td className="p-3 font-mono font-bold text-[#153822]">
                      {spectral_evidence.starch_coc_band.wavenumber} cm⁻¹
                    </td>
                    <td className="p-3 font-mono font-bold text-[#153822]">
                      {spectral_evidence.starch_coc_band.absorbance}
                    </td>
                    <td className="p-3 text-[#5A7666]">
                      Wheat flour carbohydrate adulteration marker (elevates in adulterated samples).
                    </td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-[#142C1D]">Amide I Gluten Peptide</td>
                    <td className="p-3 text-[#4A6657]">C=O carbonyl stretch in peptide backbone</td>
                    <td className="p-3 font-mono font-bold text-[#153822]">
                      {spectral_evidence.amide_i_gluten_band.wavenumber} cm⁻¹
                    </td>
                    <td className="p-3 font-mono font-bold text-[#153822]">
                      {spectral_evidence.amide_i_gluten_band.absorbance}
                    </td>
                    <td className="p-3 text-[#5A7666]">
                      Characteristic of wheat gluten storage proteins (gliadin & glutenin).
                    </td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-[#142C1D]">Curcuminoid Biomarker</td>
                    <td className="p-3 text-[#4A6657]">Conjugated C=C / C=O aromatic ring</td>
                    <td className="p-3 font-mono font-bold text-[#153822]">
                      {spectral_evidence.curcuminoid_band.wavenumber} cm⁻¹
                    </td>
                    <td className="p-3 font-mono font-bold text-[#153822]">
                      {spectral_evidence.curcuminoid_band.absorbance}
                    </td>
                    <td className="p-3 text-[#5A7666]">
                      Principal active compound of authentic turmeric rhizome (diluted by adulterant).
                    </td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-[#142C1D]">Water O-H Stretching</td>
                    <td className="p-3 text-[#4A6657]">Intermolecular hydrogen-bonded hydroxyl</td>
                    <td className="p-3 font-mono font-bold text-[#153822]">
                      {spectral_evidence.water_oh_band.wavenumber} cm⁻¹
                    </td>
                    <td className="p-3 font-mono font-bold text-[#153822]">
                      {spectral_evidence.water_oh_band.absorbance}
                    </td>
                    <td className="p-3 text-[#5A7666]">
                      Moisture band baseline across powdered botanical preparations.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Full Technical Spectral Plot */}
          <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs">
            <h3 className="text-[14px] font-bold text-[#142C1D] mb-2">
              Full-Band Technical Spectral Waveform
            </h3>
            <SpectrumPlot
              wavenumbers={result.spectrum_chart.wavenumbers}
              absorbance={result.spectrum_chart.absorbance}
              sampleId={result.sample_id}
              actualLevel={result.actual_level}
              predictedClass={prediction.predicted_class}
              showAnnotations={true}
              height={280}
            />
          </div>

          {/* Dimensionality Reduction & Mathematical Pipeline */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-3">
              <h4 className="text-[13px] font-bold uppercase tracking-wider text-[#153822]">
                Principal Component Analysis (PCA)
              </h4>
              <p className="text-[12px] text-[#4F6D5C] leading-relaxed">
                Raw ATR-FTIR scans span 2,522 contiguous optical frequencies with high inter-band collinearity. The pipeline applies standard scaling followed by PCA dimensionality reduction into <strong>91 orthogonal components</strong>, capturing <strong>90.10%</strong> of the total explained variance across the training set.
              </p>
              <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#DEE7E1] text-[11px] font-mono text-[#2B4B37]">
                Components: 91 | Explained Variance Ratio: 0.9010 | Whitening: False
              </div>
            </div>

            <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-3">
              <h4 className="text-[13px] font-bold uppercase tracking-wider text-[#153822]">
                Model Pipeline Specifications
              </h4>
              <p className="text-[12px] text-[#4F6D5C] leading-relaxed">
                <strong>Classification:</strong> L2-regularized Multinomial Logistic Regression trained on 280 cross-validation samples across 7 discrete target tiers.<br />
                <strong>Regression:</strong> Ensemble Random Forest Regressor (100 estimators) computing continuous concentration (% w/w).
              </p>
              <div className="p-3 bg-[#F8FAF9] rounded-xl border border-[#DEE7E1] text-[11px] font-mono text-[#2B4B37]">
                Classifier: LogisticRegression(C=1.0) | Regressor: RandomForestRegressor(n_estimators=100)
              </div>
            </div>
          </div>

          {/* Raw JSON Inspector & Developer Payload */}
          <div className="bg-[#112619] text-[#E0EBE4] rounded-2xl p-6 shadow-sm space-y-3">
            <div className="flex items-center justify-between pb-3 border-b border-[#21432E]">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-[#A6E1BA]" />
                <h4 className="text-[13px] font-mono font-bold text-white">
                  Raw Diagnostic JSON Payload
                </h4>
              </div>
              <button
                onClick={handleCopyJson}
                className="flex items-center gap-1.5 px-3 py-1 bg-[#214530] hover:bg-[#2C573D] text-[#A6E1BA] text-[11px] font-bold rounded-lg transition-colors"
              >
                {copiedJson ? (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy JSON</span>
                  </>
                )}
              </button>
            </div>
            <pre className="text-[11px] font-mono overflow-x-auto max-h-72 p-3 bg-[#0A1810] rounded-xl border border-[#1A3825] text-[#C4E3D0]">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* ── 8. Actionable Recommended Next Steps & Protocol Disclaimer ──── */}
      <div className="bg-[#FFFDF9] rounded-2xl border border-[#F0E6D3] p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-[#F4E9D8]">
          <ShieldAlert className="w-5 h-5 text-[#B86B14]" />
          <h3 className="text-[15px] font-extrabold text-[#563B0D]">
            Actionable Next Steps & Confirmatory Laboratory Protocols
          </h3>
          <span className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded uppercase bg-[#FDEFD9] text-[#8C520E]">
            Status: {uncertainty.status}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-[12px]">
          <div>
            <h4 className="font-extrabold text-[#5C3F0E] mb-2 flex items-center gap-1.5">
              <span>Standard Verification Wet-Chemistry Methods</span>
            </h4>
            <div className="space-y-2 text-[#6D4F1B]">
              <div className="p-3 bg-[#FFF7EC] border border-[#F5E2C9] rounded-xl">
                <span className="font-bold block text-[#5C3F0E]">
                  AOAC Method 972.16 (Polarizing Light Microscopy)
                </span>
                <span className="text-[11px]">
                  Direct optical identification of characteristic polygonal wheat starch granules and gluten matrix elements.
                </span>
              </div>
              <div className="p-3 bg-[#FFF7EC] border border-[#F5E2C9] rounded-xl">
                <span className="font-bold block text-[#5C3F0E]">
                  AOAC Method 2016.16 (HPLC-DAD Curcuminoid Assay)
                </span>
                <span className="text-[11px]">
                  High-performance liquid chromatography with diode-array detection for total curcuminoid quantification.
                </span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-extrabold text-[#5C3F0E] mb-2">
              Operational Decision Guideline
            </h4>
            <p className="text-[#6D4F1B] leading-relaxed mb-3">
              {summaryAnswers.q5_what_next}
            </p>
            <div className="p-3 bg-[#FFF7EC] border border-[#F5E2C9] rounded-xl text-[11px] text-[#7A561E]">
              <strong>Screening Notice:</strong> FoodSure AI is an intelligent rapid pre-screening instrument. Do not release commercial inventory, execute regulatory penalties, or declare human consumption safety solely based on this AI screening result without accredited laboratory confirmation.
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-[#F2E5D2] text-[11px] text-[#805C23]">
          {result.disclaimer}
        </div>
      </div>
    </div>
  );
};
