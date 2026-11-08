import express from 'express';
import { createServer as createViteServer } from 'vite';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;
const PROJECT_ROOT = path.resolve(__dirname, 'FoodSure-AI');
const PYTHON_BIN = path.join(PROJECT_ROOT, '.venv', 'bin', 'python');
const CLI_RUNNER = path.join(PROJECT_ROOT, 'cli_runner.py');
const HISTORY_FILE = path.join(PROJECT_ROOT, 'analysis_history.json');

app.use(express.json({ limit: '20mb' }));
app.use(express.urlencoded({ extended: true, limit: '20mb' }));

// Helper to execute Python CLI runner
function runPythonCli(action: string, inputPayload?: any): Promise<any> {
  return new Promise((resolve, reject) => {
    const env = {
      ...process.env,
      PYTHONPATH: PROJECT_ROOT,
    };

    const py = spawn(PYTHON_BIN, [CLI_RUNNER, action], { env });
    let stdoutData = '';
    let stderrData = '';

    if (inputPayload) {
      py.stdin.write(JSON.stringify(inputPayload));
      py.stdin.end();
    }

    py.stdout.on('data', (chunk) => {
      stdoutData += chunk.toString();
    });

    py.stderr.on('data', (chunk) => {
      stderrData += chunk.toString();
    });

    py.on('close', (code) => {
      if (code !== 0) {
        console.error(`Python process exited with code ${code}:`, stderrData);
        return reject(new Error(stderrData || `Python CLI exited with code ${code}`));
      }
      try {
        const parsed = JSON.parse(stdoutData.trim());
        resolve(parsed);
      } catch (err) {
        console.error('Failed to parse Python output:', stdoutData);
        reject(new Error('Invalid JSON received from Python inference engine'));
      }
    });

    py.on('error', (err) => {
      reject(err);
    });
  });
}

// Ensure history file exists
if (!fs.existsSync(HISTORY_FILE)) {
  fs.writeFileSync(HISTORY_FILE, JSON.stringify([]), 'utf-8');
}

// ── API ROUTES ─────────────────────────────────────────────────────────────

// System status and capability check
app.get('/api/status', (req, res) => {
  const modelExists = fs.existsSync(path.join(PROJECT_ROOT, 'models', 'foodsure_multimodal_v1.joblib'));
  const metadataExists = fs.existsSync(path.join(PROJECT_ROOT, 'models', 'foodsure_multimodal_v1_metadata.json'));
  const venvExists = fs.existsSync(PYTHON_BIN);

  res.json({
    status: 'online',
    version: '1.0.0',
    model_version: 'foodsure-ml-v1',
    model_available: modelExists,
    metadata_available: metadataExists,
    python_env_active: venvExists,
    supported_modality: 'FTIR Spectroscopy',
    feature_count: 2522,
    discrete_classes: ['0%', '1%', '2%', '3%', '5%', '7%', '9%'],
    has_gemini_key: Boolean(process.env.GEMINI_API_KEY),
    gemini_model: process.env.GEMINI_MODEL || 'gemini-3.5-flash-lite',
  });
});

// Model Metadata & 5-fold CV metrics (Instant disk read)
app.get('/api/metadata', (req, res) => {
  try {
    const metaPath = path.join(PROJECT_ROOT, 'models', 'foodsure_multimodal_v1_metadata.json');
    if (fs.existsSync(metaPath)) {
      const data = JSON.parse(fs.readFileSync(metaPath, 'utf-8'));
      return res.json(data);
    }
    res.status(404).json({ error: 'Metadata not found' });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Benchmark Test Samples (Instant disk read)
app.get('/api/samples', (req, res) => {
  try {
    const precomputedPath = path.join(PROJECT_ROOT, 'precomputed_samples.json');
    if (fs.existsSync(precomputedPath)) {
      const data = JSON.parse(fs.readFileSync(precomputedPath, 'utf-8'));
      return res.json(data);
    }
    // Fallback if not generated
    runPythonCli('samples').then((s) => res.json(s)).catch((e) => res.status(500).json({ error: e.message }));
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Downloadable single-sample CSV template for upload testing
app.get('/api/sample-csv/:sampleId', async (req, res) => {
  try {
    const { sampleId } = req.params;
    const meta = await runPythonCli('metadata');
    const cols: string[] = meta.feature_order.FTIR;
    
    // Get sample spectral data
    const samples = await runPythonCli('samples');
    const sample = samples.find((s: any) => s.sample_id === sampleId) || samples[0];
    
    // Generate CSV content
    // Row header: Sample_ID, followed by the 2522 wavenumber column names
    const header = ['Sample_ID', ...cols].join(',');
    // Sample full unscaled values (using the sample absorbance or zeros)
    const valRow = [sample.sample_id, ...Array(cols.length).fill(0).map((_, i) => {
      // Interpolate from subsampled absorbance or constant for testing
      const subIdx = Math.floor((i / cols.length) * sample.absorbance.length);
      return (sample.absorbance[subIdx] || 0.85).toFixed(5);
    })].join(',');

    const csvContent = `${header}\n${valRow}\n`;
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename="${sample.sample_id}_ftir_spectrum.csv"`);
    res.send(csvContent);
  } catch (err: any) {
    res.status(500).send(`Failed to generate sample CSV: ${err.message}`);
  }
});

// Core Dual-Stage Analysis & AI Interpretation
app.post('/api/analyze', async (req, res) => {
  try {
    const payload = req.body;
    const result = await runPythonCli('analyze', payload);

    // Persist to history
    try {
      const historyRaw = fs.readFileSync(HISTORY_FILE, 'utf-8');
      const history = JSON.parse(historyRaw);
      const record = {
        id: `FS-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
        timestamp: new Date().toISOString(),
        sample_id: result.sample_id,
        sample_name: payload.sample_name || result.sample_id,
        batch_id: payload.batch_id || 'BATCH-2026-A',
        actual_level: result.actual_level,
        predicted_class: result.prediction.predicted_class,
        predicted_percentage: result.prediction.predicted_percentage,
        is_pure: result.is_pure,
        status: result.is_pure ? 'Pure Turmeric' : 'Adulterated',
        summary: result.analysis.summary,
        uncertainty_status: result.uncertainty.status,
        result_data: result,
      };
      history.unshift(record);
      // Keep latest 100 records
      fs.writeFileSync(HISTORY_FILE, JSON.stringify(history.slice(0, 100), null, 2), 'utf-8');
      result.record_id = record.id;
    } catch (saveErr) {
      console.warn('Could not save analysis history:', saveErr);
    }

    res.json(result);
  } catch (err: any) {
    console.error('Analysis failed:', err);
    res.status(400).json({ error: err.message || 'Analysis pipeline execution failed.' });
  }
});

// Analysis History
app.get('/api/history', (req, res) => {
  try {
    const raw = fs.readFileSync(HISTORY_FILE, 'utf-8');
    const list = JSON.parse(raw);
    res.json(list);
  } catch (err) {
    res.json([]);
  }
});

app.delete('/api/history/:id', (req, res) => {
  try {
    const { id } = req.params;
    const raw = fs.readFileSync(HISTORY_FILE, 'utf-8');
    const list = JSON.parse(raw);
    const updated = list.filter((item: any) => item.id !== id);
    fs.writeFileSync(HISTORY_FILE, JSON.stringify(updated, null, 2), 'utf-8');
    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// ── VITE MIDDLEWARE SETUP ──────────────────────────────────────────────────

async function startServer() {
  const isDev = process.env.NODE_ENV !== 'production';

  if (isDev) {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);

    // Fallback HTML handler in dev mode
    app.use('*', async (req, res, next) => {
      try {
        const url = req.originalUrl;
        const indexPath = path.resolve(__dirname, 'index.html');
        let template = fs.readFileSync(indexPath, 'utf-8');
        template = await vite.transformIndexHtml(url, template);
        res.status(200).set({ 'Content-Type': 'text/html' }).end(template);
      } catch (e: any) {
        next(e);
      }
    });
  } else {
    const distPath = path.resolve(__dirname, 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`FoodSure AI Server running on port ${PORT} [${isDev ? 'DEVELOPMENT' : 'PRODUCTION'}]`);
  });
}

startServer();
