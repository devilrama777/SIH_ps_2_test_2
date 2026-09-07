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
} from '../types';

export const INITIAL_SECURITY_POSTURE: SystemSecurityPosture = {
  localAiStatus: 'Connected (llama.cpp 127.0.0.1:8484)',
  externalAiStatus: 'Strictly Disabled (Airgapped Firewall Active)',
  networkAccess: 'Restricted (Loopback Only)',
  auditLogging: 'Enabled (Tamper-Evident SHA-256 Ledger)',
  credentialStorage: 'Local OS Keyring (Zero Cloud Tokens)',
  gpuStatus: 'NVIDIA RTX 4090 (24GB VRAM Allocated: 14.8GB)',
  encryptionStatus: 'AES-256 at-rest (Local Workspace Partition)',
};

export const INITIAL_HEALTH_COMPONENTS: SystemHealthComponent[] = [
  {
    id: 'ocr',
    name: 'OCR Engine',
    engine: 'PaddleOCR v2.8 + Tesseract 5.4 (CUDA 12.4)',
    status: 'healthy',
    detail: 'Dual-pass multilingual OCR running on local GPU tensor cores',
    metrics: '99.4% char accuracy • 38 ms/page',
    latency: '38ms',
    device: 'CUDA:0 (RTX 4090)',
  },
  {
    id: 'parser',
    name: 'Document Parser',
    engine: 'PyMuPDF + Unstructured-Local (C++ bindings)',
    status: 'healthy',
    detail: 'Extracts layout hierarchy, tables (Lattice/Stream), and image vectors',
    metrics: 'Ready for document processing',
    latency: '14ms/doc',
    device: 'Host CPU (16 threads)',
  },
  {
    id: 'search',
    name: 'Search Index',
    engine: 'Qdrant Embedded + SQLite BM25 Hybrid',
    status: 'healthy',
    detail: 'Dense 1024-dim BGE-M3 vectors + sparse lexical BM25 index on NVMe',
    metrics: 'Ready for document index',
    latency: '4.2ms query',
    device: 'Local NVMe SSD',
  },
  {
    id: 'model',
    name: 'Local AI Model',
    engine: 'Llama-3.3-70B-Instruct-Q4_K_M (llama.cpp server)',
    status: 'healthy',
    detail: 'Airgapped local LLM with 32,768 token context window & zero internet egress',
    metrics: 'Local inference active',
    latency: '22ms TTFT',
    device: 'NVIDIA GPU (CUDA)',
  },
  {
    id: 'renderer',
    name: 'PDF Renderer',
    engine: 'Typst CLI 0.11 + Weasyprint Enterprise',
    status: 'healthy',
    detail: 'High-precision deterministic corporate layout engine with vector CMYK support',
    metrics: 'Pre-flight check active • PDF/A-2b compliant',
    latency: '1.4s / 60 pages',
    device: 'Local Subprocess',
  },
];

export const INITIAL_REPORTS: ReportItem[] = [];

export const INITIAL_DATA_SOURCES: DataSourceItem[] = [];

export const INITIAL_PROCESSING_JOBS: ProcessingJobItem[] = [];

export const INITIAL_EVIDENCE_ITEMS: EvidenceItem[] = [];

export const INITIAL_REPORT_SECTIONS: ReportSectionNode[] = [];

export const INITIAL_EDITOR_BLOCKS: EditorBlock[] = [];

export const INITIAL_ASSET_RECORDS: AssetRecord[] = [];

export const INITIAL_VALIDATION_ISSUES: ValidationIssueItem[] = [];

export const INITIAL_AUDIT_LOGS: AuditLogItem[] = [];
