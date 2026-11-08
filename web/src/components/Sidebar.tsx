import React from 'react';
import {
  LayoutDashboard,
  Microscope,
  History,
  FileText,
  Database,
  Cpu,
  Settings,
  BookOpen,
  ShieldCheck,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { NavPage, Language, SystemStatus } from '../types';
import { translations } from '../i18n';

interface SidebarProps {
  currentPage: NavPage;
  onNavigate: (page: NavPage) => void;
  lang: Language;
  systemStatus: SystemStatus | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  lang,
  systemStatus,
}) => {
  const t = translations[lang];

  const navItems: { id: NavPage; label: string; icon: React.ReactNode }[] = [
    {
      id: 'overview',
      label: t.overview,
      icon: <LayoutDashboard className="w-4 h-4" strokeWidth={1.75} />,
    },
    {
      id: 'analyze',
      label: t.new_analysis,
      icon: <Microscope className="w-4 h-4" strokeWidth={1.75} />,
    },
    {
      id: 'history',
      label: t.analysis_history,
      icon: <History className="w-4 h-4" strokeWidth={1.75} />,
    },
    {
      id: 'reports',
      label: t.reports,
      icon: <FileText className="w-4 h-4" strokeWidth={1.75} />,
    },
    {
      id: 'dataset',
      label: t.dataset_methodology,
      icon: <Database className="w-4 h-4" strokeWidth={1.75} />,
    },
    {
      id: 'model',
      label: t.model_info,
      icon: <Cpu className="w-4 h-4" strokeWidth={1.75} />,
    },
    {
      id: 'settings',
      label: t.settings,
      icon: <Settings className="w-4 h-4" strokeWidth={1.75} />,
    },
    {
      id: 'docs',
      label: t.documentation,
      icon: <BookOpen className="w-4 h-4" strokeWidth={1.75} />,
    },
  ];

  return (
    <aside className="w-64 flex-shrink-0 bg-[#EBF1ED] border-r border-[#E0E7E2] flex flex-col justify-between select-none">
      {/* Top Header / Branding */}
      <div>
        <div className="p-5 pb-4 border-b border-[#E0E7E2]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#153822] text-white flex items-center justify-center shadow-xs">
              <Microscope className="w-4.5 h-4.5" strokeWidth={2} />
            </div>
            <div>
              <div className="text-[15px] font-bold tracking-tight text-[#112619] leading-none flex items-center gap-1.5">
                FoodSure AI
                <span className="text-[9px] font-semibold uppercase px-1 py-0.5 rounded bg-[#DCE6DF] text-[#1D4A2F]">
                  v1.0
                </span>
              </div>
              <p className="text-[11px] text-[#4F6858] font-medium mt-1 leading-none tracking-tight">
                {t.brand_tagline}
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          <div className="px-2.5 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-[#637D6E]">
            Platform
          </div>
          {navItems.map((item) => {
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-all text-left ${
                  isActive
                    ? 'bg-[#FFFFFF] text-[#153822] font-semibold shadow-xs border border-[#D5E1D9]'
                    : 'text-[#3D5547] hover:bg-[#E3EBE5] hover:text-[#183623]'
                }`}
              >
                <span
                  className={
                    isActive ? 'text-[#153822]' : 'text-[#567262]'
                  }
                >
                  {item.icon}
                </span>
                <span className="truncate">{item.label}</span>
                {isActive && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[#153822]" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom System Status Panel */}
      <div className="p-3.5 m-3 bg-[#FFFFFF]/80 border border-[#D9E3DC] rounded-xl shadow-xs">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#546E60] flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-[#153822]" />
            Pipeline Health
          </span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#E4F2E9] text-[#153822]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#1E7D46] animate-pulse" />
            Active
          </span>
        </div>

        <div className="space-y-1 text-[11px] text-[#465F51]">
          <div className="flex justify-between items-center py-0.5">
            <span className="text-[#6C8578]">Model Engine</span>
            <span className="font-semibold text-[#183623]">Logistic Reg + RF</span>
          </div>
          <div className="flex justify-between items-center py-0.5">
            <span className="text-[#6C8578]">Spectroscopy</span>
            <span className="font-semibold text-[#183623]">2,522 WN (FTIR)</span>
          </div>
          <div className="flex justify-between items-center py-0.5">
            <span className="text-[#6C8578]">PCA Reduction</span>
            <span className="font-semibold text-[#183623]">91 Comps (90.1%)</span>
          </div>
        </div>

        <div className="mt-2.5 pt-2 border-t border-[#E5EDE7] flex items-center justify-between text-[10px] text-[#547061]">
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-[#1E7D46]" />
            Leakage-Safe CV
          </span>
          <span className="font-semibold text-[#153822]">100% F1</span>
        </div>
      </div>
    </aside>
  );
};
