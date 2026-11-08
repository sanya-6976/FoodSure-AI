import React from 'react';
import {
  Database,
  ExternalLink,
  BookOpen,
  Layers,
  Cpu,
  CheckCircle2,
  ShieldAlert,
  BarChart3,
} from 'lucide-react';
import { Language } from '../types';
import { translations } from '../i18n';

interface DatasetMethodologyViewProps {
  lang: Language;
}

export const DatasetMethodologyView: React.FC<DatasetMethodologyViewProps> = ({ lang }) => {
  const t = translations[lang];

  // Verified 21-configuration 5-fold cross-validation results from notebook 09 & evaluation report
  const cvBenchmarkData = [
    { config: 'FTIR (Current Model)', f1: '100.0%', accuracy: '100.0%', precision: '100.0%', recall: '100.0%', mae: '0.031%' },
    { config: 'Color + FTIR', f1: '100.0%', accuracy: '100.0%', precision: '100.0%', recall: '100.0%', mae: '0.038%' },
    { config: 'FTIR + Image', f1: '100.0%', accuracy: '100.0%', precision: '100.0%', recall: '100.0%', mae: '0.035%' },
    { config: 'Color + FTIR + Image', f1: '100.0%', accuracy: '100.0%', precision: '100.0%', recall: '100.0%', mae: '0.039%' },
    { config: 'Image Only (EfficientNet-B0)', f1: '95.3%', accuracy: '95.4%', precision: '95.8%', recall: '95.4%', mae: '0.245%' },
    { config: 'Color Only (Hunter Lab)', f1: '86.4%', accuracy: '86.8%', precision: '87.1%', recall: '86.8%', mae: '0.512%' },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* ── Top Header ─────────────────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-[#EEF5F0] text-[#1E5232] text-[11px] font-semibold mb-1.5">
            Academic Provenance & Empirical Audit
          </div>
          <h2 className="text-[20px] font-bold text-[#112619] tracking-tight">
            Dataset Provenance & ML Methodology
          </h2>
          <p className="text-[13px] text-[#557161] mt-0.5">
            Peer-reviewed open benchmark for multimodal turmeric adulteration detection and quantification.
          </p>
        </div>

        <a
          href="https://doi.org/10.17632/cb5kbt7bgv.1"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-3.5 py-2 bg-[#F6FAF7] hover:bg-[#EEF5F0] text-[#164126] border border-[#DCE5DF] text-[12px] font-bold rounded-xl transition-colors"
        >
          <span>Mendeley Data DOI</span>
          <ExternalLink className="w-3.5 h-3.5 text-[#1E7D46]" />
        </a>
      </div>

      {/* ── Dataset Breakdown Cards ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-5 shadow-xs">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#547362] mb-1">
            Cohort Population
          </div>
          <div className="text-[26px] font-black text-[#112619]">
            350 Samples
          </div>
          <p className="text-[12px] text-[#557161] mt-1">
            50 physical samples each across 7 distinct adulteration levels: 0%, 1%, 2%, 3%, 5%, 7%, and 9% (w/w).
          </p>
        </div>

        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-5 shadow-xs">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#547362] mb-1">
            Target Adulterant
          </div>
          <div className="text-[26px] font-black text-[#112619]">
            Wheat Flour
          </div>
          <p className="text-[12px] text-[#557161] mt-1">
            Homogenously mixed under controlled laboratory conditions to replicate commercial bulking fraud.
          </p>
        </div>

        <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-5 shadow-xs">
          <div className="text-[11px] font-bold uppercase tracking-wider text-[#547362] mb-1">
            Preserved Partition
          </div>
          <div className="text-[26px] font-black text-[#112619]">
            280 / 70 Split
          </div>
          <p className="text-[12px] text-[#557161] mt-1">
            Strict 80/20 train-test partition (40 train / 10 holdout per class) with no patient or batch overlap.
          </p>
        </div>
      </div>

      {/* ── Modalities Comparison ───────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-4">
        <h3 className="text-[15px] font-bold text-[#142C1D]">
          Comparative Modality Evaluation
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-[12px]">
          <div className="p-4 bg-[#F2F8F4] border-2 border-[#1E7D46] rounded-xl relative">
            <span className="absolute top-3 right-3 text-[10px] font-bold px-2 py-0.5 rounded bg-[#153822] text-white">
              Production Active
            </span>
            <h4 className="font-bold text-[#112619] text-[13px] mb-1">
              ATR-FTIR Spectroscopy
            </h4>
            <div className="text-[11px] font-mono text-[#1E7D46] font-semibold mb-2">
              2,522 Wavenumbers (4000–650 cm⁻¹)
            </div>
            <p className="text-[#496555] leading-relaxed">
              Attenuated Total Reflectance infrared spectroscopy captures fundamental bond vibrational frequencies. Achieved 100% Macro F1 in 5-fold CV using 91 PCA components (90.1% explained variance).
            </p>
          </div>

          <div className="p-4 bg-[#F9FCFA] border border-[#DEE7E1] rounded-xl">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#EEF5F0] text-[#4F6C5C] float-right">
              Experimental
            </span>
            <h4 className="font-bold text-[#112619] text-[13px] mb-1">
              Color Measurements
            </h4>
            <div className="text-[11px] font-mono text-[#617E6F] font-semibold mb-2">
              46 Spectral Reflectance Bands
            </div>
            <p className="text-[#557161] leading-relaxed">
              Hunter Lab colorimeter coordinates (L*, a*, b*) and 360–780 nm spectral reflectance. High confusion between pure and 1% adulteration due to visual indistinguishability.
            </p>
          </div>

          <div className="p-4 bg-[#F9FCFA] border border-[#DEE7E1] rounded-xl">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#EEF5F0] text-[#4F6C5C] float-right">
              Experimental
            </span>
            <h4 className="font-bold text-[#112619] text-[13px] mb-1">
              High-Res Macro Imaging
            </h4>
            <div className="text-[11px] font-mono text-[#617E6F] font-semibold mb-2">
              1,280 Precomputed Embeddings
            </div>
            <p className="text-[#557161] leading-relaxed">
              350 raw images (4032x3024 RGB) processed through pre-trained EfficientNet-B0 feature extractor. Reached 95.36% accuracy with RBF-SVM.
            </p>
          </div>
        </div>
      </div>

      {/* ── 5-Fold Cross Validation Benchmark Table ──────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs">
        <div className="mb-4">
          <h3 className="text-[15px] font-bold text-[#112619]">
            Empirical Benchmark: 5-Fold Cross-Validation Across Modalities
          </h3>
          <p className="text-[12px] text-[#557161] mt-0.5">
            Evaluated on the 280-sample training cohort with StratifiedKFold (random_state=42). Leakage-free preprocessing fitted inside each fold.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead>
              <tr className="bg-[#FAFDFB] border-b border-[#E3E9E5] text-[#557161] font-bold">
                <th className="py-2.5 px-3">Modality Configuration</th>
                <th className="py-2.5 px-3">Classification Macro F1</th>
                <th className="py-2.5 px-3">Macro Accuracy</th>
                <th className="py-2.5 px-3">Macro Precision</th>
                <th className="py-2.5 px-3">Macro Recall</th>
                <th className="py-2.5 px-3">RF Regression MAE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EEF3F0]">
              {cvBenchmarkData.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#F9FCFA] transition-colors">
                  <td className="py-3 px-3 font-bold text-[#142C1D]">
                    {row.config}
                  </td>
                  <td className="py-3 px-3 font-bold text-[#153822]">{row.f1}</td>
                  <td className="py-3 px-3 text-[#3B5747]">{row.accuracy}</td>
                  <td className="py-3 px-3 text-[#3B5747]">{row.precision}</td>
                  <td className="py-3 px-3 text-[#3B5747]">{row.recall}</td>
                  <td className="py-3 px-3 font-mono font-bold text-[#1F412B]">{row.mae}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Academic Citation & Reference ─────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-3">
        <h3 className="text-[14px] font-bold text-[#112619]">
          Academic Provenance & Citation
        </h3>
        <div className="p-3.5 bg-[#F8FAF8] border border-[#DEE7E1] rounded-xl font-mono text-[11px] text-[#334E3E] select-all leading-relaxed">
          Mendeley Data: "Multimodal Dataset for Turmeric Adulteration Detection Using Imaging, ATR-FTIR Spectroscopy, and Color Measurements" (DOI: 10.17632/cb5kbt7bgv.1)
        </div>
      </div>
    </div>
  );
};
