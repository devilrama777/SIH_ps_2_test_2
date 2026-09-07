import {
  DataSourceItem,
  ProcessingJobItem,
  JobStage,
  EvidenceItem,
  ReportItem,
  ReportSectionNode,
  EditorBlock,
  AssetRecord,
  ValidationIssueItem,
  AuditLogItem,
  SystemHealthComponent,
  SystemSecurityPosture,
  AIEditProposal,
} from '../types';
import {
  INITIAL_DATA_SOURCES,
  INITIAL_PROCESSING_JOBS,
  INITIAL_EVIDENCE_ITEMS,
  INITIAL_REPORTS,
  INITIAL_REPORT_SECTIONS,
  INITIAL_EDITOR_BLOCKS,
  INITIAL_ASSET_RECORDS,
  INITIAL_VALIDATION_ISSUES,
  INITIAL_AUDIT_LOGS,
  INITIAL_HEALTH_COMPONENTS,
  INITIAL_SECURITY_POSTURE,
} from './mockData';

const API_BASE = (typeof window !== 'undefined' && (window as any).__MINEINTEL_API_BASE__) || 'http://127.0.0.1:8765';

interface StageDefinition {
  stage: JobStage;
  progress: number;
  logMessage: (name: string) => string;
}

const PIPELINE_SEQUENCE: StageDefinition[] = [
  {
    stage: 'Discovering',
    progress: 10,
    logMessage: (name) => `Discovered '${name}'. Verifying SHA-256 checksum & MIME signatures...`,
  },
  {
    stage: 'Extracting',
    progress: 25,
    logMessage: () => `Layout parser initialized. Segmenting structural tokens and page streams...`,
  },
  {
    stage: 'OCR',
    progress: 45,
    logMessage: () => `Multi-engine OCR active (PyTesseract + EasyOCR fallback). Transcribing optical layers...`,
  },
  {
    stage: 'Table extraction',
    progress: 60,
    logMessage: () => `Table lattice detection completed. Extracted structured matrices with high confidence.`,
  },
  {
    stage: 'Image extraction',
    progress: 75,
    logMessage: () => `Visual asset isolation complete. Perceptual dHash computed and cataloged.`,
  },
  {
    stage: 'Indexing',
    progress: 90,
    logMessage: () => `Populating local SQLite FTS5 index and metadata catalog...`,
  },
  {
    stage: 'Embedding',
    progress: 98,
    logMessage: () => `Generating dense vector embeddings (BGE-M3 768-dim) for semantic retrieval...`,
  },
  {
    stage: 'Completed',
    progress: 100,
    logMessage: (name) => `Pipeline execution complete for '${name}'. 0 errors, 0 warnings.`,
  },
];

/**
 * Service Client Interface simulating Tauri IPC bridge to local Rust/Python services.
 * In a production Tauri environment, each method delegates to:
 * `window.__TAURI__.invoke('command_name', { payload })`
 */
class LocalDesktopService {
  private dataSources: DataSourceItem[] = [...INITIAL_DATA_SOURCES];
  private jobs: ProcessingJobItem[] = [...INITIAL_PROCESSING_JOBS];
  private evidence: EvidenceItem[] = [...INITIAL_EVIDENCE_ITEMS];
  private reports: ReportItem[] = [...INITIAL_REPORTS];
  private sections: ReportSectionNode[] = [...INITIAL_REPORT_SECTIONS];
  private editorBlocks: EditorBlock[] = [...INITIAL_EDITOR_BLOCKS];
  private assets: AssetRecord[] = [...INITIAL_ASSET_RECORDS];
  private validationIssues: ValidationIssueItem[] = [...INITIAL_VALIDATION_ISSUES];
  private auditLogs: AuditLogItem[] = [...INITIAL_AUDIT_LOGS];
  private healthComponents: SystemHealthComponent[] = [...INITIAL_HEALTH_COMPONENTS];
  private securityPosture: SystemSecurityPosture = { ...INITIAL_SECURITY_POSTURE };

  private workerInterval: any = null;
  private jobStartTimes: Map<string, number> = new Map();

  constructor() {
    this.jobs.forEach((job) => {
      if (job.status === 'running') {
        this.jobStartTimes.set(job.id, Date.now() - 8000);
      }
    });
    this.synthesizeAutonomousCorpus();
    this.startPipelineWorker();
  }

  private startPipelineWorker() {
    if (this.workerInterval) return;
    this.workerInterval = setInterval(() => {
      this.tickPipeline();
    }, 1200);
  }

  private tickPipeline() {
    const now = Date.now();

    for (const job of this.jobs) {
      if (job.status !== 'running') continue;

      let startTime = this.jobStartTimes.get(job.id);
      if (!startTime) {
        startTime = now - 6000;
        this.jobStartTimes.set(job.id, startTime);
      }

      const elapsedSec = Math.max(1, Math.floor((now - startTime) / 1000));
      const mins = Math.floor(elapsedSec / 60);
      const secs = elapsedSec % 60;
      job.elapsedTime = `${mins}m ${String(secs).padStart(2, '0')}s`;

      const currentStageIndex = PIPELINE_SEQUENCE.findIndex((s) => s.stage === job.currentStage);

      if (currentStageIndex === -1) {
        const first = PIPELINE_SEQUENCE[0];
        job.currentStage = first.stage;
        job.progress = first.progress;
      } else if (currentStageIndex < PIPELINE_SEQUENCE.length - 1) {
        const next = PIPELINE_SEQUENCE[currentStageIndex + 1];
        job.currentStage = next.stage;
        job.progress = next.progress;

        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        job.logs.push(`[${timeStr}] ${next.logMessage(job.jobName)}`);

        if (next.stage === 'Completed') {
          job.status = 'completed';
          job.filesProcessed = job.totalFiles;
          job.errorsCount = 0;
          job.warningsCount = 0;
          this.syncCompletedDataSource(job.jobName);
        }
      } else {
        job.status = 'completed';
        job.progress = 100;
        job.filesProcessed = job.totalFiles;
      }
    }
  }

  private syncCompletedDataSource(jobName: string) {
    const cleanName = jobName
      .replace(/^Ingestion & OCR:\s*/i, '')
      .replace(/^Reprocess Document:\s*/i, '')
      .trim()
      .toLowerCase();

    const targetDoc = this.dataSources.find(
      (d) =>
        d.filename.toLowerCase() === cleanName ||
        cleanName.includes(d.filename.toLowerCase()) ||
        d.filename.toLowerCase().includes(cleanName)
    );

    if (targetDoc) {
      targetDoc.ocrStatus = 'Completed';
      targetDoc.indexedStatus = 'Indexed';
      targetDoc.processingStatus = 'completed';
      if (!targetDoc.extractedTablesCount || targetDoc.extractedTablesCount === 0) {
        targetDoc.extractedTablesCount = 2;
      }
      if (!targetDoc.extractedImagesCount || targetDoc.extractedImagesCount === 0) {
        targetDoc.extractedImagesCount = 1;
      }
    }

    this.synthesizeAutonomousCorpus();
  }

  public synthesizeAutonomousCorpus() {
    // 1. Synthesize Reports
    this.reports = [
      {
        id: 'rep-autonomous',
        name: 'Consolidated Technical & Geological Evaluation (Block ML-492)',
        organization: 'MineIntel / Central Exploration & Operations',
        reportingPeriod: 'Q4 FY26 Technical Report',
        description: 'Autonomous multi-source synthesis across exploration boreholes, laboratory assays, field observations, and production metrics.',
        createdAt: '2026-03-01 09:00',
        lastModified: new Date().toISOString().replace('T', ' ').slice(0, 16),
        status: 'Ready for Export',
        sectionsCount: 6,
        wordCount: 3050,
        sourcesLinkedCount: 5,
        validationScore: 98,
        selectedModel: 'Autonomous Synthesis Engine (Local Airgap)',
      },
    ];

    // 2. Synthesize Evidence Items
    this.evidence = [
      {
        id: 'ev-001',
        documentId: 'doc-borehole',
        documentName: 'borehole_mining_data.csv',
        documentType: 'CSV',
        sourceLocation: 'Table 1, Drillhole Intercept Logs (Rows 12-18)',
        spreadsheetName: 'Drillhole_Assay_Log',
        cellRange: 'C12:G18',
        extractionMethod: 'Lattice Table Extractor',
        confidence: 99.4,
        relevantText: "Borehole BH-2026-04 intercepted major seam 'Seam II' at depth 45.2m to 54.8m (net thickness 9.6m). Proximate assay shows Ash content 18.4%, Moisture 5.2%, Gross Calorific Value 6,120 kcal/kg, classified under prime metallurgical Grade G4.",
        metadata: {
          year: 2026,
          month: 'March',
          organizationUnit: 'Central Exploration Division',
          date: '2026-03-02',
          authorOrSource: 'Geoconsult Core Drilling Services',
        },
        bbox: { x: 40, y: 120, width: 450, height: 180 },
      },
      {
        id: 'ev-002',
        documentId: 'doc-lab-pdf',
        documentName: 'laboratory_quality_summary.pdf',
        documentType: 'PDF',
        page: 3,
        sourceLocation: 'Page 3, Section 2.1 (Proximate Analysis Certificate)',
        extractionMethod: 'Tesseract OCR',
        confidence: 98.7,
        relevantText: 'Certified laboratory proximate assay for composite coal samples indicates Total Moisture of 6.8%, Ash Content of 24.2% (air-dried basis), Volatile Matter of 28.5%, and Fixed Carbon of 40.5%. Average Gross Calorific Value (GCV) stands at 5,420 kcal/kg, meeting statutory Grade G8 parameters with low total sulfur (0.48%).',
        metadata: {
          year: 2026,
          month: 'March',
          organizationUnit: 'Central Testing Laboratory',
          date: '2026-03-04',
          authorOrSource: 'NABL Accredited Coal Testing Division',
        },
        bbox: { x: 50, y: 180, width: 480, height: 210 },
      },
      {
        id: 'ev-003',
        documentId: 'doc-field-docx',
        documentName: 'field_observation_notes.docx',
        documentType: 'DOCX',
        page: 1,
        sourceLocation: 'Section 3 (Geotechnical Slope Inspection & Bench Assessment)',
        extractionMethod: 'Native Parser',
        confidence: 97.5,
        relevantText: 'Geotechnical survey of open-cast highwall bench #4 reveals competent sandstone overburden with Rock Mass Rating (RMR) score of 68 (Good Rock). Calculated Factor of Safety (FoS) is 1.42 under dry condition and 1.31 under hydrostatic saturation, fully complying with DGMS Circular 02 slope safety guidelines.',
        metadata: {
          year: 2026,
          month: 'March',
          organizationUnit: 'Mine Geotechnical & Safety Cell',
          date: '2026-03-05',
          authorOrSource: 'Sr. Geotechnical Engineer',
        },
        bbox: { x: 45, y: 140, width: 460, height: 160 },
      },
      {
        id: 'ev-004',
        documentId: 'doc-chart-png',
        documentName: 'mining_data_chart.png',
        documentType: 'Images',
        page: 1,
        sourceLocation: 'Figure 1.1: Production Trend & Stripping Ratio Telemetry',
        extractionMethod: 'Vector Embedding Match',
        confidence: 96.8,
        relevantText: 'Monthly excavation performance indicates Run-of-Mine (ROM) coal production of 245,000 MT/month against target 240,000 MT (+2.1%). Overburden removal reached 680,000 m3/month yielding an operational Stripping Ratio of 2.78 m3/MT, representing optimal fleet utilization across draglines and 100T dumpers.',
        metadata: {
          year: 2026,
          month: 'March',
          organizationUnit: 'Mine Operations Planning',
          date: '2026-03-05',
          authorOrSource: 'Dispatch Fleet Telemetry',
        },
        bbox: { x: 30, y: 80, width: 500, height: 250 },
      },
      {
        id: 'ev-005',
        documentId: 'doc-readme-txt',
        documentName: 'README.txt',
        documentType: 'TXT',
        page: 1,
        sourceLocation: 'Header & Exploration License Metadata',
        extractionMethod: 'Native Parser',
        confidence: 99.8,
        relevantText: 'MineIntel Exploration Block ML-492 coordinates: UTM Zone 45N (WGS84 datum, Northing 2634100m to 2638500m, Easting 432100m to 437400m). Total allocated concession area: 24.8 sq km. All drilling, sampling, and assay data collected under statutory CIL/CMPDI QA/QC protocols.',
        metadata: {
          year: 2026,
          month: 'March',
          organizationUnit: 'Land & Concession Registry',
          date: '2026-03-01',
          authorOrSource: 'Survey & Legal Division',
        },
        bbox: { x: 20, y: 50, width: 480, height: 120 },
      },
      {
        id: 'ev-006',
        documentId: 'doc-borehole-composite',
        documentName: 'borehole_mining_data.csv',
        documentType: 'CSV',
        sourceLocation: 'Table 2, Seam Correlation Summary',
        spreadsheetName: 'Seam_Reserve_Metrics',
        cellRange: 'A1:E8',
        extractionMethod: 'Lattice Table Extractor',
        confidence: 99.1,
        relevantText: 'Consolidated geological reserve estimation across Seams I, II, and III totals 42.6 Million Tonnes (MT) of proved mineable reserves with an average cumulative seam thickness of 18.4 meters and stripping ratio bounded below 3.0 m3/MT.',
        metadata: {
          year: 2026,
          month: 'March',
          organizationUnit: 'Mineral Resource Estimation Cell',
          date: '2026-03-03',
          authorOrSource: 'Competent Person Reserve Certification',
        },
        bbox: { x: 35, y: 150, width: 440, height: 170 },
      },
    ];

    // 3. Synthesize Report Section Outline
    this.sections = [
      {
        id: 'sec-1',
        title: '1.0 Executive Summary & Mine Concession Overview',
        level: 1,
        aiRationale: 'Synthesized from README.txt metadata and high-level reserve metrics.',
        linkedEvidenceCount: 2,
        status: 'validated',
        wordCount: 420,
      },
      {
        id: 'sec-2',
        title: '2.0 Geological Stratigraphy & Core Drillhole Logs',
        level: 1,
        aiRationale: 'Compiled from borehole_mining_data.csv intercept logs and seam correlations.',
        linkedEvidenceCount: 2,
        status: 'validated',
        wordCount: 680,
      },
      {
        id: 'sec-3',
        title: '3.0 Coal Quality & Certified Laboratory Assay',
        level: 1,
        aiRationale: 'Parsed from laboratory_quality_summary.pdf proximate and ultimate test parameters.',
        linkedEvidenceCount: 1,
        status: 'validated',
        wordCount: 560,
      },
      {
        id: 'sec-4',
        title: '4.0 Geotechnical Slope Stability & Field Observations',
        level: 1,
        aiRationale: 'Derived from field_observation_notes.docx bench inspections and RMR ratings.',
        linkedEvidenceCount: 1,
        status: 'validated',
        wordCount: 520,
      },
      {
        id: 'sec-5',
        title: '5.0 Mine Production, Overburden & Stripping Efficiency',
        level: 1,
        aiRationale: 'Extracted from mining_data_chart.png monthly production curves and fleet telemetry.',
        linkedEvidenceCount: 1,
        status: 'validated',
        wordCount: 490,
      },
      {
        id: 'sec-6',
        title: '6.0 Statutory Compliance & QA/QC Audit Trail',
        level: 1,
        aiRationale: 'Cross-verified provenance reconciliation across all 5 source documents.',
        linkedEvidenceCount: 2,
        status: 'validated',
        wordCount: 380,
      },
    ];

    // 4. Synthesize Editor Blocks
    this.editorBlocks = [
      // Section 1 Blocks
      {
        id: 'blk-101',
        sectionId: 'sec-1',
        type: 'heading',
        level: 1,
        content: '1.0 Executive Summary & Mine Concession Overview',
      },
      {
        id: 'blk-102',
        sectionId: 'sec-1',
        type: 'paragraph',
        content: 'This technical synthesis compiles multi-source exploration drilling, laboratory proximate assays, geotechnical field observations, and production telemetry for Mining Lease Block ML-492 (24.8 sq km). All survey benchmarks are referenced in UTM Zone 45N (WGS84 datum) under statutory CIL/CMPDI exploration protocols. Exploration confirms a high-value bituminous deposit amenable to open-cast mechanized mining.',
        citationId: 'ev-005',
        evidenceRef: {
          documentName: 'README.txt',
          location: 'Header & Exploration License Metadata',
          verified: true,
        },
      },
      {
        id: 'blk-103',
        sectionId: 'sec-1',
        type: 'callout',
        calloutType: 'statutory',
        content: 'Key Technical Findings: Total Proved Mineable Reserve: 42.6 MT • Primary Intercept: Seam II (9.6m clean coal) • Average Coal Quality: Grade G8 (5,420 kcal/kg GCV) • Highwall Slope Stability Factor of Safety: 1.42 (DGMS Compliant) • Active Stripping Ratio: 2.78 m3/MT.',
      },

      // Section 2 Blocks
      {
        id: 'blk-201',
        sectionId: 'sec-2',
        type: 'heading',
        level: 1,
        content: '2.0 Geological Stratigraphy & Core Drillhole Logs',
      },
      {
        id: 'blk-202',
        sectionId: 'sec-2',
        type: 'paragraph',
        content: "Exploration diamond core drilling confirmed persistent lateral continuity of three primary coal seams across the tenement. Borehole BH-2026-04 intercepted prime metallurgical Seam II at depth 45.2m to 54.8m with a clean net thickness of 9.6m, displaying low dirt-band inclusion and favorable hanging-wall sandstone competence.",
        citationId: 'ev-001',
        evidenceRef: {
          documentName: 'borehole_mining_data.csv',
          location: 'Table 1, Row 12-18',
          verified: true,
        },
      },
      {
        id: 'blk-203',
        sectionId: 'sec-2',
        type: 'table',
        caption: 'Table 2.1: Key Exploration Borehole Core Intercepts & Seam Quality Matrix',
        tableData: {
          headers: ['Borehole ID', 'Target Seam', 'Depth (m)', 'Thickness (m)', 'Ash (%)', 'GCV (kcal/kg)', 'Grade'],
          rows: [
            ['BH-2026-01', 'Seam I', '28.4 – 33.6', '5.2', '22.1%', '5,680', 'G7'],
            ['BH-2026-02', 'Seam I', '31.0 – 36.8', '5.8', '21.4%', '5,740', 'G7'],
            ['BH-2026-04', 'Seam II', '45.2 – 54.8', '9.6', '18.4%', '6,120', 'G4'],
            ['BH-2026-05', 'Seam III', '78.5 – 84.1', '5.6', '26.8%', '5,150', 'G9'],
          ],
        },
      },
      {
        id: 'blk-204',
        sectionId: 'sec-2',
        type: 'paragraph',
        content: 'Consolidated geological modeling yields a cumulative proved reserve of 42.6 Million Tonnes with a weighted average in-situ seam thickness of 18.4 meters. Low tectonic shearing ensures predictable long-term excavation sequencing.',
        citationId: 'ev-006',
        evidenceRef: {
          documentName: 'borehole_mining_data.csv',
          location: 'Table 2, Seam Correlation Summary',
          verified: true,
        },
      },

      // Section 3 Blocks
      {
        id: 'blk-301',
        sectionId: 'sec-3',
        type: 'heading',
        level: 1,
        content: '3.0 Coal Quality & Certified Laboratory Assay',
      },
      {
        id: 'blk-302',
        sectionId: 'sec-3',
        type: 'paragraph',
        content: 'Certified proximate and ultimate analysis of drill core composites by the NABL-accredited Central Testing Laboratory indicates consistent medium-rank bituminous coal with low total sulfur (0.48%) and high ash fusion temperature (1,380°C).',
        citationId: 'ev-002',
        evidenceRef: {
          documentName: 'laboratory_quality_summary.pdf',
          location: 'Page 3, Section 2.1',
          verified: true,
        },
      },
      {
        id: 'blk-303',
        sectionId: 'sec-3',
        type: 'table',
        caption: 'Table 3.1: Certified Composite Proximate & Ultimate Assay Results',
        tableData: {
          headers: ['Parameter', 'Measured Value', 'Test Method', 'Specification Limit', 'Compliance'],
          rows: [
            ['Total Moisture', '6.8%', 'IS 1350 (Part I)', '< 10.0%', 'Pass'],
            ['Ash Content (air-dried)', '24.2%', 'IS 1350 (Part I)', 'Grade G8 Range', 'Pass'],
            ['Volatile Matter', '28.5%', 'IS 1350 (Part I)', '25.0 – 32.0%', 'Pass'],
            ['Fixed Carbon', '40.5%', 'By difference', '> 38.0%', 'Pass'],
            ['Gross Calorific Value (GCV)', '5,420 kcal/kg', 'Bomb Calorimeter', '5,200 – 5,500 kcal/kg', 'Pass (Grade G8)'],
            ['Total Sulfur', '0.48%', 'Eschka Method', '< 0.80%', 'Pass (Low Sulfur)'],
          ],
        },
      },

      // Section 4 Blocks
      {
        id: 'blk-401',
        sectionId: 'sec-4',
        type: 'heading',
        level: 1,
        content: '4.0 Geotechnical Slope Stability & Field Observations',
      },
      {
        id: 'blk-402',
        sectionId: 'sec-4',
        type: 'paragraph',
        content: 'Geotechnical survey of open-cast highwall bench #4 reveals competent sandstone overburden with Rock Mass Rating (RMR) score of 68 (Good Rock). Calculated Factor of Safety (FoS) is 1.42 under dry condition and 1.31 under hydrostatic saturation, fully complying with DGMS Circular 02 slope safety guidelines.',
        citationId: 'ev-003',
        evidenceRef: {
          documentName: 'field_observation_notes.docx',
          location: 'Section 3 (Geotechnical Slope Inspection)',
          verified: true,
        },
      },

      // Section 5 Blocks
      {
        id: 'blk-501',
        sectionId: 'sec-5',
        type: 'heading',
        level: 1,
        content: '5.0 Mine Production, Overburden & Stripping Efficiency',
      },
      {
        id: 'blk-502',
        sectionId: 'sec-5',
        type: 'paragraph',
        content: 'Monthly excavation performance indicates Run-of-Mine (ROM) coal production of 245,000 MT/month against target 240,000 MT (+2.1%). Overburden removal reached 680,000 m3/month yielding an operational Stripping Ratio of 2.78 m3/MT, representing optimal fleet utilization across draglines and 100T dumpers.',
        citationId: 'ev-004',
        evidenceRef: {
          documentName: 'mining_data_chart.png',
          location: 'Figure 1.1: Production Trend',
          verified: true,
        },
      },

      // Section 6 Blocks
      {
        id: 'blk-601',
        sectionId: 'sec-6',
        type: 'heading',
        level: 1,
        content: '6.0 Statutory Compliance & QA/QC Audit Trail',
      },
      {
        id: 'blk-602',
        sectionId: 'sec-6',
        type: 'paragraph',
        content: 'All source datasets have undergone cryptographic SHA-256 verification and automated OCR lattice extraction. Every numerical assertion in this document is bidirectionally bound to local immutable provenance records, ensuring full readiness for statutory DGMS and corporate filing.',
      },
    ];
  }

  // ==========================================
  // System Health & Security
  // ==========================================
  async getSystemHealth(): Promise<SystemHealthComponent[]> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/health`, { method: 'GET' });
      if (res.ok) {
        const diagRes = await fetch(`${API_BASE}/api/v1/diagnostics`, { method: 'GET' });
        const diag = diagRes.ok ? await diagRes.json() : null;
        return [
          {
            id: 'srv-rest-daemon',
            name: 'Local REST API Daemon',
            engine: 'FastAPI / Uvicorn (0.141.1)',
            status: 'healthy',
            latency: '3ms',
            detail: 'Listening on 127.0.0.1:8765 (Loopback secure)',
            metrics: '0.1.0 (Air-Gapped)',
          },
          {
            id: 'srv-doc-intel',
            name: 'Document Intelligence & Extraction',
            engine: 'PyMuPDF + Docx + OpenPyXL',
            status: 'healthy',
            latency: '12ms',
            detail: 'Local multi-format extraction engine active',
            metrics: 'Canonical AST Normalizer',
          },
          {
            id: 'srv-sqlite-fts',
            name: 'SQLite FTS5 Indexing & Vector Fusion',
            engine: 'SQLite 3.45+ FTS5 BM25',
            status: 'healthy',
            latency: '5ms',
            detail: 'Local evidence database mounted in workspace',
            metrics: 'Relational & Full-Text Search',
          },
          {
            id: 'srv-ai-inference',
            name: 'Air-Gapped Local Inference Engine',
            engine: 'Local AI Gateway (Gemma / Qwen)',
            status: 'healthy',
            latency: '45ms',
            detail: diag ? `CPU: ${diag.cpu_usage_percent}% | RAM: ${diag.memory_available_gb} GB free` : 'Active local inference provider',
            metrics: 'Deterministic Heuristic Grounding',
          },
          {
            id: 'srv-firewall',
            name: 'Air-Gapped Network Firewall',
            engine: 'OS Socket Sandbox',
            status: 'healthy',
            latency: '0ms',
            detail: 'Zero external network socket egress permitted',
            metrics: 'Air-Gapped Active',
          },
        ];
      }
    } catch {
      // Graceful fallback
    }
    return [...this.healthComponents];
  }

  async getSecurityPosture(): Promise<SystemSecurityPosture> {
    return { ...this.securityPosture };
  }

  // ==========================================
  // Reports
  // ==========================================
  async getReports(): Promise<ReportItem[]> {
    return [...this.reports];
  }

  async getReportById(id: string): Promise<ReportItem | undefined> {
    return this.reports.find((r) => r.id === id);
  }

  async createReport(params: {
    name: string;
    organization: string;
    reportingPeriod: string;
    description: string;
    selectedSources: string[];
    referenceReport?: string;
    processingConfig: {
      ocr: boolean;
      tableExtraction: boolean;
      imageExtraction: boolean;
      metadataExtraction: boolean;
      indexing: boolean;
    };
    aiConfig: {
      modelName: string;
      contextLength: number;
      temperature: number;
      strictVerification: boolean;
    };
  }): Promise<ReportItem> {
    const newReport: ReportItem = {
      id: `rep-${Date.now().toString().slice(-4)}`,
      name: params.name,
      organization: params.organization,
      reportingPeriod: params.reportingPeriod,
      description: params.description,
      createdAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
      lastModified: new Date().toISOString().replace('T', ' ').slice(0, 16),
      status: 'In Progress',
      sectionsCount: 7,
      wordCount: 1850,
      sourcesLinkedCount: params.selectedSources.length,
      validationScore: 88,
      referenceReportUsed: params.referenceReport,
      selectedModel: params.aiConfig.modelName,
    };
    this.reports.unshift(newReport);
    this.logAudit({
      user: 'sysadmin@cil-airgap.internal',
      category: 'Report Generation',
      severity: 'info',
      action: 'Report Initialized',
      target: newReport.name,
      details: `Created new report plan using local model ${params.aiConfig.modelName} and ${params.selectedSources.length} attached data sources.`,
    });
    return newReport;
  }

  // ==========================================
  // Data Sources
  // ==========================================
  async getDataSources(): Promise<DataSourceItem[]> {
    return [...this.dataSources];
  }

  async addDataSource(fileData: Partial<DataSourceItem>): Promise<DataSourceItem> {
    const newDoc: DataSourceItem = {
      id: `src-${Date.now().toString().slice(-4)}`,
      filename: fileData.filename || 'New_Organizational_Record.pdf',
      type: fileData.type || 'PDF',
      sizeBytes: fileData.sizeBytes || 4829100,
      dateModified: new Date().toISOString().replace('T', ' ').slice(0, 16),
      sourcePath: fileData.sourcePath || `/data/local_repos/incoming/${fileData.filename}`,
      processingStatus: 'processing',
      pages: fileData.pages || 12,
      ocrStatus: fileData.type === 'Scanned PDF' ? 'In Progress' : 'Not Required',
      indexedStatus: 'Pending',
      extractedTablesCount: 0,
      extractedImagesCount: 0,
      summary: fileData.summary || 'Ingested document awaiting local extraction pipeline.',
      checksum: `sha256:${Math.random().toString(16).substring(2, 26)}`,
    };
    this.dataSources.unshift(newDoc);

    // Queue a background processing job
    this.addProcessingJob({
      jobName: `Ingestion & OCR: ${newDoc.filename}`,
      type: newDoc.type === 'Scanned PDF' ? 'OCR Batch' : 'Full Ingestion',
      totalFiles: 1,
    });

    this.logAudit({
      user: 'sysadmin@cil-airgap.internal',
      category: 'Data Ingestion',
      severity: 'info',
      action: 'Local Data Source Added',
      target: newDoc.filename,
      details: `Local file registered into workspace partition. Processing job queued.`,
    });

    return newDoc;
  }

  async removeDataSource(id: string): Promise<boolean> {
    const item = this.dataSources.find((d) => d.id === id);
    if (!item) return false;
    this.dataSources = this.dataSources.filter((d) => d.id !== id);
    this.logAudit({
      user: 'sysadmin@cil-airgap.internal',
      category: 'Data Ingestion',
      severity: 'warning',
      action: 'Data Source Removed',
      target: item.filename,
      details: `File removed from active corpus index. Associated vector embeddings marked for purge.`,
    });
    return true;
  }

  async reprocessDataSource(id: string): Promise<boolean> {
    const item = this.dataSources.find((d) => d.id === id);
    if (!item) return false;
    item.processingStatus = 'processing';
    this.addProcessingJob({
      jobName: `Reprocess Document: ${item.filename}`,
      type: 'Full Ingestion',
      totalFiles: 1,
    });
    return true;
  }

  // ==========================================
  // Processing Jobs
  // ==========================================
  async getProcessingJobs(): Promise<ProcessingJobItem[]> {
    return [...this.jobs];
  }

  async addProcessingJob(params: {
    jobName: string;
    type: ProcessingJobItem['type'];
    totalFiles: number;
  }): Promise<ProcessingJobItem> {
    const id = `job-${Date.now().toString().slice(-4)}`;
    this.jobStartTimes.set(id, Date.now());
    const newJob: ProcessingJobItem = {
      id,
      jobName: params.jobName,
      type: params.type,
      progress: 10,
      currentStage: 'Discovering',
      startedAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
      elapsedTime: '0m 00s',
      status: 'running',
      errorsCount: 0,
      warningsCount: 0,
      filesProcessed: 0,
      totalFiles: params.totalFiles,
      logs: [
        `[${new Date().toLocaleTimeString()}] Local worker dispatched task '${params.jobName}' to background pool`,
        `[${new Date().toLocaleTimeString()}] Checking local GPU tensor core availability... CUDA context acquired`,
        `[${new Date().toLocaleTimeString()}] Discovered '${params.jobName}'. Verifying SHA-256 checksum & MIME signatures...`,
      ],
    };
    this.jobs.unshift(newJob);
    this.startPipelineWorker();
    return newJob;
  }

  async updateJobStatus(id: string, status: 'running' | 'paused' | 'completed' | 'failed'): Promise<boolean> {
    const job = this.jobs.find((j) => j.id === id);
    if (!job) return false;

    const timeStr = new Date().toLocaleTimeString();
    if (status === 'paused') {
      job.status = 'paused';
      job.logs.push(`[${timeStr}] Job execution suspended by user.`);
    } else if (status === 'running') {
      if (job.status === 'completed' || job.status === 'failed') {
        job.status = 'running';
        job.currentStage = 'Discovering';
        job.progress = 10;
        job.filesProcessed = 0;
        job.errorsCount = 0;
        job.warningsCount = 0;
        this.jobStartTimes.set(job.id, Date.now());
        job.logs.push(`[${timeStr}] Pipeline restarted by user. Resetting stage progression.`);
      } else {
        job.status = 'running';
        job.logs.push(`[${timeStr}] Job execution resumed.`);
      }
      this.startPipelineWorker();
    } else if (status === 'failed') {
      job.status = 'failed';
      job.logs.push(`[${timeStr}] Job execution terminated / cancelled by user.`);
    } else if (status === 'completed') {
      job.status = 'completed';
      job.currentStage = 'Completed';
      job.progress = 100;
      job.filesProcessed = job.totalFiles;
      job.logs.push(`[${timeStr}] Job marked as completed.`);
      this.syncCompletedDataSource(job.jobName);
    }
    return true;
  }

  // ==========================================
  // Evidence Search
  // ==========================================
  async searchEvidence(query: string, filters?: {
    year?: number;
    month?: string;
    documentType?: string;
    documentName?: string;
    minConfidence?: number;
  }): Promise<EvidenceItem[]> {
    let results = [...this.evidence];
    if (query.trim()) {
      const q = query.toLowerCase();
      results = results.filter(
        (e) =>
          e.relevantText.toLowerCase().includes(q) ||
          e.documentName.toLowerCase().includes(q) ||
          (e.sectionName && e.sectionName.toLowerCase().includes(q)) ||
          (e.sheetName && e.sheetName.toLowerCase().includes(q)) ||
          e.sourceLocation.toLowerCase().includes(q)
      );
    }
    if (filters?.year) {
      results = results.filter((e) => e.metadata.year === filters.year);
    }
    if (filters?.documentType && filters.documentType !== 'All') {
      results = results.filter((e) => e.documentType === filters.documentType);
    }
    if (filters?.minConfidence) {
      results = results.filter((e) => e.confidence >= (filters.minConfidence || 0));
    }
    return results;
  }

  // ==========================================
  // Report Planner & Structure
  // ==========================================
  async getReportSections(): Promise<ReportSectionNode[]> {
    return JSON.parse(JSON.stringify(this.sections));
  }

  async updateSections(newSections: ReportSectionNode[]): Promise<void> {
    this.sections = JSON.parse(JSON.stringify(newSections));
  }

  // ==========================================
  // Report Editor & Blocks
  // ==========================================
  async getEditorBlocks(sectionId?: string): Promise<EditorBlock[]> {
    if (!sectionId) return [...this.editorBlocks];
    return this.editorBlocks.filter((b) => b.sectionId === sectionId);
  }

  async updateEditorBlock(updatedBlock: EditorBlock): Promise<void> {
    const idx = this.editorBlocks.findIndex((b) => b.id === updatedBlock.id);
    if (idx >= 0) {
      this.editorBlocks[idx] = updatedBlock;
    } else {
      this.editorBlocks.push(updatedBlock);
    }
  }

  async applyAIProposal(proposal: AIEditProposal): Promise<void> {
    const block = this.editorBlocks.find((b) => b.id === proposal.targetBlockId);
    if (block && proposal.proposedText) {
      block.content = proposal.proposedText;
      if (block.evidenceRef) {
        block.evidenceRef.verified = true;
      }
      this.logAudit({
        user: 'sysadmin@cil-airgap.internal',
        category: 'Agent Action',
        severity: 'info',
        action: 'AI Verification Revision Accepted',
        target: block.id,
        details: `Updated assertion from '${proposal.originalValue}' to '${proposal.verifiedValue}' based on verified ${proposal.searchedEvidence?.sourceFile || 'live source'} evidence.`,
      });

      // Also resolve corresponding validation issue if it exists
      const issue = this.validationIssues.find((v) => v.targetBlockId === block.id);
      if (issue) {
        issue.severity = 'pass';
        issue.title = `${proposal.searchedEvidence?.sourceFile || 'Live File'} Grounding Reconciled`;
        issue.description = `Verified against ${proposal.searchedEvidence?.sourceFile} (${proposal.searchedEvidence?.rangeOrSection || proposal.searchedEvidence?.sheetOrPage}).`;
      }
    }
  }

  // ==========================================
  // Contextual AI Agent Inquiry (Grounded in Live Files)
  // ==========================================
  async triggerContextualAIAgent(params: {
    reportId: string;
    sectionId: string;
    selectedBlockId: string;
    instruction: string;
  }): Promise<AIEditProposal> {
    // 1. Locate the targeted block & section from active report
    const targetBlock =
      this.editorBlocks.find((b) => b.id === params.selectedBlockId) ||
      this.editorBlocks.find((b) => b.sectionId === params.sectionId && b.type === 'paragraph') ||
      this.editorBlocks.find((b) => b.sectionId === params.sectionId) ||
      this.editorBlocks[0];

    const targetSection =
      this.sections.find((s) => s.id === params.sectionId) ||
      this.sections.find((s) => targetBlock && s.id === targetBlock.sectionId) || {
        id: params.sectionId || 'sec-5',
        title: '5.0 Mine Production, Overburden & Stripping Efficiency',
        level: 1,
        aiRationale: 'Live file context',
        linkedEvidenceCount: 1,
        status: 'validated' as const,
        wordCount: 400,
      };

    // 2. Identify the active live file / evidence linked to this block or section
    let liveEv = this.evidence.find(
      (e) =>
        (targetBlock?.citationId && e.id === targetBlock.citationId) ||
        (targetBlock?.evidenceRef?.documentName &&
          e.documentName.toLowerCase() === targetBlock.evidenceRef.documentName.toLowerCase())
    );

    if (!liveEv) {
      const secTitleLower = targetSection.title.toLowerCase();
      if (params.sectionId === 'sec-5' || secTitleLower.includes('production') || secTitleLower.includes('stripping')) {
        liveEv = this.evidence.find((e) => e.documentName.includes('mining_data_chart'));
      } else if (params.sectionId === 'sec-2' || secTitleLower.includes('geological') || secTitleLower.includes('drillhole') || secTitleLower.includes('stratigraphy')) {
        liveEv = this.evidence.find((e) => e.documentName.includes('borehole'));
      } else if (params.sectionId === 'sec-3' || secTitleLower.includes('quality') || secTitleLower.includes('laboratory') || secTitleLower.includes('assay')) {
        liveEv = this.evidence.find((e) => e.documentName.includes('laboratory'));
      } else if (params.sectionId === 'sec-4' || secTitleLower.includes('geotechnical') || secTitleLower.includes('slope') || secTitleLower.includes('observation')) {
        liveEv = this.evidence.find((e) => e.documentName.includes('field_observation'));
      } else if (params.sectionId === 'sec-1' || secTitleLower.includes('executive') || secTitleLower.includes('overview') || secTitleLower.includes('concession')) {
        liveEv = this.evidence.find((e) => e.documentName.includes('README'));
      }
    }

    // Default fallback to first live evidence or data source if available
    const liveDocName =
      liveEv?.documentName ||
      targetBlock?.evidenceRef?.documentName ||
      this.dataSources[0]?.filename ||
      'mining_data_chart.png';

    const liveLocation =
      liveEv?.sourceLocation ||
      targetBlock?.evidenceRef?.location ||
      'Figure 1.1: Production Trend & Stripping Ratio Telemetry';

    const liveSheetOrPage =
      liveEv?.sheetName ||
      (liveEv?.page ? `Page ${liveEv.page}` : liveEv?.spreadsheetName || 'Telemetry Feed');

    const liveSnippet =
      liveEv?.relevantText ||
      targetBlock?.content ||
      'Monthly excavation telemetry indicates certified Run-of-Mine coal production of 245,000 MT/month with overburden removal of 680,000 m3/month.';

    // 3. Grounded analysis based on the live source file & prompt instruction
    const query = (params.instruction || '').toLowerCase();
    const isTone = query.includes('tone') || query.includes('formal') || query.includes('improve');
    const isSummarize = query.includes('summarize') || query.includes('brief') || query.includes('executive');
    const isVerify = query.includes('verify') || query.includes('figure') || query.includes('numerical') || query.includes('wrong') || query.includes('ledger');

    let originalVal = 'Drafted Assertion';
    let verifiedVal = 'Verified Ledger Assertion';
    let diffAnalysis = `Calibrated against live index of '${liveDocName}'.`;
    let proposedRevision = targetBlock?.content || '';

    if (liveDocName.includes('mining_data_chart') || params.sectionId === 'sec-5') {
      originalVal = '245,000 MT/month (Target: 240,000 MT)';
      verifiedVal = '245,000 MT/month • Overburden: 680,000 m³/mo • SR: 2.78 m³/MT';
      diffAnalysis = `Cross-checked against live production telemetry in '${liveDocName}'. Reconciled ROM extraction at 245,000 MT/month (+2.1% above statutory target) and calibrated Stripping Ratio at 2.78 m³/MT with 0 compliance non-conformances.`;

      if (isTone) {
        proposedRevision =
          'Reconciled pithead extraction telemetry confirms certified Run-of-Mine (ROM) coal production of 245,000 MT/month against the statutory baseline of 240,000 MT (+2.1%). Concurrent overburden removal of 680,000 m³/month achieves an operational Stripping Ratio of 2.78 m³/MT, demonstrating high-efficiency dragline deployment and optimal heavy earthmoving machinery (HEMM) fleet availability.';
      } else if (isSummarize) {
        proposedRevision =
          'Executive Summary: Certified ROM coal production achieved 245,000 MT/month (+2.1% above target) with an operational stripping ratio of 2.78 m³/MT supported by 680,000 m³/month overburden removal.';
      } else {
        proposedRevision =
          'Audited extraction telemetry verifies Run-of-Mine coal production at 245,000 MT/month against the statutory target of 240,000 MT (+2.1%). Total overburden removal reached 680,000 m³/month yielding an operational Stripping Ratio of 2.78 m³/MT, strictly conforming with electronic dispatch weighbridge telemetry [mining_data_chart.png #Figure 1.1].';
      }
    } else if (liveDocName.includes('borehole') || params.sectionId === 'sec-2') {
      originalVal = 'Seam II: 9.6m Clean Thickness (Depth 45.2m – 54.8m)';
      verifiedVal = 'Seam II: 9.6m • Ash: 18.4% • GCV: 6,120 kcal/kg (Grade G4)';
      diffAnalysis = `Cross-checked against borehole drill assay logs in '${liveDocName}'. Intercept borehole BH-2026-04 verified with 18.4% ash content and Grade G4 metallurgical rating. Total proved reserve confirmed at 42.6 MT.`;

      if (isTone) {
        proposedRevision =
          'Exploration diamond core drilling officially substantiates persistent lateral continuity of the target coal sequences. Intercept logs for borehole BH-2026-04 confirm clean metallurgical Seam II between 45.2m and 54.8m with a composite thickness of 9.6m, exhibiting low dirt-band contamination (18.4% ash) and high gross calorific value of 6,120 kcal/kg.';
      } else if (isSummarize) {
        proposedRevision =
          'Core drillhole BH-2026-04 confirmed prime Seam II at 45.2–54.8m with 9.6m net thickness, 18.4% ash, and 6,120 kcal/kg GCV (Grade G4).';
      } else {
        proposedRevision =
          'Exploration diamond core drilling confirmed persistent lateral continuity of three primary coal seams across the tenement. Borehole BH-2026-04 intercepted prime metallurgical Seam II at depth 45.2m to 54.8m with a clean net thickness of 9.6m, displaying low dirt-band inclusion and favorable hanging-wall sandstone competence.';
      }
    } else if (liveDocName.includes('laboratory') || params.sectionId === 'sec-3') {
      originalVal = 'Moisture 6.8% • Ash 24.2% • GCV 5,420 kcal/kg';
      verifiedVal = 'Grade G8 Certified (IS 1350 compliant) • Sulfur: 0.48%';
      diffAnalysis = `Calibrated against certified NABL laboratory assay certificate '${liveDocName}'. Parameters strictly comply with IS 1350 Part I standards with low sulfur (0.48%) and Grade G8 thermal band.`;

      if (isTone) {
        proposedRevision =
          'Certified proximate and ultimate characterization by the NABL-accredited Central Testing Laboratory corroborates consistent medium-rank bituminous coal with low total sulfur (0.48%) and an ash fusion temperature of 1,380°C. Total moisture of 6.8% and air-dried ash content of 24.2% ensure consistent Grade G8 thermal delivery.';
      } else if (isSummarize) {
        proposedRevision =
          'NABL laboratory analysis confirms Grade G8 bituminous coal: 6.8% moisture, 24.2% ash, 5,420 kcal/kg GCV, and 0.48% total sulfur.';
      } else {
        proposedRevision =
          'Certified proximate and ultimate analysis of drill core composites by the NABL-accredited Central Testing Laboratory indicates consistent medium-rank bituminous coal with low total sulfur (0.48%) and high ash fusion temperature (1,380°C). Total Moisture is 6.8% with Gross Calorific Value of 5,420 kcal/kg.';
      }
    } else if (liveDocName.includes('field_observation') || params.sectionId === 'sec-4') {
      originalVal = 'Highwall Factor of Safety: 1.42 (Dry State)';
      verifiedVal = 'FoS: 1.42 (Dry) / 1.31 (Saturated) • RMR: 68';
      diffAnalysis = `Cross-checked with field geotechnical inspection notes in '${liveDocName}'. Bench #4 sandstone strata confirmed competent with Rock Mass Rating of 68, safely exceeding statutory DGMS minimum threshold of 1.30.`;

      if (isTone) {
        proposedRevision =
          'Geotechnical kinematic stability analysis across open-cast highwall bench #4 establishes competent sandstone overburden characterized by a Rock Mass Rating (RMR) of 68 (Good Rock). Evaluated Factor of Safety of 1.42 in the dry state and 1.31 under maximum groundwater saturation fully complies with DGMS Circular 02 guidelines.';
      } else if (isSummarize) {
        proposedRevision =
          'Bench #4 highwall inspection confirms stable competent rock (RMR 68) with a dry Factor of Safety of 1.42 (saturated 1.31), exceeding DGMS standards.';
      } else {
        proposedRevision =
          'Geotechnical survey of open-cast highwall bench #4 reveals competent sandstone overburden with Rock Mass Rating (RMR) score of 68 (Good Rock). Calculated Factor of Safety (FoS) is 1.42 under dry condition and 1.31 under hydrostatic saturation, fully complying with DGMS Circular 02 slope safety guidelines.';
      }
    } else if (liveDocName.includes('README') || params.sectionId === 'sec-1') {
      originalVal = 'Block ML-492 Concession Area: 24.8 sq km';
      verifiedVal = 'UTM Zone 45N • Proved Reserve: 42.6 MT • Grade G8';
      diffAnalysis = `Verified against statutory concession metadata registry in '${liveDocName}'. Concession boundaries and UTM Zone 45N geographic projection validated under CIL/CMPDI exploration standard.`;

      if (isTone) {
        proposedRevision =
          'This statutory technical synthesis integrates exploration core drilling, laboratory proximate assays, geotechnical field observations, and operational telemetry for Mining Lease Block ML-492 (24.8 sq km). Benchmark coordinates are validated in UTM Zone 45N under official CIL/CMPDI protocols, confirming 42.6 MT proved mineable reserves.';
      } else if (isSummarize) {
        proposedRevision =
          'Block ML-492 executive summary: 24.8 sq km concession in UTM Zone 45N with 42.6 MT proved mineable reserves, Grade G8 coal, and DGMS compliant 1.42 slope stability factor.';
      } else {
        proposedRevision =
          'This technical synthesis compiles multi-source exploration drilling, laboratory proximate assays, geotechnical field observations, and production telemetry for Mining Lease Block ML-492 (24.8 sq km). All survey benchmarks are referenced in UTM Zone 45N under statutory CIL/CMPDI exploration protocols.';
      }
    } else {
      // Generic live file ingested into workspace
      originalVal = targetBlock?.content?.slice(0, 45) || 'Drafted Metric';
      verifiedVal = `Verified Assertion from ${liveDocName}`;
      diffAnalysis = `Cross-referenced against local indexed file '${liveDocName}' (${liveLocation}). Provenance hash confirmed under local zero-cloud airgap policy.`;
      proposedRevision = targetBlock?.content
        ? `${targetBlock.content} [Verified against ${liveDocName}]`
        : liveSnippet;
    }

    // 4. Specific Natural Language Instruction Parsing & Execution:
    // Handles commands like:
    // - "change the word audited to audit" / "change audited to audit" / "replace X with Y" / "swap X for Y"
    // - "remove X" / "delete word X"
    // - "change 240,000 to 250,000"
    const rawInstruction = (params.instruction || '').trim();

    const replacePattern =
      /(?:change|replace|substitute|swap)\s+(?:the\s+word\s+|the\s+term\s+|the\s+text\s+)?["']?([^"'\s]+)["']?\s+(?:to|with|for|by)\s+["']?([^"'\s]+)["']?/i;
    const replaceMatch = rawInstruction.match(replacePattern);

    if (replaceMatch) {
      const fromWord = replaceMatch[1].replace(/[.,;:!?]/g, '').trim();
      const toWord = replaceMatch[2].replace(/[.,;:!?]/g, '').trim();

      const baseText = targetBlock?.content || proposedRevision;
      const wordRegex = new RegExp(`\\b${fromWord}\\b`, 'gi');

      if (wordRegex.test(baseText) || wordRegex.test(proposedRevision)) {
        const sourceText = wordRegex.test(baseText) ? baseText : proposedRevision;
        proposedRevision = sourceText.replace(wordRegex, (match) => {
          if (match[0] === match[0].toUpperCase() && match.slice(1) === match.slice(1).toLowerCase()) {
            return toWord.charAt(0).toUpperCase() + toWord.slice(1);
          }
          if (match === match.toUpperCase()) {
            return toWord.toUpperCase();
          }
          return toWord.toLowerCase();
        });
        originalVal = fromWord;
        verifiedVal = toWord;
        diffAnalysis = `Direct editorial command executed: Replaced '${fromWord}' with '${toWord}' in active live text block.`;
      } else {
        const subRegex = new RegExp(fromWord, 'gi');
        if (subRegex.test(baseText) || subRegex.test(proposedRevision)) {
          const sourceText = subRegex.test(baseText) ? baseText : proposedRevision;
          proposedRevision = sourceText.replace(subRegex, (match) => {
            if (match[0] === match[0].toUpperCase()) {
              return toWord.charAt(0).toUpperCase() + toWord.slice(1);
            }
            return toWord;
          });
          originalVal = fromWord;
          verifiedVal = toWord;
          diffAnalysis = `Direct editorial command executed: Replaced '${fromWord}' with '${toWord}' in active live text block.`;
        }
      }
    } else {
      const removePattern = /(?:remove|delete|omit)\s+(?:the\s+word\s+|the\s+term\s+)?["']?([^"'\s]+)["']?/i;
      const removeMatch = rawInstruction.match(removePattern);
      if (removeMatch) {
        const wordToRemove = removeMatch[1].trim();
        const baseText = targetBlock?.content || proposedRevision;
        const removeRegex = new RegExp(`\\b${wordToRemove}\\b\\s*`, 'gi');
        if (removeRegex.test(baseText) || removeRegex.test(proposedRevision)) {
          const sourceText = removeRegex.test(baseText) ? baseText : proposedRevision;
          proposedRevision = sourceText.replace(removeRegex, '');
          originalVal = `Contains '${wordToRemove}'`;
          verifiedVal = `Removed '${wordToRemove}'`;
          diffAnalysis = `Direct editorial command executed: Removed '${wordToRemove}' from active live text block.`;
        }
      }
    }

    return {
      id: `prop-${Date.now().toString().slice(-4)}`,
      targetBlockId: targetBlock?.id || params.selectedBlockId || 'blk-502',
      contextSection: targetSection.title,
      userQuery: params.instruction,
      agentStatus: 'proposal_ready',
      searchedEvidence: {
        sourceFile: liveDocName,
        sheetOrPage: liveSheetOrPage,
        rangeOrSection: liveLocation,
        rawSnippet: liveSnippet,
      },
      originalValue: originalVal,
      verifiedValue: verifiedVal,
      differenceAnalysis: diffAnalysis,
      proposedText: proposedRevision,
      confidenceScore: 99.4,
    };
  }

  // ==========================================
  // Asset Manager
  // ==========================================
  async getAssets(): Promise<AssetRecord[]> {
    return [...this.assets];
  }

  // ==========================================
  // Validation Center
  // ==========================================
  async getValidationIssues(): Promise<ValidationIssueItem[]> {
    return [...this.validationIssues];
  }

  // ==========================================
  // Security & Audit
  // ==========================================
  async getAuditLogs(): Promise<AuditLogItem[]> {
    return [...this.auditLogs];
  }

  private logAudit(entry: Omit<AuditLogItem, 'id' | 'timestamp' | 'ipOrOrigin' | 'verificationHash'>) {
    const newLog: AuditLogItem = {
      id: `aud-${Date.now().toString().slice(-4)}`,
      timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19),
      ipOrOrigin: '127.0.0.1 (Tauri Local Core)',
      verificationHash: Array.from({ length: 40 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
      ...entry,
    };
    this.auditLogs.unshift(newLog);
  }
}

export const desktopService = new LocalDesktopService();
