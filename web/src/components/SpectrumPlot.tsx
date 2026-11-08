import React, { useState } from 'react';
import { Eye, Info, Layers, ZoomIn } from 'lucide-react';

interface SpectrumPlotProps {
  wavenumbers: number[];
  absorbance: number[];
  sampleId?: string;
  actualLevel?: number | null;
  predictedClass?: string;
  showAnnotations?: boolean;
  height?: number;
}

export const SpectrumPlot: React.FC<SpectrumPlotProps> = ({
  wavenumbers,
  absorbance,
  sampleId = 'Sample Spectrum',
  actualLevel,
  predictedClass,
  showAnnotations = true,
  height = 240,
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [showReference, setShowReference] = useState(false);

  if (!wavenumbers || !absorbance || wavenumbers.length === 0) {
    return (
      <div
        className="w-full flex items-center justify-center bg-[#F8FAF8] rounded-xl border border-[#E3EAE5] text-[#698476] text-[12px]"
        style={{ height }}
      >
        No spectral data available for plotting.
      </div>
    );
  }

  // Calculate viewBox and ranges
  const minWn = Math.min(...wavenumbers);
  const maxWn = Math.max(...wavenumbers);
  const minAbs = Math.min(...absorbance);
  const maxAbs = Math.max(...absorbance);

  // SVG internal coordinates
  const svgWidth = 800;
  const svgHeight = height;
  const padding = { top: 25, right: 30, bottom: 35, left: 55 };
  const plotWidth = svgWidth - padding.left - padding.right;
  const plotHeight = svgHeight - padding.top - padding.bottom;

  // In IR spectroscopy, X-axis is conventionally inverted (4000 on left, 650 on right)
  const getX = (wn: number) => {
    const fraction = (maxWn - wn) / (maxWn - minWn || 1);
    return padding.left + fraction * plotWidth;
  };

  const getY = (abs: number) => {
    const range = (maxAbs - minAbs) || 1;
    const fraction = (abs - minAbs) / range;
    return padding.top + (1 - fraction) * plotHeight;
  };

  // Build SVG path
  let pathD = '';
  let areaD = '';

  wavenumbers.forEach((wn, i) => {
    const x = getX(wn);
    const y = getY(absorbance[i]);
    if (i === 0) {
      pathD += `M ${x} ${y}`;
      areaD += `M ${x} ${padding.top + plotHeight} L ${x} ${y}`;
    } else {
      pathD += ` L ${x} ${y}`;
      areaD += ` L ${x} ${y}`;
    }
  });

  const lastX = getX(wavenumbers[wavenumbers.length - 1]);
  areaD += ` L ${lastX} ${padding.top + plotHeight} Z`;

  // Theoretical pure turmeric baseline overlay (curcumin peaks higher, starch lower)
  let refPathD = '';
  if (showReference) {
    wavenumbers.forEach((wn, i) => {
      // Approximate pure spectrum adjustment
      let adj = absorbance[i];
      if (wn >= 980 && wn <= 1060) adj *= 0.88; // less starch
      if (wn >= 1480 && wn <= 1530) adj *= 1.12; // more curcuminoid
      const x = getX(wn);
      const y = getY(adj);
      refPathD += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
    });
  }

  // Key chemical peak markers
  const markers = [
    { wn: 1020, label: 'Starch C-O-C', desc: 'Wheat flour adulterant marker (~1020 cm⁻¹)' },
    { wn: 1650, label: 'Amide I', desc: 'Gluten protein peptide bond (~1650 cm⁻¹)' },
    { wn: 1510, label: 'Curcuminoid', desc: 'Turmeric curcumin aromatic ring (~1510 cm⁻¹)' },
    { wn: 3350, label: 'O-H Stretch', desc: 'Hydrogen bonded hydroxyl (~3350 cm⁻¹)' },
  ];

  // Grid tick values
  const xTicks = [4000, 3500, 3000, 2500, 2000, 1500, 1000, 650];
  const yTicks = [
    minAbs,
    minAbs + (maxAbs - minAbs) * 0.33,
    minAbs + (maxAbs - minAbs) * 0.66,
    maxAbs,
  ];

  return (
    <div className="w-full bg-[#FFFFFF] rounded-xl border border-[#E3E9E5] p-4 shadow-xs">
      {/* Header with Title and Toggles */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-[13px] font-bold text-[#153822]">
              ATR-FTIR Absorption Spectrum
            </h4>
            <span className="text-[10px] px-2 py-0.5 rounded-md font-semibold bg-[#EEF5F0] text-[#1D5131]">
              4000 – 650 cm⁻¹
            </span>
          </div>
          <p className="text-[11px] text-[#698476] mt-0.5">
            {sampleId} {actualLevel !== undefined && actualLevel !== null ? `(Ground Truth: ${actualLevel}%)` : ''}
            {predictedClass ? ` • Model Pred: ${predictedClass}` : ''}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowReference(!showReference)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-colors ${
              showReference
                ? 'bg-[#153822] text-white border-[#153822]'
                : 'bg-[#F6FAF7] text-[#3E5C4B] border-[#DCE5DF] hover:bg-[#EEF5F0]'
            }`}
          >
            <Layers className="w-3 h-3" />
            <span>Pure Turmeric Baseline</span>
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto select-none"
          style={{ maxHeight: height }}
          onMouseLeave={() => setHoverIndex(null)}
        >
          {/* Background Grid */}
          {yTicks.map((abs, idx) => (
            <line
              key={`y-grid-${idx}`}
              x1={padding.left}
              y1={getY(abs)}
              x2={padding.left + plotWidth}
              y2={getY(abs)}
              stroke="#EDF3EF"
              strokeDasharray="3 3"
              strokeWidth={1}
            />
          ))}

          {xTicks.map((wn, idx) => (
            <line
              key={`x-grid-${idx}`}
              x1={getX(wn)}
              y1={padding.top}
              x2={getX(wn)}
              y2={padding.top + plotHeight}
              stroke="#EDF3EF"
              strokeDasharray="3 3"
              strokeWidth={1}
            />
          ))}

          {/* Shaded Area Under Curve */}
          <path d={areaD} fill="rgba(21, 56, 34, 0.05)" />

          {/* Reference Overlay (if enabled) */}
          {showReference && (
            <path
              d={refPathD}
              fill="none"
              stroke="#A37A20"
              strokeWidth={1.5}
              strokeDasharray="4 3"
              opacity={0.85}
            />
          )}

          {/* Main Spectrum Curve */}
          <path
            d={pathD}
            fill="none"
            stroke="#153822"
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* Chemical Marker Bands (Vertical lines & labels) */}
          {showAnnotations &&
            markers.map((m, idx) => {
              const x = getX(m.wn);
              if (x < padding.left || x > padding.left + plotWidth) return null;
              return (
                <g key={`marker-${idx}`} className="opacity-80 hover:opacity-100">
                  <line
                    x1={x}
                    y1={padding.top}
                    x2={x}
                    y2={padding.top + plotHeight}
                    stroke="#1E7D46"
                    strokeWidth={1}
                    strokeDasharray="2 3"
                  />
                  <rect
                    x={x - 32}
                    y={padding.top - 18}
                    width={64}
                    height={14}
                    rx={3}
                    fill="#EBF5EE"
                    stroke="#D5E6DA"
                    strokeWidth={1}
                  />
                  <text
                    x={x}
                    y={padding.top - 8}
                    textAnchor="middle"
                    className="text-[9px] font-bold fill-[#153822]"
                  >
                    {m.label}
                  </text>
                </g>
              );
            })}

          {/* X-Axis Ticks & Labels */}
          {xTicks.map((wn, idx) => (
            <text
              key={`x-label-${idx}`}
              x={getX(wn)}
              y={padding.top + plotHeight + 18}
              textAnchor="middle"
              className="text-[10px] font-medium fill-[#637F70]"
            >
              {wn}
            </text>
          ))}
          <text
            x={padding.left + plotWidth / 2}
            y={padding.top + plotHeight + 32}
            textAnchor="middle"
            className="text-[10px] font-semibold fill-[#415C4D]"
          >
            Wavenumber (cm⁻¹)
          </text>

          {/* Y-Axis Ticks & Labels */}
          {yTicks.map((abs, idx) => (
            <text
              key={`y-label-${idx}`}
              x={padding.left - 8}
              y={getY(abs) + 3}
              textAnchor="end"
              className="text-[10px] font-medium fill-[#637F70]"
            >
              {abs.toFixed(2)}
            </text>
          ))}
          <text
            x={-svgHeight / 2}
            y={14}
            transform="rotate(-90)"
            textAnchor="middle"
            className="text-[10px] font-semibold fill-[#415C4D]"
          >
            Absorbance (A)
          </text>
        </svg>
      </div>

      {/* Legend & Explanations */}
      <div className="mt-2.5 pt-2 border-t border-[#EEF3F0] flex flex-wrap items-center justify-between text-[11px] text-[#557162]">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-[#153822] rounded-full" />
            <span className="font-semibold text-[#183623]">Sample Spectrum</span>
          </div>
          {showReference && (
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-[#A37A20] border-t border-dashed" />
              <span className="font-semibold text-[#664C0E]">Pure Turmeric (0%)</span>
            </div>
          )}
        </div>

        <div className="text-[10px] text-[#718E7E]">
          Wheat flour adulteration manifests prominently in starch C-O-C bands (980–1050 cm⁻¹) & gluten Amide I (1650 cm⁻¹).
        </div>
      </div>
    </div>
  );
};
