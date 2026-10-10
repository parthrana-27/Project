export interface CompileRequest {
  prompt: string;
  language: string;
  max_repairs?: number;
}

export interface CompileResponse {
  job_id: string;
  status: string;
  stream_url: string;
}

export interface HistoryItem {
  id: string;
  created_at: string;
  prompt: string;
  language: string;
  status: string;
  success: boolean;
  total_attempts: number;
}

export interface HistoryDetail {
  id: string;
  created_at: string;
  prompt: string;
  language: string;
  status: string;
  success: boolean;
  intent?: any;
  ir?: any;
  generated_code?: string;
  total_attempts: number;
  test_summary?: any;
  attempt_history?: any[];
  error_message?: string;
}

const BASE_URL = '';

export async function startCompile(req: CompileRequest): Promise<CompileResponse> {
  const res = await fetch(`${BASE_URL}/api/compile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to start compilation' }));
    throw new Error(err.detail || 'Compilation request failed');
  }
  return res.json();
}

export async function fetchHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${BASE_URL}/api/history`);
  if (!res.ok) throw new Error('Failed to fetch history');
  return res.json();
}

export async function fetchHistoryDetail(id: string): Promise<HistoryDetail> {
  const res = await fetch(`${BASE_URL}/api/history/${id}`);
  if (!res.ok) throw new Error('Failed to fetch history item');
  return res.json();
}

export async function deleteHistoryItem(id: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/history/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete history item');
}
