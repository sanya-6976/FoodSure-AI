import React, { useState, useEffect } from 'react';
import {
  NavPage,
  Language,
  SystemStatus,
  ModelMetadata,
  BenchmarkSample,
  HistoryRecord,
  AnalysisResult,
} from './types';
import { Sidebar } from './components/Sidebar';
import { TopNav } from './components/TopNav';
import { SplashLoader } from './components/SplashLoader';
import { ProcessingModal } from './components/ProcessingModal';

// Views
import { OverviewView } from './views/OverviewView';
import { NewAnalysisView } from './views/NewAnalysisView';
import { AnalysisResultsView } from './views/AnalysisResultsView';
import { AnalysisHistoryView } from './views/AnalysisHistoryView';
import { ReportsView } from './views/ReportsView';
import { DatasetMethodologyView } from './views/DatasetMethodologyView';
import { ModelInfoView } from './views/ModelInfoView';
import { SettingsView } from './views/SettingsView';
import { DocumentationView } from './views/DocumentationView';

export default function App() {
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [currentPage, setCurrentPage] = useState<NavPage>('overview');
  const [lang, setLang] = useState<Language>('en');

  // Backend States
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [metadata, setMetadata] = useState<ModelMetadata | null>(null);
  const [samples, setSamples] = useState<BenchmarkSample[]>([]);
  const [history, setHistory] = useState<HistoryRecord[]>([]);

  // Active Analysis State
  const [selectedBenchmark, setSelectedBenchmark] = useState<BenchmarkSample | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzingSampleId, setAnalyzingSampleId] = useState('FS-SMP-2026');
  const [currentResult, setCurrentResult] = useState<AnalysisResult | null>(null);
  const [showResultsView, setShowResultsView] = useState(false);

  // Load initial backend state
  useEffect(() => {
    // Safety fallback: ensure UI is visible within 300ms no matter what
    const safetyTimer = setTimeout(() => {
      setLoadingInitial(false);
    }, 300);

    async function initData() {
      try {
        const [statusRes, metaRes, samplesRes, histRes] = await Promise.allSettled([
          fetch('/api/status').then((r) => r.json()),
          fetch('/api/metadata').then((r) => r.json()),
          fetch('/api/samples').then((r) => r.json()),
          fetch('/api/history').then((r) => r.json()),
        ]);

        if (statusRes.status === 'fulfilled') setSystemStatus(statusRes.value);
        if (metaRes.status === 'fulfilled') setMetadata(metaRes.value);
        if (samplesRes.status === 'fulfilled' && Array.isArray(samplesRes.value)) {
          setSamples(samplesRes.value);
          if (samplesRes.value.length > 0) {
            setSelectedBenchmark(samplesRes.value[0]);
          }
        }
        if (histRes.status === 'fulfilled' && Array.isArray(histRes.value)) {
          setHistory(histRes.value);
          if (histRes.value.length > 0) {
            setCurrentResult(histRes.value[0].result_data);
          }
        }
      } catch (err) {
        console.warn('Initial data load warning:', err);
      } finally {
        setLoadingInitial(false);
      }
    }

    initData();
    return () => clearTimeout(safetyTimer);
  }, []);

  const handleStartAnalysis = async (payload: any) => {
    setIsAnalyzing(true);
    setAnalyzingSampleId(payload.sample_id || 'Custom Sample');

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Analysis failed with code ${res.status}`);
      }

      const analysisData: AnalysisResult = await res.json();
      setCurrentResult(analysisData);

      // Refresh history from backend
      const updatedHist = await fetch('/api/history').then((r) => r.json()).catch(() => []);
      if (Array.isArray(updatedHist)) {
        setHistory(updatedHist);
      }

      // Small delay for natural transition
      setTimeout(() => {
        setIsAnalyzing(false);
        setShowResultsView(true);
      }, 500);
    } catch (err: any) {
      setIsAnalyzing(false);
      alert(`Analysis Error: ${err.message || 'Failed to complete analysis.'}`);
    }
  };

  const handleDeleteHistoryRecord = async (id: string) => {
    try {
      await fetch(`/api/history/${id}`, { method: 'DELETE' });
      setHistory((prev) => prev.filter((h) => h.id !== id));
    } catch (err) {
      console.error('Delete history error:', err);
    }
  };

  const handleSelectSampleForAnalysis = (sample: BenchmarkSample) => {
    setSelectedBenchmark(sample);
    setShowResultsView(false);
    setCurrentPage('analyze');
  };

  const handleViewReport = (result: AnalysisResult) => {
    setCurrentResult(result);
    setCurrentPage('reports');
  };

  const handleSearch = (query: string) => {
    const q = query.toLowerCase();
    // Check if matches benchmark sample
    const foundSample = samples.find((s) => s.sample_id.toLowerCase().includes(q));
    if (foundSample) {
      setSelectedBenchmark(foundSample);
      setCurrentPage('analyze');
      return;
    }
    // Otherwise open history
    setCurrentPage('history');
  };

  if (loadingInitial) {
    return <SplashLoader />;
  }

  return (
    <div className="flex h-screen bg-[#FBFDFB] text-[#112619] font-sans antialiased overflow-hidden select-none">
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <Sidebar
        currentPage={currentPage}
        onNavigate={(p) => {
          setShowResultsView(false);
          setCurrentPage(p);
        }}
        lang={lang}
        systemStatus={systemStatus}
      />

      {/* ── Main Application Workspace ───────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <TopNav
          currentPage={currentPage}
          onNavigate={(p) => {
            setShowResultsView(false);
            setCurrentPage(p);
          }}
          lang={lang}
          onToggleLang={() => setLang(lang === 'en' ? 'hi' : 'en')}
          systemStatus={systemStatus}
          onSearch={handleSearch}
        />

        {/* Scrollable View Container */}
        <main className="flex-1 overflow-y-auto px-6 py-6 lg:px-8">
          {showResultsView && currentResult ? (
            <AnalysisResultsView
              result={currentResult}
              lang={lang}
              onNavigate={(p) => {
                setShowResultsView(false);
                setCurrentPage(p);
              }}
              onViewReport={handleViewReport}
              onNewAnalysis={() => {
                setShowResultsView(false);
                setCurrentPage('analyze');
              }}
            />
          ) : (
            <>
              {currentPage === 'overview' && (
                <OverviewView
                  onNavigate={setCurrentPage}
                  lang={lang}
                  systemStatus={systemStatus}
                  history={history}
                  samples={samples}
                  onSelectSampleForAnalysis={handleSelectSampleForAnalysis}
                  onViewReport={handleViewReport}
                />
              )}

              {currentPage === 'analyze' && (
                <NewAnalysisView
                  lang={lang}
                  systemStatus={systemStatus}
                  samples={samples}
                  selectedBenchmark={selectedBenchmark}
                  onSelectBenchmark={setSelectedBenchmark}
                  onStartAnalysis={handleStartAnalysis}
                  isAnalyzing={isAnalyzing}
                />
              )}

              {currentPage === 'history' && (
                <AnalysisHistoryView
                  history={history}
                  lang={lang}
                  onViewReport={handleViewReport}
                  onDeleteRecord={handleDeleteHistoryRecord}
                  onNavigate={setCurrentPage}
                />
              )}

              {currentPage === 'reports' && (
                <ReportsView
                  currentResult={currentResult}
                  history={history}
                  lang={lang}
                />
              )}

              {currentPage === 'dataset' && (
                <DatasetMethodologyView lang={lang} />
              )}

              {currentPage === 'model' && (
                <ModelInfoView metadata={metadata} lang={lang} />
              )}

              {currentPage === 'settings' && (
                <SettingsView
                  lang={lang}
                  onSetLang={setLang}
                  onNavigate={setCurrentPage}
                />
              )}

              {currentPage === 'docs' && <DocumentationView lang={lang} />}
            </>
          )}
        </main>
      </div>

      {/* ── Processing Multi-Stage Modal ─────────────────────────────────── */}
      <ProcessingModal
        isOpen={isAnalyzing}
        sampleId={analyzingSampleId}
        hasGeminiKey={Boolean(systemStatus?.has_gemini_key)}
      />
    </div>
  );
}
