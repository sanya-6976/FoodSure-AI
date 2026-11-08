import React from 'react';
import {
  BookOpen,
  Microscope,
  CheckCircle2,
  FileCheck2,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';
import { Language } from '../types';

interface DocumentationViewProps {
  lang: Language;
}

export const DocumentationView: React.FC<DocumentationViewProps> = () => {
  const bands = [
    {
      range: '980 – 1050 cm⁻¹',
      band: 'C–O–C Ring Vibration & Stretch',
      target: 'Starch Polysaccharides',
      significance:
        'Wheat flour is ~70% starch. As wheat flour adulteration increases, absorption in this glycosidic region rises steeply relative to pure turmeric.',
    },
    {
      range: '1620 – 1680 cm⁻¹',
      band: 'Amide I (C=O Peptide Stretch)',
      target: 'Wheat Gluten Protein',
      significance:
        'Secondary structural marker of plant gluten proteins (gliadin and glutenin) absent in high concentrations in pure rhizome extracts.',
    },
    {
      range: '1480 – 1530 cm⁻¹',
      band: 'Conjugated C=C & Benzene Ring',
      target: 'Curcuminoids (Curcumin)',
      significance:
        'Biomarker fingerprint of pure Curcuma longa. Adulteration with flour dilutes this aromatic resonance.',
    },
    {
      range: '3200 – 3500 cm⁻¹',
      band: 'O–H Hydroxyl Stretching',
      target: 'Phenolics & Moisture',
      significance:
        'Broad absorption envelope reflecting moisture and free hydroxyl groups from curcuminoid enols and starches.',
    },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* ── Top Header ─────────────────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs flex items-center justify-between">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-[#EEF5F0] text-[#1E5232] text-[11px] font-semibold mb-1.5">
            Scientific Reference
          </div>
          <h2 className="text-[20px] font-bold text-[#112619] tracking-tight">
            ATR-FTIR Spectroscopy & Food Testing Protocols
          </h2>
          <p className="text-[13px] text-[#557161] mt-0.5">
            Standard Operating Procedures, vibrational band assignments, and laboratory wet-chemistry verification methods.
          </p>
        </div>
      </div>

      {/* ── Vibrational Band Assignments Table ──────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-4">
        <div>
          <h3 className="text-[15px] font-bold text-[#112619]">
            Vibrational Band Index (4000 to 650 cm⁻¹)
          </h3>
          <p className="text-[12px] text-[#557161] mt-0.5">
            Key infrared spectral markers utilized by FoodSure AI to discriminate pure Curcuma longa from wheat-flour mixtures.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px] border border-[#E2EAE5] rounded-xl overflow-hidden">
            <thead className="bg-[#F6FAF7] border-b border-[#E2EAE5] font-bold text-[#355242]">
              <tr>
                <th className="p-3">Wavenumber Range</th>
                <th className="p-3">Vibrational Assignment</th>
                <th className="p-3">Chemical Biomarker</th>
                <th className="p-3">Diagnostic Significance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EEF3F0]">
              {bands.map((b, idx) => (
                <tr key={idx} className="hover:bg-[#F9FCFA] transition-colors">
                  <td className="p-3 font-mono font-bold text-[#153822] whitespace-nowrap">
                    {b.range}
                  </td>
                  <td className="p-3 font-bold text-[#142C1D]">{b.band}</td>
                  <td className="p-3 text-[#1E7D46] font-semibold">{b.target}</td>
                  <td className="p-3 text-[#4A6455] leading-relaxed">{b.significance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Official Verification Protocols ─────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs space-y-4">
        <h3 className="text-[15px] font-bold text-[#112619]">
          Recommended Confirmatory Laboratory Protocols
        </h3>
        <p className="text-[12px] text-[#557161]">
          When FoodSure AI detects potential adulteration, the physical sample should be routed through standard ISO/AOAC testing pipelines:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-[12px]">
          <div className="p-4 bg-[#F8FAF8] border border-[#DEE7E1] rounded-xl space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#1E7D46]">
              Morphological Analysis
            </span>
            <h4 className="font-bold text-[#142C1D] text-[13px]">
              AOAC 972.16 Polarizing Microscopy
            </h4>
            <p className="text-[#557161] leading-relaxed">
              Examines microscopic birefringence of wheat starch granules (bimodal 15–35 µm lenticular vs spherical 2–8 µm) compared with gelatinized or native turmeric cells.
            </p>
          </div>

          <div className="p-4 bg-[#F8FAF8] border border-[#DEE7E1] rounded-xl space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#1E7D46]">
              Chemical Quantification
            </span>
            <h4 className="font-bold text-[#142C1D] text-[13px]">
              AOAC 2016.16 HPLC-DAD
            </h4>
            <p className="text-[#557161] leading-relaxed">
              High-performance liquid chromatography with diode-array detection to quantitatively determine curcumin, demethoxycurcumin (DMC), and bisdemethoxycurcumin (BDMC).
            </p>
          </div>

          <div className="p-4 bg-[#F8FAF8] border border-[#DEE7E1] rounded-xl space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#1E7D46]">
              Genetic Authenticity
            </span>
            <h4 className="font-bold text-[#142C1D] text-[13px]">
              Real-Time PCR DNA Barcoding
            </h4>
            <p className="text-[#557161] leading-relaxed">
              Amplifies species-specific primers for the chloroplast matK and rbcL genes to unequivocally detect presence of Triticum aestivum (wheat) in spice powder.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
