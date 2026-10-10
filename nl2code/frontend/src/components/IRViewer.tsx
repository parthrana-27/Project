import React, { useState } from 'react';
import { Layers, Copy, Check, Braces, Clock, ShieldAlert } from 'lucide-react';

interface IRViewerProps {
  ir: any;
}

export const IRViewer: React.FC<IRViewerProps> = ({ ir }) => {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'structured' | 'json'>('structured');

  if (!ir) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col items-center justify-center min-h-[220px] text-center text-slate-500">
        <Braces className="w-8 h-8 mb-2 opacity-40" />
        <span className="text-xs font-mono">No Intermediate Representation generated yet.</span>
        <span className="text-[11px] text-slate-600 mt-1">Run compilation to inspect IR schema.</span>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(ir, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-indigo-400" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Intermediate Representation (IR)
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <div className="bg-slate-950 p-0.5 rounded-lg border border-slate-800 flex text-[11px]">
            <button
              onClick={() => setViewMode('structured')}
              className={`px-2 py-0.5 rounded ${viewMode === 'structured' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Schema
            </button>
            <button
              onClick={() => setViewMode('json')}
              className={`px-2 py-0.5 rounded ${viewMode === 'json' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Raw JSON
            </button>
          </div>
          <button
            onClick={handleCopy}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
            title="Copy IR JSON"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto max-h-[300px]">
        {viewMode === 'json' ? (
          <pre className="text-xs font-mono bg-slate-950 p-3 rounded-lg border border-slate-800 text-sky-300 leading-relaxed overflow-x-auto">
            {JSON.stringify(ir, null, 2)}
          </pre>
        ) : (
          <div className="space-y-3 text-xs">
            {/* Signature & Function */}
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-[10px] text-slate-500 uppercase font-mono block">Signature</span>
              <code className="text-sky-300 font-mono font-medium block mt-0.5">
                {ir.signature || `${ir.function_name}()`}
              </code>
            </div>

            {/* Complexity */}
            {ir.complexity_target && (
              <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 flex items-start gap-2">
                <Clock className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
                <div>
                  <div className="flex items-center gap-3 font-mono text-[11px]">
                    <span className="text-slate-400">Time: <strong className="text-amber-300">{ir.complexity_target.time_complexity}</strong></span>
                    <span className="text-slate-400">Space: <strong className="text-amber-300">{ir.complexity_target.space_complexity}</strong></span>
                  </div>
                  {ir.complexity_target.explanation && (
                    <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                      {ir.complexity_target.explanation}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Edge Cases */}
            {ir.edge_cases && ir.edge_cases.length > 0 && (
              <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                <span className="text-[10px] text-slate-500 uppercase font-mono block mb-1">
                  Guarded Edge Cases ({ir.edge_cases.length})
                </span>
                <ul className="list-disc list-inside text-[11px] text-slate-300 space-y-0.5">
                  {ir.edge_cases.map((ec: string, i: number) => (
                    <li key={i}>{ec}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Test cases badge */}
            <div className="text-[11px] text-slate-400 font-mono flex items-center justify-between px-1">
              <span>Synthesized Unit Tests:</span>
              <span className="text-indigo-400 font-bold">{ir.test_cases?.length || 0} Cases</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
