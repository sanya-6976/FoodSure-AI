import React from 'react';
import {
  ArrowUpRight,
  Microscope,
  ShieldAlert,
  Sparkles,
  FileText,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Database,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Cpu,
} from 'lucide-react';
import {
  NavPage,
  Language,
  SystemStatus,
  HistoryRecord,
  BenchmarkSample,
  AnalysisResult,
} from '../types';
import { translations } from '../i18n';
import { SpectrumPlot } from '../components/SpectrumPlot';

interface OverviewViewProps {
  onNavigate: (page: NavPage) => void;
  lang: Language;
  systemStatus: SystemStatus | null;
  history: HistoryRecord[];
  samples: BenchmarkSample[];
  onSelectSampleForAnalysis: (sample: BenchmarkSample) => void;
  onViewReport: (result: AnalysisResult) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  onNavigate,
  lang,
  systemStatus,
  history,
  samples,
  onSelectSampleForAnalysis,
  onViewReport,
}) => {
  const t = translations[lang];

  // Benchmark pure sample for preview
  const pureSample = samples.find((s) => s.is_pure) || samples[0];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* ── Welcome Banner ──────────────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 lg:p-8 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#EBF4EE] text-[#1B4B2D] text-[11px] font-semibold mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-[#1E7D46]" />
            Dual-Stage Spectroscopic AI Platform
          </div>

          <h2 className="text-[24px] lg:text-[28px] font-extrabold text-[#112619] tracking-tight leading-tight">
            {t.welcome_heading}
          </h2>

          <p className="text-[14px] text-[#4F6858] font-normal mt-2 leading-relaxed">
            {t.welcome_subheading}
          </p>

          <div className="flex flex-wrap items-center gap-3 mt-5">
            <button
              onClick={() => onNavigate('analyze')}
              className="flex items-center gap-2 px-4 py-2 bg-[#153822] hover:bg-[#0E2818] text-white text-[13px] font-semibold rounded-xl shadow-xs transition-colors"
            >
              <Microscope className="w-4 h-4" />
              <span>{t.start_new_analysis}</span>
            </button>

            <button
              onClick={() => onNavigate('dataset')}
              className="flex items-center gap-2 px-4 py-2 bg-[#F6FAF7] hover:bg-[#EBF3ED] text-[#244731] border border-[#D7E2DB] text-[13px] font-semibold rounded-xl transition-colors"
            >
              <Database className="w-4 h-4" />
              <span>{t.explore_methodology}</span>
            </button>
          </div>
        </div>

        {/* Decorative Graphic or Scientific Pill */}
        <div className="relative z-10 flex-shrink-0 bg-[#F4F9F6] border border-[#DCE8E0] rounded-xl p-4 w-full md:w-64">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#496554] mb-2 flex items-center justify-between">
            <span>Core Model Specs</span>
            <span className="w-2 h-2 rounded-full bg-[#1E7D46]" />
          </div>
          <div className="space-y-1.5 text-[12px]">
            <div className="flex justify-between">
              <span className="text-[#647F70]">Spectroscopy</span>
              <span className="font-semibold text-[#183623]">ATR-FTIR</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#647F70]">Wavenumbers</span>
              <span className="font-semibold text-[#183623]">2,522 Features</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#647F70]">Adulterant</span>
              <span className="font-semibold text-[#183623]">Wheat Flour</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#647F70]">Classification</span>
              <span className="font-semibold text-[#183623]">0% – 9% w/w</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── KPI Metric Cards ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Samples Evaluated */}
        <div className="bg-[#FFFFFF] rounded-xl border border-[#E3E9E5] p-5 shadow-xs">
          <div className="flex items-center justify-between text-[#617D6E] mb-2">
            <span className="text-[12px] font-medium">{t.total_samples}</span>
            <Database className="w-4 h-4 text-[#153822]" />
          </div>
          <div className="text-[26px] font-extrabold text-[#112619] tracking-tight">
            350
          </div>
          <div className="flex items-center gap-1.5 mt-1 text-[11px] text-[#4D6758]">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#1E7D46]" />
            <span>280 Train / 70 Holdout (Mendeley DOI)</span>
          </div>
        </div>

        {/* Metric 2: Macro F1 */}
        <div className="bg-[#FFFFFF] rounded-xl border border-[#E3E9E5] p-5 shadow-xs">
          <div className="flex items-center justify-between text-[#617D6E] mb-2">
            <span className="text-[12px] font-medium">{t.model_macro_f1}</span>
            <CheckCircle2 className="w-4 h-4 text-[#153822]" />
          </div>
          <div className="text-[26px] font-extrabold text-[#112619] tracking-tight">
            100%
          </div>
          <div className="flex items-center gap-1.5 mt-1 text-[11px] text-[#4D6758]">
            <span className="font-semibold text-[#1E7D46]">± 0.0% Std</span>
            <span>in 5-fold Stratified CV</span>
          </div>
        </div>

        {/* Metric 3: Regression MAE */}
        <div className="bg-[#FFFFFF] rounded-xl border border-[#E3E9E5] p-5 shadow-xs">
          <div className="flex items-center justify-between text-[#617D6E] mb-2">
            <span className="text-[12px] font-medium">{t.regression_mae}</span>
            <TrendingUp className="w-4 h-4 text-[#153822]" />
          </div>
          <div className="text-[26px] font-extrabold text-[#112619] tracking-tight">
            0.031%
          </div>
          <div className="flex items-center gap-1.5 mt-1 text-[11px] text-[#4D6758]">
            <span>Random Forest Regressor (% w/w)</span>
          </div>
        </div>

        {/* Metric 4: Adulterant Scope */}
        <div className="bg-[#FFFFFF] rounded-xl border border-[#E3E9E5] p-5 shadow-xs">
          <div className="flex items-center justify-between text-[#617D6E] mb-2">
            <span className="text-[12px] font-medium">{t.adulterant_scope}</span>
            <ShieldAlert className="w-4 h-4 text-[#A87212]" />
          </div>
          <div className="text-[22px] font-extrabold text-[#112619] tracking-tight truncate">
            Wheat Flour
          </div>
          <div className="flex items-center gap-1.5 mt-1 text-[11px] text-[#698476]">
            <span>7 discrete tiers (0%, 1%, 2%, 3%, 5%, 7%, 9%)</span>
          </div>
        </div>
      </div>

      {/* ── Spectral Curve Preview + Benchmark Quick Test ─────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {pureSample && (
            <SpectrumPlot
              wavenumbers={pureSample.wavenumbers}
              absorbance={pureSample.absorbance}
              sampleId={pureSample.sample_id}
              actualLevel={pureSample.actual_level}
              predictedClass="0% Pure Turmeric"
              showAnnotations={true}
              height={260}
            />
          )}
        </div>

        {/* Quick Benchmark Sample Tester */}
        <div className="bg-[#FFFFFF] rounded-xl border border-[#E3E9E5] p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[14px] font-bold text-[#142C1D]">
                Benchmark Sample Quick-Test
              </h3>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#EEF5F0] text-[#1E5232]">
                70 Available
              </span>
            </div>
            <p className="text-[12px] text-[#557161] mb-4 leading-relaxed">
              Select any validated physical test sample from the Mendeley benchmark to immediately load its 2,522-point FTIR spectrum and run live dual-stage inference.
            </p>

            <div className="space-y-2">
              {samples.slice(0, 4).map((sample) => (
                <div
                  key={sample.sample_id}
                  onClick={() => onSelectSampleForAnalysis(sample)}
                  className="flex items-center justify-between p-2.5 bg-[#F6FAF7] hover:bg-[#EEF5F0] border border-[#DEE7E1] rounded-lg cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        sample.is_pure ? 'bg-[#1E7D46]' : 'bg-[#C27D15]'
                      }`}
                    />
                    <div>
                      <div className="text-[12px] font-bold text-[#153822]">
                        {sample.sample_id}
                      </div>
                      <div className="text-[10px] text-[#698476]">
                        Ground Truth: {sample.actual_level}% Adulteration
                      </div>
                    </div>
                  </div>
                  <span className="text-[11px] font-semibold text-[#183623] flex items-center gap-1">
                    Analyze <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => onNavigate('analyze')}
            className="w-full mt-4 py-2 bg-[#F0F5F2] hover:bg-[#E3EBE5] text-[#1D4A2F] text-[12px] font-semibold rounded-lg border border-[#D2DFD6] transition-colors"
          >
            Open Full Analysis Studio
          </button>
        </div>
      </div>

      {/* ── Recent Analyses Table ───────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-xl border border-[#E3E9E5] p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-[15px] font-bold text-[#112619]">
              Recent Laboratory Analyses
            </h3>
            <p className="text-[12px] text-[#557161] mt-0.5">
              Verified spectroscopic screening records stored in local audit trail.
            </p>
          </div>
          <button
            onClick={() => onNavigate('history')}
            className="text-[12px] font-semibold text-[#153822] hover:underline flex items-center gap-1"
          >
            View All History <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {history.length === 0 ? (
          <div className="py-12 text-center text-[#698476] text-[13px] bg-[#F8FAF8] rounded-lg border border-dashed border-[#DCE5DF]">
            No analyses recorded yet. Start your first sample screening above!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[12px]">
              <thead>
                <tr className="border-b border-[#E7EFE9] text-[#607D6E] font-semibold">
                  <th className="py-2.5 px-3">Sample ID</th>
                  <th className="py-2.5 px-3">Date / Time</th>
                  <th className="py-2.5 px-3">Discrete Class</th>
                  <th className="py-2.5 px-3">Regression (% w/w)</th>
                  <th className="py-2.5 px-3">Screening Status</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F0F5F2]">
                {history.slice(0, 5).map((item) => (
                  <tr key={item.id} className="hover:bg-[#F9FCFA] transition-colors">
                    <td className="py-3 px-3 font-bold text-[#142C1D]">
                      {item.sample_id}
                      <span className="block text-[10px] font-normal text-[#6C8578]">
                        {item.batch_id}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-[#587364]">
                      {new Date(item.timestamp).toLocaleDateString()}{' '}
                      <span className="text-[10px] text-[#7E998B]">
                        {new Date(item.timestamp).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-semibold text-[#183623]">
                      {item.predicted_class}
                    </td>
                    <td className="py-3 px-3 font-mono font-medium text-[#2A4B36]">
                      {item.predicted_percentage !== null
                        ? `${item.predicted_percentage.toFixed(2)}%`
                        : '—'}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                          item.is_pure
                            ? 'bg-[#E5F5EB] text-[#1E7D46]'
                            : 'bg-[#FFF3E0] text-[#B86B14]'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            item.is_pure ? 'bg-[#1E7D46]' : 'bg-[#B86B14]'
                          }`}
                        />
                        {item.is_pure ? t.pure_turmeric : t.adulterated}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => onViewReport(item.result_data)}
                        className="px-2.5 py-1 bg-[#EEF5F0] hover:bg-[#E0EDE4] text-[#164126] font-semibold rounded-lg text-[11px] transition-colors inline-flex items-center gap-1"
                      >
                        <FileText className="w-3 h-3" />
                        {t.view_report}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Scientific Limitations Card ─────────────────────────────────── */}
      <div className="bg-[#FFFDF9] rounded-xl border border-[#F0E6D3] p-5 text-[12px] text-[#715423] shadow-xs">
        <div className="flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-[#B86B14] flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-bold text-[#54390B] text-[13px]">
              Scientific Compliance & Research Boundary Disclaimer
            </h4>
            <p className="leading-relaxed text-[#6E501F]">
              FoodSure AI is an AI-assisted screening research tool evaluated on 350 physical laboratory samples (Mendeley Data DOI: 10.17632/cb5kbt7bgv.1) with wheat-flour as the targeted adulterant. Model outputs are mathematical estimates and pattern-matching decisions; they do not replace official regulatory certification or accredited wet-chemistry protocols (e.g., AOAC microscopy or DNA-based assays).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
