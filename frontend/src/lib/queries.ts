// TanStack Query hooks, one per backend endpoint — cache/loading/error
// states and the 2s batch-status polling (same cadence
// scripts/run_fixture_batch.py already validates against the live stack)
// come from the library instead of hand-rolled state machines.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import type {
  BatchCreateResponse,
  BatchStatusResponse,
  DocumentDetailResponse,
  DocumentListResponse,
  DocumentTypeCatalogResponse,
  LoginRequest,
  LoginResponse,
  ReviewCorrectionRequest,
  ReviewCorrectionResponse,
  ReviewItem,
  TypeSuggestion,
} from '@/types/api'

const TERMINAL_BATCH_STATUSES = new Set(['completed'])

export function useLogin() {
  return useMutation({
    mutationFn: async (body: LoginRequest) => {
      const { data } = await apiClient.post<LoginResponse>('/auth/login', body)
      return data
    },
  })
}

export interface DocumentListFilters {
  status?: string
  document_type?: string
  needs_review?: boolean
  limit?: number
  offset?: number
}

export function useDocumentList(filters: DocumentListFilters = {}) {
  return useQuery({
    queryKey: ['documents', filters],
    queryFn: async () => {
      const { data } = await apiClient.get<DocumentListResponse>('/documents', { params: filters })
      return data
    },
  })
}

export function useBatch(batchId: string | undefined) {
  return useQuery({
    queryKey: ['batch', batchId],
    queryFn: async () => {
      const { data } = await apiClient.get<BatchStatusResponse>(`/batches/${batchId}`)
      return data
    },
    enabled: !!batchId,
    refetchInterval: (query) => (query.state.data?.status && TERMINAL_BATCH_STATUSES.has(query.state.data.status) ? false : 2000),
  })
}

export function useCreateBatch() {
  return useMutation({
    mutationFn: async ({ files, requestInputPayload }: { files: File[]; requestInputPayload?: Record<string, unknown> }) => {
      const form = new FormData()
      for (const file of files) form.append('files', file)
      if (requestInputPayload && Object.keys(requestInputPayload).length > 0) {
        form.append('request_input_payload', JSON.stringify(requestInputPayload))
      }
      const { data } = await apiClient.post<BatchCreateResponse>('/batches', form)
      return data
    },
  })
}

export function useDocument(documentId: string | undefined) {
  return useQuery({
    queryKey: ['document', documentId],
    queryFn: async () => {
      const { data } = await apiClient.get<DocumentDetailResponse>(`/documents/${documentId}`)
      return data
    },
    enabled: !!documentId,
  })
}

/** Fetches the original file's bytes as a Blob URL, respecting the JWT
 * header — a plain `<img src=...>`/react-pdf `file=url` can't attach auth
 * headers, so the bytes are fetched through axios instead. */
export function useDocumentFileUrl(documentId: string | undefined) {
  return useQuery({
    queryKey: ['document-file', documentId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/documents/${documentId}/file`, { responseType: 'blob' })
      return URL.createObjectURL(data as Blob)
    },
    enabled: !!documentId,
    staleTime: Infinity,
  })
}

export function useReviewQueue() {
  return useQuery({
    queryKey: ['review-queue'],
    queryFn: async () => {
      const { data } = await apiClient.get<ReviewItem[]>('/review')
      return data
    },
  })
}

export function useSubmitCorrection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ reviewItemId, body }: { reviewItemId: string; body: ReviewCorrectionRequest }) => {
      const { data } = await apiClient.post<ReviewCorrectionResponse>(`/review/${reviewItemId}`, body)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] })
    },
  })
}

export function useTypeSuggestions() {
  return useQuery({
    queryKey: ['type-suggestions'],
    queryFn: async () => {
      const { data } = await apiClient.get<TypeSuggestion[]>('/type-suggestions')
      return data
    },
  })
}

export function useResolveTypeSuggestion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ suggestionId, decision }: { suggestionId: string; decision: 'accept' | 'reject' }) => {
      const { data } = await apiClient.post<TypeSuggestion>(`/type-suggestions/${suggestionId}/${decision}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['type-suggestions'] })
      queryClient.invalidateQueries({ queryKey: ['document-types'] })
    },
  })
}

export function useDocumentTypeCatalog() {
  return useQuery({
    queryKey: ['document-types'],
    queryFn: async () => {
      const { data } = await apiClient.get<DocumentTypeCatalogResponse>('/document-types')
      return data
    },
  })
}
