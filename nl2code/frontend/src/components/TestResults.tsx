import React from 'react';
import { CheckCircle, XCircle, Clock, ShieldCheck, Bug, History } from 'lucide-react';

interface TestResultsProps {
  testSummary: any;
  attemptHistory?: any[];
}

export const TestResults: React.FC<TestResultsProps> = ({ testSummary, attemptHistory = [] }) => {
  if (!testSummary && attemptHistory.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col items-center justify-center min-h-[160px] text-center text-slate-500">
        <ShieldCheck className="w-8 h-8 mb-2 opacity-40" />
        <span className="text-xs font-mono">No test results available.</span>
        <span className="text-[11px] text-slate-600 mt-1">Tests run automatically inside the sandbox.</span>
      </div>
    );
  }

  const passedTests = testSummary?.passed_tests || 0;
  const totalTests = testSummary?.total_tests || 0;
  const failedTests = testSummary?.failed_tests || 0;
  const execTime = testSummary?.execution_time_ms || 0;
  const allPassed = testSummary?.passed;
  const testResults = testSummary?.test_results || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col">
      {/* Header Summary */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          {allPassed ? (
            <CheckCircle className="w-5 h-5 text-emerald-400" />
          ) : (
            <XCircle className="w-5 h-5 text-rose-400" />
          )}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
              Sandbox Test Suite Verification
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">
              {allPassed ? 'All unit tests passed successfully' : 'One or more unit tests failed'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-mono bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
            <Clock className="w-3.5 h-3.5 text-sky-400" />
            <span className="text-slate-300">{execTime} ms</span>
          </div>
          <div
            className={`text-xs font-mono font-semibold px-2.5 py-1 rounded-lg border ${
              allPassed
                ? 'bg-emerald-950/70 border-emerald-800/80 text-emerald-300'
                : 'bg-rose-950/70 border-rose-800/80 text-rose-300'
            }`}
          >
            {passedTests} / {totalTests} Passed
          </div>
        </div>
      </div>

      {/* Repair History Indicator if > 1 attempts */}
      {attemptHistory.length > 1 && (
        <div className="mb-3 p-2.5 bg-amber-950/30 border border-amber-800/60 rounded-lg flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-amber-300">
            <History className="w-4 h-4 shrink-0" />
            <span>Automatic Repair Activated: Recovered after <strong>{attemptHistory.length} attempts</strong></span>
          </div>
          <span className="font-mono text-[11px] text-amber-400">Self-Repaired</span>
        </div>
      )}

      {/* Individual Test Cards */}
      <div className="space-y-2 max-h-[220px] overflow-y-auto">
        {testResults.map((tc: any) => (
          <div
            key={tc.id}
            className={`p-2.5 rounded-lg border text-xs font-mono transition ${
              tc.status === 'pass'
                ? 'bg-slate-950/60 border-emerald-900/40 text-slate-300'
                : 'bg-rose-950/20 border-rose-900/60 text-rose-200'
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-200">Test #{tc.id}</span>
                {tc.description && (
                  <span className="text-[11px] text-slate-500 font-sans truncate max-w-[200px]">
                    {tc.description}
                  </span>
                )}
              </div>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase ${
                  tc.status === 'pass'
                    ? 'bg-emerald-900/60 text-emerald-300'
                    : 'bg-rose-900/60 text-rose-300'
                }`}
              >
                {tc.status}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-950 p-2 rounded border border-slate-900">
              <div>
                <span className="text-slate-500 block text-[10px]">Input:</span>
                <span className="text-sky-300 truncate block">{JSON.stringify(tc.input)}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">Expected:</span>
                <span className="text-emerald-300 truncate block">{JSON.stringify(tc.expected)}</span>
              </div>
            </div>

            {tc.status === 'fail' && tc.error && (
              <div className="mt-2 p-1.5 bg-rose-950/40 rounded border border-rose-900/40 text-rose-300 text-[11px] flex items-start gap-1.5">
                <Bug className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <span className="break-all">{tc.error}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
