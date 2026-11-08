export type NavPage =
  | 'overview'
  | 'analyze'
  | 'history'
  | 'reports'
  | 'dataset'
  | 'model'
  | 'settings'
  | 'docs';

export type Language = 'en' | 'hi';

export interface SystemStatus {
  status: string;
  version: string;
  model_version: string;
  model_available: boolean;
  metadata_available: boolean;
  python_env_active: boolean;
  supported_modality: string;
  feature_count: number;
  discrete_classes: string[];
  has_gemini_key: boolean;
  gemini_model: string;
}

export interface BenchmarkSample {
  sample_id: string;
  actual_level: number;
  is_pure: boolean;
  wavenumbers: number[];
  absorbance: number[];
  full_spectrum_length: number;
}

export interface PeakInfo {
  wavenumber: number;
  absorbance: number;
}

export interface SpectralEvidence {
  starch_coc_band: PeakInfo;
  amide_i_gluten_band: PeakInfo;
  curcuminoid_band: PeakInfo;
  water_oh_band: PeakInfo;
}

export interface PredictionData {
  predicted_class: string;
  predicted_percentage: number | null;
  model_version: string;
  probabilities: null;
  probability_note: string;
  regression_note: string;
}

export interface AnalysisReport {
  summary: string;
  interpretation: string;
  supporting_evidence: string[];
  analysis_mode: string;
}

export interface UncertaintyData {
  status: 'clean' | 'caution' | 'warning';
  flags: string[];
  recommendations: string[];
}

export interface StructuredAnswers {
  q1_what_detected: string;
  q2_what_it_means: string;
  q3_supporting_evidence: string;
  q4_uncertainties_limitations: string;
  q5_what_next: string;
}

export interface ExplanationFiveSections {
  what_we_found: string;
  what_it_means: string;
  supporting_evidence: string;
  important_limitations: string;
  recommended_next_step: string;
}

export interface EvidenceOverview {
  input_validation: string;
  analyzed_modality: string;
  feature_compatibility: string;
  evidence_availability: string;
}

export interface TrustFactor {
  label: string;
  status: 'verified' | 'caution';
  explanation: string;
}

export interface GlossaryTerm {
  term: string;
  explanation: string;
}

export interface AnalysisResult {
  success: boolean;
  sample_id: string;
  analysis_date?: string;
  input_modality?: string;
  actual_level: number | null;
  is_pure: boolean;
  prediction: PredictionData;
  spectral_evidence: SpectralEvidence;
  spectrum_chart: {
    wavenumbers: number[];
    absorbance: number[];
  };
  structured_answers?: StructuredAnswers;
  explanation_five_sections?: ExplanationFiveSections;
  evidence_overview?: EvidenceOverview;
  trust_factors?: TrustFactor[];
  glossary_terms?: GlossaryTerm[];
  analysis: AnalysisReport;
  uncertainty: UncertaintyData;
  limitations: string[];
  recommended_verification: string;
  disclaimer: string;
  record_id?: string;
}

export interface HistoryRecord {
  id: string;
  timestamp: string;
  sample_id: string;
  sample_name: string;
  batch_id: string;
  actual_level: number | null;
  predicted_class: string;
  predicted_percentage: number | null;
  is_pure: boolean;
  status: string;
  summary: string;
  uncertainty_status: string;
  result_data: AnalysisResult;
}

export interface ModelMetadata {
  model_version: string;
  modality_configuration: string[];
  classification_model: string;
  regression_model: string;
  feature_order: {
    FTIR: string[];
    Color?: string[];
    Image?: string[];
  };
  pca_components_and_explained_variance: {
    FTIR: {
      components: number;
      explained_variance: number;
    };
  };
  class_labels_percentage: number[];
  training_split: {
    training_sample_count: number;
    heldout_sample_count: number;
    cross_validation: string;
  };
  classification_cv_metrics: {
    Accuracy: { mean: number; std: number };
    'Macro Precision': { mean: number; std: number };
    'Macro Recall': { mean: number; std: number };
    'Macro F1': { mean: number; std: number };
  };
  regression_cv_metrics: {
    MAE: { mean: number; std: number };
    RMSE: { mean: number; std: number };
    R2: { mean: number; std: number };
  };
  heldout_metrics: {
    'Test Accuracy': number;
    'Test Macro F1': number;
    'Regression Test MAE': number;
    'Regression Test R2': number;
  };
  probability_calibration: string;
  limitations?: string;
}
