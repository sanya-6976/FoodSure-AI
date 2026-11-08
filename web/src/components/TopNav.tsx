import React, { useState } from 'react';
import {
  Search,
  Bell,
  Globe,
  Plus,
  Shield,
  CheckCircle,
  AlertTriangle,
  Info,
  ChevronRight,
  UserCheck,
} from 'lucide-react';
import { NavPage, Language, SystemStatus } from '../types';
import { translations } from '../i18n';

interface TopNavProps {
  currentPage: NavPage;
  onNavigate: (page: NavPage) => void;
  lang: Language;
  onToggleLang: () => void;
  systemStatus: SystemStatus | null;
  onSearch: (query: string) => void;
}

export const TopNav: React.FC<TopNavProps> = ({
  currentPage,
  onNavigate,
  lang,
  onToggleLang,
  systemStatus,
  onSearch,
}) => {
  const t = translations[lang];
  const [showNotifications, setShowNotifications] = useState(false);
  const [searchVal, setSearchVal] = useState('');

  const getPageTitle = (page: NavPage) => {
    switch (page) {
      case 'overview':
        return t.overview;
      case 'analyze':
        return t.new_analysis;
      case 'history':
        return t.analysis_history;
      case 'reports':
        return t.reports;
      case 'dataset':
        return t.dataset_methodology;
      case 'model':
        return t.model_info;
      case 'settings':
        return t.settings;
      case 'docs':
        return t.documentation;
      default:
        return t.overview;
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchVal.trim()) {
      onSearch(searchVal.trim());
    }
  };

  return (
    <header className="h-16 bg-[#FFFFFF] border-b border-[#E3E9E5] px-6 flex items-center justify-between flex-shrink-0 z-20">
      {/* Left: Breadcrumbs & Page Title */}
      <div className="flex items-center gap-3">
        <div className="text-[13px] font-medium text-[#657F71] flex items-center gap-1.5">
          <span>FoodSure AI</span>
          <ChevronRight className="w-3.5 h-3.5 text-[#97AC9E]" />
          <span className="font-semibold text-[#153822]">{getPageTitle(currentPage)}</span>
        </div>

        <div className="h-4 w-[1px] bg-[#E2EAE4] mx-1 hidden sm:block" />

        <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#EBF4EE] text-[#1E5232] text-[11px] font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-[#1E7D46]" />
          Dual-Stage FTIR Engine
        </div>
      </div>

      {/* Center: Quick Search Bar */}
      <form onSubmit={handleSearchSubmit} className="hidden lg:flex items-center relative w-72">
        <Search className="w-3.5 h-3.5 text-[#738E7F] absolute left-3 pointer-events-none" />
        <input
          type="text"
          value={searchVal}
          onChange={(e) => setSearchVal(e.target.value)}
          placeholder={t.search_placeholder}
          className="w-full pl-9 pr-3 py-1.5 bg-[#F6FAF7] border border-[#DCE5DF] rounded-lg text-[12px] text-[#1A3324] placeholder-[#81998C] focus:outline-none focus:border-[#153822] focus:bg-white transition-all"
        />
      </form>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5">
        {/* Language Toggle */}
        <button
          onClick={onToggleLang}
          title="Toggle Language (English / हिन्दी)"
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-[12px] font-semibold text-[#375242] hover:bg-[#F0F5F2] rounded-lg border border-[#DCE5DF] transition-colors"
        >
          <Globe className="w-3.5 h-3.5 text-[#153822]" />
          <span>{lang === 'en' ? 'हिन्दी' : 'EN'}</span>
        </button>

        {/* Notifications Popover */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 text-[#466152] hover:bg-[#F0F5F2] rounded-lg border border-[#DCE5DF] transition-colors relative"
            title="System Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#1E7D46] ring-2 ring-white" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-[#DCE5DF] p-3 z-50 animate-in fade-in slide-in-from-top-1">
              <div className="flex items-center justify-between pb-2 border-b border-[#EDF3EF] mb-2">
                <span className="text-[12px] font-bold text-[#153822]">Platform Alerts</span>
                <span className="text-[10px] text-[#698476] font-medium">3 Updates</span>
              </div>
              <div className="space-y-2 text-[11px]">
                <div className="p-2 bg-[#F6FAF7] rounded-lg border border-[#E1ECE4] flex items-start gap-2">
                  <CheckCircle className="w-3.5 h-3.5 text-[#1E7D46] mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-semibold text-[#183623]">Model Artifact Loaded</div>
                    <div className="text-[#597365]">foodsure_multimodal_v1.joblib is active with 2,522 wavenumbers.</div>
                  </div>
                </div>
                <div className="p-2 bg-[#F6FAF7] rounded-lg border border-[#E1ECE4] flex items-start gap-2">
                  <Info className="w-3.5 h-3.5 text-[#2C6287] mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-semibold text-[#183623]">Gemini AI Analyst Ready</div>
                    <div className="text-[#597365]">
                      {systemStatus?.has_gemini_key
                        ? 'Connected with Google Gemini API.'
                        : 'Operating in deterministic evidence fallback mode.'}
                    </div>
                  </div>
                </div>
                <div className="p-2 bg-[#FFF9F2] rounded-lg border border-[#F4E4D2] flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-[#B86B14] mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-semibold text-[#663A07]">Research Screening Protocol</div>
                    <div className="text-[#7D5323]">Outputs are preliminary screening estimates; confirm via ISO wet lab.</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Primary CTA */}
        {currentPage !== 'analyze' && (
          <button
            onClick={() => onNavigate('analyze')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[#153822] hover:bg-[#0F2918] text-white text-[12px] font-semibold rounded-lg shadow-xs transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{t.start_new_analysis}</span>
          </button>
        )}

        {/* User Profile Chip */}
        <div className="flex items-center gap-2 pl-2 border-l border-[#E2EAE4]">
          <div className="w-7 h-7 rounded-full bg-[#E5EFE8] border border-[#CDDDCE] text-[#153822] flex items-center justify-center font-bold text-[11px]">
            SS
          </div>
          <div className="hidden xl:block text-left">
            <div className="text-[12px] font-bold text-[#142C1D] leading-none">
              Dr. S. Sharma
            </div>
            <div className="text-[10px] text-[#698476] leading-none mt-0.5">
              Food Safety QA
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
