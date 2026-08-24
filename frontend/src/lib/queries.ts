// TanStack Query hooks, one per backend endpoint — cache/loading/error
// states come from the library instead of hand-rolled state machines.
import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { getToken } from '@/lib/auth'
import type {
  AppUser,
  AuditLogResponse,
  BatchCreateResponse,
  BatchStatusResponse,
  CreateUserRequest,
  DocumentDetailResponse,
  DocumentListResponse,
  DocumentTypeCatalogResponse,
  LoginRequest,
  LoginResponse,
  ReviewCorrectionRequest,
  ReviewCorrectionResponse,
  ReviewItem,
  TypeSuggestion,
  UpdateTypeSuggestionRequest,
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
  /** Matches against the filename AND the extracted field values (see
   * DocumentRepository._filtered) — one box searches both. */
  q?: string
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
    // useBatchLiveUpdates (SSE) is the primary way this updates while a
    // batch is processing — this interval is only a safety net in case the
    // stream dies silently (e.g. a proxy buffering/dropping it), so it's
    // deliberately much slower than the old 2s poll.
    refetchInterval: (query) => (query.state.data?.status && TERMINAL_BATCH_STATUSES.has(query.state.data.status) ? false : 15000),
  })
}

/** Opens a Server-Sent Events connection to GET /batches/{id}/stream and
 * pushes every update straight into the ['batch', batchId] query cache —
 * every existing consumer of useBatch just re-renders, no separate state to
 * thread through. Uses `fetch` with a manual Authorization header rather
 * than the browser's native EventSource, which can't set custom headers
 * (see the backend route's docstring for why the JWT isn't passed as a
 * query param instead). No auto-reconnect loop: the backend generator ends
 * the stream on its own once the batch reaches a terminal status, and
 * useBatch's slow fallback poll above covers the rare case of the
 * connection dying for another reason. */
export function useBatchLiveUpdates(batchId: string | undefined) {
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!batchId) return
    const controller = new AbortController()

    async function connect() {
      const token = getToken()
      let response: Response
      try {
        response = await fetch(`/api/batches/${batchId}/stream`, {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          signal: controller.signal,
        })
      } catch {
        return
      }
      const reader = response.body?.getReader()
      if (!reader) return
      const decoder = new TextDecoder()
      let buffer = ''
      try {
        while (true) {
          const { value, done } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const frames = buffer.split('\n\n')
          buffer = frames.pop() ?? ''
          for (const frame of frames) {
            const dataLine = frame.split('\n').find((line) => line.startsWith('data: '))
            if (!dataLine) continue
            const payload = JSON.parse(dataLine.slice('data: '.length)) as BatchStatusResponse
            queryClient.setQueryData(['batch', batchId], payload)
          }
        }
      } catch {
        // Connection dropped mid-stream — the slow fallback poll on
        // useBatch takes over rather than reconnecting here.
      }
    }

    connect()
    return () => controller.abort()
  }, [batchId, queryClient])
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

export function useUpdateTypeSuggestion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ suggestionId, body }: { suggestionId: string; body: UpdateTypeSuggestionRequest }) => {
      const { data } = await apiClient.patch<TypeSuggestion>(`/type-suggestions/${suggestionId}`, body)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['type-suggestions'] })
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

export function useAuditLog(params: { limit?: number; offset?: number } = {}) {
  return useQuery({
    queryKey: ['audit-log', params],
    queryFn: async () => {
      const { data } = await apiClient.get<AuditLogResponse>('/audit', { params })
      return data
    },
  })
}

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const { data } = await apiClient.get<AppUser[]>('/users')
      return data
    },
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: CreateUserRequest) => {
      const { data } = await apiClient.post<AppUser>('/users', body)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
