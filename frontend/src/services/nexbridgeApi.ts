import type {
  TransformResponse,
  ClassifyResponse,
  ProposeMappingsRequest,
  ProposeMappingsResponse,
} from '@/types/nexbridge.types';

const BASE_URL = 'http://localhost:8000';

export const nexbridgeApi = {

  transform: async (
    payload: string,
    sourceFormat: string,
    targetFormat: string,
    targetSchema: Record<string, string>,
    rootElement?: string
  ): Promise<TransformResponse> => {
    const res = await fetch(`${BASE_URL}/transform`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        payload,
        source_format: sourceFormat,
        target_format: targetFormat,
        target_schema: targetSchema,
        root_element: rootElement ?? 'payload',
      }),
    });
    if (!res.ok) throw new Error(`Transform failed: ${res.status}`);
    return res.json();
  },

  classify: async (fieldNames: string[]): Promise<ClassifyResponse> => {
    const res = await fetch(`${BASE_URL}/classify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ field_names: fieldNames }),
    });
    if (!res.ok) throw new Error(`Classify failed: ${res.status}`);
    return res.json();
  },

  getRegistry: async () => {
    const res = await fetch(`${BASE_URL}/registry`);
    if (!res.ok) throw new Error(`Registry failed: ${res.status}`);
    return res.json();
  },

  healthCheck: async () => {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
    return res.json();
  },

  proposeMappings: async (
    request: ProposeMappingsRequest
  ): Promise<ProposeMappingsResponse> => {
    const res = await fetch(`${BASE_URL}/registry/propose-mappings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? `Propose mappings failed: ${res.status}`);
    }
    return res.json();
  },
};
