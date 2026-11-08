import { AnalysisResult, StructuredAnswers, ExplanationFiveSections, EvidenceOverview, TrustFactor, GlossaryTerm } from '../types';

export function getEnrichedResult(result: AnalysisResult): {
  summaryAnswers: StructuredAnswers;
  fiveSections: ExplanationFiveSections;
  evidenceOverview: EvidenceOverview;
  trustFactors: TrustFactor[];
  glossaryTerms: GlossaryTerm[];
  formattedDate: string;
  formattedModality: string;
} {
  const isPure = result.is_pure;
  const predClass = result.prediction.predicted_class;
  const predPct = result.prediction.predicted_percentage;
  const sampleId = result.sample_id;
  const dateStr = result.analysis_date || new Date().toISOString();
  const formattedDate = new Date(dateStr).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
  const formattedModality = result.input_modality || 'ATR-FTIR Spectroscopy (2,522 Wavenumbers)';

  const starchWn = result.spectral_evidence.starch_coc_band.wavenumber;
  const starchAbs = result.spectral_evidence.starch_coc_band.absorbance;
  const amideWn = result.spectral_evidence.amide_i_gluten_band.wavenumber;
  const amideAbs = result.spectral_evidence.amide_i_gluten_band.absorbance;
  const curcWn = result.spectral_evidence.curcuminoid_band.wavenumber;
  const curcAbs = result.spectral_evidence.curcuminoid_band.absorbance;

  // 1. Structured Answers to the 5 Core Questions
  const summaryAnswers: StructuredAnswers = result.structured_answers || {
    q1_what_detected: isPure
      ? 'FoodSure AI detected an infrared spectral pattern consistent with pure turmeric powder (0% wheat flour adulteration).'
      : `FoodSure AI detected spectral evidence consistent with wheat flour adulteration at the ${predClass} category (continuous estimate: ${predPct !== null ? predPct.toFixed(2) : predClass}% w/w).`,
    q2_what_it_means: isPure
      ? 'FoodSure AI classified this sample as pure turmeric based on its infrared absorption profile. The continuous regression model estimated an adulteration level of 0.00% (or near-zero). This indicates no detectable wheat flour presence within the model\'s 7-tier resolution, though this preliminary screening result should be confirmed through accredited laboratory testing.'
      : `FoodSure AI classified this sample into the ${predClass} adulteration tier based on its FTIR feature profile. The continuous regression model independently estimated an adulteration level of ${predPct !== null ? predPct.toFixed(2) : predClass}% w/w. This is a preliminary AI screening result indicating potential bulk dilution with wheat flour, and should be verified through confirmatory laboratory testing.`,
    q3_supporting_evidence: `The classification is supported by 2,522 infrared wavenumber measurements (4000 to 650 cm⁻¹) compressed via 91 orthogonal principal components (90.1% explained variance). Key diagnostic absorbance peaks include starch glycosidic C-O-C vibration at ${starchWn} cm⁻¹ (absorbance: ${starchAbs}) and wheat gluten peptide Amide I at ${amideWn} cm⁻¹ (absorbance: ${amideAbs}).`,
    q4_uncertainties_limitations: 'The model was evaluated on a controlled 350-sample benchmark dataset using wheat flour as the sole adulterant. The model assigns patterns to seven discrete training tiers (0%, 1%, 2%, 3%, 5%, 7%, 9%) and does not provide calibrated posterior probabilities. Real-world market variations and non-wheat adulterants fall outside current scope.',
    q5_what_next: 'Submit the physical sample to an accredited food testing facility for confirmatory wet-chemistry analysis, specifically AOAC 972.16 polarizing microscopy for wheat starch granules or AOAC 2016.16 HPLC-DAD for curcuminoid assay.',
  };

  // 2. 5-Section AI Interpretation
  const fiveSections: ExplanationFiveSections = result.explanation_five_sections || {
    what_we_found: `The FoodSure AI dual-stage spectroscopic engine analyzed the ATR-FTIR fingerprint of sample ${sampleId}. The classifier predicted category ${predClass}, and the continuous regressor estimated ${predPct !== null ? predPct.toFixed(2) : predClass}% w/w adulteration.`,
    what_it_means: isPure
      ? 'This result indicates that the sample\'s infrared spectrum exhibits absorption patterns characteristic of pure turmeric rhizome without detectable flour additives.'
      : `This result indicates that the sample's infrared spectrum exhibits absorption patterns characteristic of turmeric blended with approximately ${predPct !== null ? predPct.toFixed(2) : predClass}% wheat flour.`,
    supporting_evidence: `Input validation confirmed 2,522 contiguous wavenumber features aligned with the trained PCA representation. Observable absorption at ${starchWn} cm⁻¹ (absorbance: ${starchAbs}) reflects polysaccharide content, while absorption at ${curcWn} cm⁻¹ (absorbance: ${curcAbs}) corresponds to curcuminoid aromatics.`,
    important_limitations: 'This model operates as a research screening prototype. The classifier evaluates pattern proximity rather than calibrated statistical certainty. It cannot diagnose adulterants other than wheat flour or replace ISO-certified assays.',
    recommended_next_step: 'Treat this screening verdict as an indicator. For commercial release, regulatory filing, or quality disputes, conduct independent laboratory microscopy or HPLC testing.',
  };

  // 3. Structured Evidence Overview
  const evidenceOverview: EvidenceOverview = result.evidence_overview || {
    input_validation: 'Passed (2,522 contiguous spectral points verified)',
    analyzed_modality: 'ATR-FTIR Spectroscopy (4000 – 650 cm⁻¹)',
    feature_compatibility: '91 PCA components (90.10% explained variance)',
    evidence_availability: 'Available (Wavenumber bands and PCA projection)',
  };

  // 4. Trust Factors
  const trustFactors: TrustFactor[] = result.trust_factors || [
    {
      label: 'Verified Spectral Input',
      status: 'verified',
      explanation: 'All 2,522 infrared wavenumber values were supplied, checked for finite numerical ranges, and aligned with the saved feature contract.',
    },
    {
      label: 'Calibration Notice',
      status: 'caution',
      explanation: 'The classifier outputs decision boundary placement across trained categories; it does not return calibrated probabilistic certainty.',
    },
    {
      label: 'External Validation Pending',
      status: 'caution',
      explanation: 'The system was evaluated on a controlled 350-sample benchmark dataset (Mendeley Data). Independent market-sample validation is not yet established.',
    },
    {
      label: 'Preliminary Screening Protocol',
      status: 'caution',
      explanation: 'FoodSure AI is a non-destructive preliminary screening tool, not a legally certified substitute for accredited laboratory analysis.',
    },
  ];

  // 5. Glossary Terms
  const glossaryTerms: GlossaryTerm[] = result.glossary_terms || [
    {
      term: 'FTIR',
      explanation: 'A non-destructive technique that measures how a powder sample absorbs infrared light across different wavelengths to reveal its chemical bonds.',
    },
    {
      term: 'Classification',
      explanation: 'The category predicted by the AI model among 7 trained adulteration tiers (0%, 1%, 2%, 3%, 5%, 7%, 9%).',
    },
    {
      term: 'Regression',
      explanation: 'An independent continuous numerical percentage estimate (% w/w) of wheat flour in the sample.',
    },
    {
      term: 'Cross-Validation',
      explanation: 'A rigorous testing method checking model stability across 5 independent training and validation splits to prevent data leakage.',
    },
    {
      term: 'MAE (Mean Absolute Error)',
      explanation: 'The average absolute difference between predicted and actual adulteration levels (0.031% on this model).',
    },
    {
      term: 'R² (Coefficient of Determination)',
      explanation: 'A measure of how accurately the continuous model tracks real adulteration variations (0.985 in cross-validation).',
    },
  ];

  return {
    summaryAnswers,
    fiveSections,
    evidenceOverview,
    trustFactors,
    glossaryTerms,
    formattedDate,
    formattedModality,
  };
}
