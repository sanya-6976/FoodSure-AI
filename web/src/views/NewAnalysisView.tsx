import React, { useState } from 'react';
import {
  Upload,
  FileCheck,
  CheckCircle2,
  AlertCircle,
  Download,
  Database,
  ArrowRight,
  Sparkles,
  Info,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import {
  NavPage,
  Language,
  BenchmarkSample,
  AnalysisResult,
  SystemStatus,
} from '../types';
import { translations } from '../i18n';
import { SpectrumPlot } from '../components/SpectrumPlot';

interface NewAnalysisViewProps {
  lang: Language;
  systemStatus: SystemStatus | null;
  samples: BenchmarkSample[];
  selectedBenchmark: BenchmarkSample | null;
  onSelectBenchmark: (sample: BenchmarkSample | null) => void;
  onStartAnalysis: (payload: any) => Promise<void>;
  isAnalyzing: boolean;
}

export const NewAnalysisView: React.FC<NewAnalysisViewProps> = ({
  lang,
  systemStatus,
  samples,
  selectedBenchmark,
  onSelectBenchmark,
  onStartAnalysis,
  isAnalyzing,
}) => {
  const t = translations[lang];

  // Form states
  const [activeTab, setActiveTab] = useState<'benchmark' | 'upload'>('benchmark');
  const [sampleId, setSampleId] = useState(selectedBenchmark?.sample_id || 'FS-SMP-2026');
  const [sampleName, setSampleName] = useState('Turmeric Powder Screening');
  const [batchId, setBatchId] = useState('LOT-2026-088');
  const [notes, setNotes] = useState('Standard incoming quality check.');
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(true);

  // Uploaded file state
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [uploadedFeatures, setUploadedFeatures] = useState<number[] | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSpectrum, setUploadSpectrum] = useState<{
    wavenumbers: number[];
    absorbance: number[];
  } | null>(null);

  // Benchmark filters
  const [classFilter, setClassFilter] = useState<string>('all');

  const filteredSamples = samples.filter((s) => {
    if (classFilter === 'all') return true;
    if (classFilter === 'pure') return s.is_pure;
    return `${s.actual_level}%` === classFilter;
  });

  // Handle CSV file selection and parsing
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError(null);
    setUploadedFileName(file.name);

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        const lines = text.trim().split(/\r?\n/);
        if (lines.length < 2) {
          throw new Error('CSV must contain a header row and at least one data row.');
        }

        const headers = lines[0].split(',').map((c) => c.trim().replace(/^"|"$/g, ''));
        const values = lines[1].split(',').map((v) => parseFloat(v.trim()));

        // Check if first column is sample ID
        let numericVals = values;
        let finalSampleId = sampleId;
        if (isNaN(values[0])) {
          finalSampleId = lines[1].split(',')[0].trim().replace(/^"|"$/g, '');
          numericVals = values.slice(1);
          setSampleId(finalSampleId);
        }

        if (numericVals.some((v) => isNaN(v))) {
          throw new Error('All spectral feature values must be valid numeric numbers.');
        }

        // Expected 2,522 features (or close to it)
        if (numericVals.length < 500) {
          throw new Error(
            `Incomplete spectral sweep: received ${numericVals.length} features, expected 2,522 wavenumber values.`
          );
        }

        setUploadedFeatures(numericVals);

        // Subsample for fast preview
        const step = Math.max(1, Math.floor(numericVals.length / 630));
        const subAbs = numericVals.filter((_, i) => i % step === 0);
        const subWn = Array.from({ length: subAbs.length }, (_, i) =>
          Math.round(4000 - (i / subAbs.length) * (4000 - 650))
        );

        setUploadSpectrum({ wavenumbers: subWn, absorbance: subAbs });
      } catch (err: any) {
        setUploadError(err.message || 'Failed to parse CSV file.');
        setUploadedFeatures(null);
        setUploadSpectrum(null);
      }
    };
    reader.readAsText(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!disclaimerAccepted) return;

    if (activeTab === 'benchmark') {
      const activeSample = selectedBenchmark || samples[0];
      await onStartAnalysis({
        sample_id: activeSample.sample_id,
        sample_name: sampleName,
        batch_id: batchId,
        notes: notes,
      });
    } else {
      if (!uploadedFeatures) {
        setUploadError('Please select a valid FTIR CSV file before running analysis.');
        return;
      }
      await onStartAnalysis({
        sample_id: sampleId,
        sample_name: sampleName,
        batch_id: batchId,
        notes: notes,
        features: uploadedFeatures,
      });
    }
  };

  const currentPreviewSpectrum =
    activeTab === 'benchmark'
      ? selectedBenchmark || samples[0]
      : uploadSpectrum;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* ── Top Header ─────────────────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-[#EEF5F0] text-[#1E5232] text-[11px] font-semibold mb-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#1E7D46]" />
            Active Pipeline: ATR-FTIR Dual-Stage
          </div>
          <h2 className="text-[20px] font-bold text-[#112619] tracking-tight">
            New Turmeric Adulteration Screening
          </h2>
          <p className="text-[13px] text-[#557161] mt-0.5">
            Configure sample identification and provide spectroscopic infrared features for pattern detection.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[12px] font-medium text-[#658273]">Model Target:</span>
          <span className="px-2.5 py-1 rounded-lg bg-[#F2F7F4] border border-[#D5E2DA] text-[12px] font-bold text-[#153822]">
            Wheat Flour (0% – 9%)
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* ── Step 1: Sample Metadata ────────────────────────────────────── */}
        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs">
          <div className="flex items-center gap-2.5 pb-3 border-b border-[#EEF3F0] mb-4">
            <div className="w-6 h-6 rounded-full bg-[#153822] text-white flex items-center justify-center font-bold text-[11px]">
              1
            </div>
            <h3 className="text-[14px] font-bold text-[#132B1D]">
              Sample Information & Traceability
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-[12px]">
            <div>
              <label className="block font-bold text-[#1F3D2B] mb-1">
                Sample Identifier <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={sampleId}
                onChange={(e) => setSampleId(e.target.value)}
                placeholder="e.g., T7S33 or SMP-2026-99"
                className="w-full px-3 py-2 bg-[#F7FAF8] border border-[#D8E3DC] rounded-lg text-[13px] text-[#142C1D] font-medium focus:bg-white focus:border-[#153822] focus:outline-none transition-all"
              />
            </div>

            <div>
              <label className="block font-bold text-[#1F3D2B] mb-1">
                Batch / Lot Number
              </label>
              <input
                type="text"
                value={batchId}
                onChange={(e) => setBatchId(e.target.value)}
                placeholder="e.g., LOT-2026-088"
                className="w-full px-3 py-2 bg-[#F7FAF8] border border-[#D8E3DC] rounded-lg text-[13px] text-[#142C1D] font-medium focus:bg-white focus:border-[#153822] focus:outline-none transition-all"
              />
            </div>

            <div>
              <label className="block font-bold text-[#1F3D2B] mb-1">
                Sample Description
              </label>
              <input
                type="text"
                value={sampleName}
                onChange={(e) => setSampleName(e.target.value)}
                placeholder="e.g., Commercial Turmeric Sample"
                className="w-full px-3 py-2 bg-[#F7FAF8] border border-[#D8E3DC] rounded-lg text-[13px] text-[#142C1D] font-medium focus:bg-white focus:border-[#153822] focus:outline-none transition-all"
              />
            </div>
          </div>
        </div>

        {/* ── Step 2: Input Selection & Verification ──────────────────────── */}
        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-[#EEF3F0] mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-full bg-[#153822] text-white flex items-center justify-center font-bold text-[11px]">
                2
              </div>
              <h3 className="text-[14px] font-bold text-[#132B1D]">
                Input Modality & FTIR Spectral Source
              </h3>
            </div>

            {/* Mode Tabs */}
            <div className="flex rounded-lg bg-[#EBF1ED] p-1 border border-[#DCE5DF] text-[12px] font-semibold">
              <button
                type="button"
                onClick={() => setActiveTab('benchmark')}
                className={`px-3 py-1 rounded-md transition-all ${
                  activeTab === 'benchmark'
                    ? 'bg-white text-[#153822] shadow-xs'
                    : 'text-[#486655] hover:text-[#183623]'
                }`}
              >
                Benchmark Dataset
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('upload')}
                className={`px-3 py-1 rounded-md transition-all ${
                  activeTab === 'upload'
                    ? 'bg-white text-[#153822] shadow-xs'
                    : 'text-[#486655] hover:text-[#183623]'
                }`}
              >
                Upload FTIR CSV
              </button>
            </div>
          </div>

          {activeTab === 'benchmark' ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 text-[12px]">
                <p className="text-[#557161]">
                  Choose from 70 verified benchmark test samples from the Mendeley dataset with real physical spectra:
                </p>

                {/* Filter Pills */}
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-[#6C8577] text-[11px] font-semibold mr-1">Filter:</span>
                  {['all', 'pure', '1%', '2%', '3%', '5%', '7%', '9%'].map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => setClassFilter(lvl)}
                      className={`px-2 py-0.5 rounded-md text-[11px] font-semibold border transition-colors ${
                        classFilter === lvl
                          ? 'bg-[#153822] text-white border-[#153822]'
                          : 'bg-[#F6FAF7] text-[#41604F] border-[#DCE5DF] hover:bg-[#EEF5F0]'
                      }`}
                    >
                      {lvl === 'all' ? 'All' : lvl === 'pure' ? '0% Pure' : lvl}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sample Cards Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 gap-2.5 max-h-56 overflow-y-auto p-1 border border-[#E5EFE8] rounded-xl bg-[#FAFCFA]">
                {filteredSamples.map((sample) => {
                  const isSelected = selectedBenchmark?.sample_id === sample.sample_id;
                  return (
                    <div
                      key={sample.sample_id}
                      onClick={() => {
                        onSelectBenchmark(sample);
                        setSampleId(sample.sample_id);
                      }}
                      className={`p-2 rounded-lg cursor-pointer text-center border transition-all ${
                        isSelected
                          ? 'bg-[#EBF5EE] border-[#153822] ring-1 ring-[#153822]'
                          : 'bg-white border-[#DEE7E1] hover:bg-[#F2F7F4]'
                      }`}
                    >
                      <div className="text-[12px] font-bold text-[#153822]">
                        {sample.sample_id}
                      </div>
                      <div
                        className={`text-[10px] font-semibold mt-0.5 ${
                          sample.is_pure ? 'text-[#1E7D46]' : 'text-[#AF6F10]'
                        }`}
                      >
                        {sample.actual_level}%
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            /* Upload FTIR CSV Tab */
            <div className="space-y-4">
              <div className="border-2 border-dashed border-[#D2E0D6] rounded-xl p-6 text-center bg-[#F9FCFA] hover:bg-[#F2F8F4] transition-colors relative">
                <input
                  type="file"
                  accept=".csv,.txt"
                  onChange={handleFileUpload}
                  className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                />
                <div className="w-10 h-10 rounded-full bg-[#E5F1E9] text-[#153822] flex items-center justify-center mx-auto mb-2">
                  <Upload className="w-5 h-5" />
                </div>
                <div className="text-[13px] font-bold text-[#142C1D]">
                  {uploadedFileName ? uploadedFileName : 'Drop FTIR Spectrum CSV Here'}
                </div>
                <p className="text-[11px] text-[#557161] mt-1 max-w-md mx-auto">
                  Must contain 2,522 infrared wavenumber values from 4000 to 650 cm⁻¹.
                </p>

                {uploadedFeatures && (
                  <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E5F5EB] text-[#1E7D46] text-[11px] font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Verified {uploadedFeatures.length} wavenumber features ready
                  </div>
                )}

                {uploadError && (
                  <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FDF2F2] text-[#B92A2A] text-[11px] font-semibold">
                    <AlertCircle className="w-3.5 h-3.5" />
                    {uploadError}
                  </div>
                )}
              </div>

              {/* Download CSV Template Helper */}
              <div className="flex items-center justify-between p-3 bg-[#F6FAF7] border border-[#DEE7E1] rounded-xl text-[12px]">
                <div className="flex items-center gap-2 text-[#466352]">
                  <Info className="w-4 h-4 text-[#1E7D46]" />
                  <span>
                    Need a test file? Download a real benchmark FTIR spectrum formatted with all 2,522 wavenumber headers.
                  </span>
                </div>
                <a
                  href="/api/sample-csv/T7S33"
                  download="T7S33_ftir_spectrum.csv"
                  className="px-3 py-1 bg-white hover:bg-[#EEF5F0] text-[#153822] font-semibold rounded-lg border border-[#D5E2DA] inline-flex items-center gap-1.5 text-[11px] transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download Sample CSV
                </a>
              </div>
            </div>
          )}

          {/* Live Spectral Curve Preview */}
          {currentPreviewSpectrum && (
            <div className="mt-5 pt-4 border-t border-[#EEF3F0]">
              <SpectrumPlot
                wavenumbers={currentPreviewSpectrum.wavenumbers}
                absorbance={currentPreviewSpectrum.absorbance}
                sampleId={sampleId}
                showAnnotations={true}
                height={220}
              />
            </div>
          )}
        </div>

        {/* ── Step 3: Review & Scientific Confirmation ────────────────────── */}
        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-[#EEF3F0]">
            <div className="w-6 h-6 rounded-full bg-[#153822] text-white flex items-center justify-center font-bold text-[11px]">
              3
            </div>
            <h3 className="text-[14px] font-bold text-[#132B1D]">
              Confirmation & Scientific Compliance
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[12px]">
            <div className="p-3 bg-[#F6FAF7] border border-[#DEE7E1] rounded-xl">
              <span className="text-[#647F70] block text-[11px]">Feature Schema</span>
              <span className="font-bold text-[#153822]">2,522 Wavenumbers</span>
              <span className="text-[10px] text-[#557161] block mt-0.5">Aligned with PCA model</span>
            </div>
            <div className="p-3 bg-[#F6FAF7] border border-[#DEE7E1] rounded-xl">
              <span className="text-[#647F70] block text-[11px]">Inference Engines</span>
              <span className="font-bold text-[#153822]">Logistic Reg + RF Regressor</span>
              <span className="text-[10px] text-[#557161] block mt-0.5">Dual-Stage Output</span>
            </div>
            <div className="p-3 bg-[#F6FAF7] border border-[#DEE7E1] rounded-xl">
              <span className="text-[#647F70] block text-[11px]">AI Synthesis Mode</span>
              <span className="font-bold text-[#153822]">
                {systemStatus?.has_gemini_key ? 'Gemini 3.5 Flash' : 'Deterministic Fallback'}
              </span>
              <span className="text-[10px] text-[#557161] block mt-0.5">8-Section Report</span>
            </div>
          </div>

          <div className="pt-2">
            <label className="flex items-start gap-2.5 cursor-pointer text-[12px] text-[#496555] select-none">
              <input
                type="checkbox"
                checked={disclaimerAccepted}
                onChange={(e) => setDisclaimerAccepted(e.target.checked)}
                className="mt-0.5 rounded text-[#153822] focus:ring-[#153822]"
              />
              <span>
                I acknowledge that FoodSure AI is an AI-assisted research screening system. Model outputs are mathematical pattern estimates, not laboratory certifications, and consequential findings should be confirmed via accredited wet chemistry.
              </span>
            </label>
          </div>

          {/* Submit Action */}
          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={isAnalyzing || !disclaimerAccepted}
              className="flex items-center gap-2 px-6 py-2.5 bg-[#153822] hover:bg-[#0E2818] disabled:opacity-50 text-white text-[13px] font-bold rounded-xl shadow-xs transition-colors"
            >
              <Sparkles className="w-4 h-4 text-[#A6E1BA]" />
              <span>Run Dual-Stage Analysis</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
