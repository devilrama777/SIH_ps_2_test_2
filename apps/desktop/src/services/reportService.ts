import {
  DataSourceItem,
  ProcessingJobItem,
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
    const newJob: ProcessingJobItem = {
      id: `job-${Date.now().toString().slice(-4)}`,
      jobName: params.jobName,
      type: params.type,
      progress: 15,
      currentStage: 'Extracting',
      startedAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
      elapsedTime: '0m 08s',
      status: 'running',
      errorsCount: 0,
      warningsCount: 0,
      filesProcessed: 0,
      totalFiles: params.totalFiles,
      logs: [
        `[${new Date().toLocaleTimeString()}] Local worker dispatched task '${params.jobName}' to background thread`,
        `[${new Date().toLocaleTimeString()}] Checking local GPU tensor core availability... CUDA context acquired`,
      ],
    };
    this.jobs.unshift(newJob);
    return newJob;
  }

  async updateJobStatus(id: string, status: 'running' | 'paused' | 'completed' | 'failed'): Promise<boolean> {
    const job = this.jobs.find((j) => j.id === id);
    if (!job) return false;
    job.status = status;
    if (status === 'paused') {
      job.logs.push(`[${new Date().toLocaleTimeString()}] Job execution suspended by user.`);
    } else if (status === 'running') {
      job.logs.push(`[${new Date().toLocaleTimeString()}] Job execution resumed.`);
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
        details: `Updated numerical assertion from '${proposal.originalValue}' to '${proposal.verifiedValue}' based on verified ledger evidence.`,
      });

      // Also resolve corresponding validation issue if it exists
      const issue = this.validationIssues.find((v) => v.targetBlockId === block.id);
      if (issue) {
        issue.severity = 'pass';
        issue.title = 'Gross Turnover reconciled with audited ledger';
        issue.description = `Verified against ${proposal.searchedEvidence?.sourceFile} (${proposal.searchedEvidence?.sheetOrPage}).`;
      }
    }
  }

  // ==========================================
  // Contextual AI Agent Inquiry (Simulation of local model)
  // ==========================================
  async triggerContextualAIAgent(params: {
    reportId: string;
    sectionId: string;
    selectedBlockId: string;
    instruction: string;
  }): Promise<AIEditProposal> {
    // Exact simulation of the required user scenario:
    // USER: "The revenue figure here looks wrong. Verify it."
    // AGENT: Searching evidence... Found Financial_Report.xlsx, Sheet: March, Range: G27:G31...
    return {
      id: `prop-${Date.now().toString().slice(-4)}`,
      targetBlockId: params.selectedBlockId || 'blk-004',
      contextSection: '4.1 Turnover, FSA Realizations & E-Auction Premiums',
      userQuery: params.instruction,
      agentStatus: 'proposal_ready',
      searchedEvidence: {
        sourceFile: 'CIL_FY26_Q3_Consolidated_Financial_Ledger.xlsx',
        sheetOrPage: 'March_Consolidated_Summary',
        rangeOrSection: 'G27:G31',
        rawSnippet:
          'Gross Operational Turnover Q3 FY26: ₹4,912.80 Cr (Reflects finalized pithead realized price of ₹1,642.50/ton across 29.91 MT of prime coking & non-coking coal dispatched). Prior provisional estimate was ₹4,820.50 Cr before reconciliation.',
      },
      originalValue: '₹4,820.50 Cr',
      verifiedValue: '₹4,912.80 Cr',
      differenceAnalysis: '+₹92.30 Cr (+1.9%) discrepancy identified. The drafted paragraph utilized an unadjusted provisional figure instead of the reconciled audited ledger.',
      proposedText:
        'Gross operational turnover for the quarter stands at ₹4,912.80 Cr across all active mining commands, reconciled with finalized pithead realization rates. Average net realization per metric tonne stood at ₹1,642.50, driven by higher calorific grade off-takes in Central Coalfields and Bharat Coking Coal limited divisions.',
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
