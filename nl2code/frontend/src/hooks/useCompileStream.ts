import { useState, useCallback, useRef } from 'react';
import { startCompile } from '../lib/api';

export type StageName = 'intent' | 'ir' | 'codegen' | 'validate' | 'sandbox' | 'repair' | 'done';
export type StageStatus = 'idle' | 'running' | 'ok' | 'failed';

export interface StageInfo {
  name: StageName;
  label: string;
  status: StageStatus;
  message?: string;
}

const INITIAL_STAGES: Record<StageName, StageStatus> = {
  intent: 'idle',
  ir: 'idle',
  codegen: 'idle',
  validate: 'idle',
  sandbox: 'idle',
  repair: 'idle',
  done: 'idle',
};

export function useCompileStream() {
  const [isCompiling, setIsCompiling] = useState(false);
  const [stages, setStages] = useState<Record<StageName, StageStatus>>(INITIAL_STAGES);
  const [stageMessages, setStageMessages] = useState<Record<string, string>>({});
  const [intent, setIntent] = useState<any>(null);
  const [ir, setIr] = useState<any>(null);
  const [code, setCode] = useState<string>('');
  const [testSummary, setTestSummary] = useState<any>(null);
  const [attemptHistory, setAttemptHistory] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);

  const resetState = () => {
    setStages(INITIAL_STAGES);
    setStageMessages({});
    setIntent(null);
    setIr(null);
    setCode('');
    setTestSummary(null);
    setAttemptHistory([]);
    setError(null);
  };

  const loadPastRecord = (record: any) => {
    resetState();
    if (record.intent) setIntent(record.intent);
    if (record.ir) setIr(record.ir);
    if (record.generated_code) setCode(record.generated_code);
    if (record.test_summary) setTestSummary(record.test_summary);
    if (record.attempt_history) setAttemptHistory(record.attempt_history);
    
    // Set all stages to OK if completed
    const st = { ...INITIAL_STAGES };
    (Object.keys(st) as StageName[]).forEach((k) => {
      st[k] = record.success ? 'ok' : 'failed';
    });
    setStages(st);
  };

  const compile = useCallback(async (prompt: string, language: string, maxRepairs = 3) => {
    resetState();
    setIsCompiling(true);

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const resp = await startCompile({ prompt, language, max_repairs: maxRepairs });
      const es = new EventSource(resp.stream_url);
      eventSourceRef.current = es;

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const { stage, status, payload } = data;

          if (stage === 'error') {
            setError(payload?.error || 'Unknown compilation failure');
            setIsCompiling(false);
            es.close();
            return;
          }

          setStages((prev) => ({
            ...prev,
            [stage]: status,
          }));

          if (payload?.message) {
            setStageMessages((prev) => ({ ...prev, [stage]: payload.message }));
          }

          if (stage === 'intent' && payload?.intent) {
            setIntent(payload.intent);
          } else if (stage === 'ir' && payload?.ir) {
            setIr(payload.ir);
          } else if (stage === 'codegen' && payload?.code) {
            setCode(payload.code);
          } else if (stage === 'sandbox' && payload?.test_summary) {
            setTestSummary(payload.test_summary);
          } else if (stage === 'repair' && payload?.attempt) {
            setStageMessages((prev) => ({
              ...prev,
              repair: `Repair iteration ${payload.attempt}...`,
            }));
          } else if (stage === 'done') {
            if (payload?.final_code) setCode(payload.final_code);
            if (payload?.history) setAttemptHistory(payload.history);
            setIsCompiling(false);
            es.close();
          }
        } catch (err) {
          console.error('Error handling SSE message:', err);
        }
      };

      es.onerror = () => {
        setIsCompiling(false);
        es.close();
      };
    } catch (err: any) {
      setError(err.message || 'Failed to initialize compiler session');
      setIsCompiling(false);
    }
  }, []);

  return {
    isCompiling,
    stages,
    stageMessages,
    intent,
    ir,
    code,
    testSummary,
    attemptHistory,
    error,
    compile,
    loadPastRecord,
    setCode,
  };
}
