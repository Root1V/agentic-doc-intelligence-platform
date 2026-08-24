// Hand-written interfaces mirroring the FastAPI/Pydantic response models —
// see the plan: ~10 endpoints is small enough that hand-sync beats an
// OpenAPI-codegen pipeline for now (revisit only if the surface grows).

export interface ToolCallRecord {
  turn: number
  tool_name: string
  arguments: Record<string, unknown>
  result_summary: string
  reasoning: string | null
}

/** The citation envelope wrapping every leaf value in a document's
 * `extraction` payload — page/bbox/source_text are what make this
 * platform's extraction "grounded" rather than a bare value. */
export interface Extracted<T> {
  value: T
  page: number | null
  bbox: [number, number, number, number] | null
  confidence: number
  source_text: string | null
  region_id: number | null
  reasoning_trace: ToolCallRecord[] | null
}

export interface DocumentSummary {
  id: string
  batch_id: string
  status: string
  document_type: string | null
  classification_confidence: number | null
  needs_review: boolean
  original_filename: string
  parent_document_id: string | null
  page_start: number | null
  page_end: number | null
}

export interface BatchStatusResponse {
  id: string
  status: string
  documents: DocumentSummary[]
}

export interface BatchCreateResponse {
  batch_id: string
}

export interface ValidationIssue {
  rule_id: string
  category: string
  field_path: string | null
  severity: 'info' | 'warning' | 'error'
  message: string
  confidence: number
  confidence_method: string
  explanation: string
}

export interface DocumentDetailResponse {
  id: string
  status: string
  document_type: string | null
  classification_confidence: number | null
  needs_review: boolean
  original_filename: string
  parent_document_id: string | null
  page_start: number | null
  page_end: number | null
  extraction: Record<string, unknown> | null
  validation_issues: ValidationIssue[]
}

export interface DocumentListResponse {
  total: number
  documents: DocumentSummary[]
}

export interface ReviewItem {
  id: string
  document_id: string
  field_path: string
  current_value: { value: unknown }
  confidence: number
  reason: 'low_confidence' | 'validation_issue'
  status: string
}

export interface ReviewCorrectionRequest {
  corrected_value: unknown
  model_version?: string | null
  prompt_version?: string | null
}

export interface ReviewCorrectionResponse {
  review_item_id: string
  status: string
}

export interface SuggestedField {
  name: string
  field_type: string
  description: string
  required: boolean
}

export interface TypeSuggestion {
  id: string
  document_id: string
  batch_id: string
  suggested_type_name: string
  suggested_display_name: string
  rationale: string
  fields: SuggestedField[]
  status: string
  reviewer_identity: string | null
}

export interface DocumentTypeFieldInfo {
  name: string
  field_type: string
  description: string | null
  required: boolean
}

export interface DocumentTypeInfo {
  name: string
  description: string
  fields: DocumentTypeFieldInfo[]
}

export interface PendingTypeInfo {
  suggestion_id: string
  suggested_type_name: string
  suggested_display_name: string
  rationale: string
  fields: Record<string, unknown>[]
}

export interface DocumentTypeCatalogResponse {
  registered: DocumentTypeInfo[]
  pending: PendingTypeInfo[]
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user_name: string
}
