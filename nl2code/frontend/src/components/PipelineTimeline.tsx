import React from 'react';
import { 
  CheckCircle2, 
  CircleDashed, 
  AlertCircle, 
  RefreshCw, 
  Cpu, 
  FileCode2, 
  ShieldCheck, 
  Box, 
  Layers 
} from 'lucide-react';
import { StageName, StageStatus } from '../hooks/useCompileStream';

interface PipelineTimelineProps {
  stages: Record<StageName, StageStatus>;
  messages: Record<string, string>;
}

const STAGE_CONFIG: Array<{ key: StageName; label: string; icon: any; desc: string }> = [
  { key: 'intent', label: '1. Intent Parser', icon: Cpu, desc: 'Grammar analysis & constraint extraction' },
  { key: 'ir', label: '2. IR Builder', icon: Layers, desc: 'Strict Pydantic JSON IR generation' },
  { key: 'codegen', label: '3. Code Generator', icon: FileCode2, desc: 'Language-idiomatic synthesis' },
  { key: 'validate', label: '4. Static Validator', icon: ShieldCheck, desc: 'AST & syntax check' },
  { key: 'sandbox', label: '5. Sandbox Executor', icon: Box, desc: 'Isolated Docker unit test execution' },
  { key: 'repair', label: '6. Repair Loop', icon: RefreshCw, desc: 'Feedback loop & diagnostic recovery' },
];

export const PipelineTimeline: React.FC<PipelineTimelineProps> = ({ stages, messages }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Compiler Pipeline Stages
        </h3>
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
          6-Stage Architecture
        </span>
      </div>

      <div className="space-y-2.5">
        {STAGE_CONFIG.map(({ key, label, icon: Icon, desc }) => {
          const status = stages[key] || 'idle';
          const msg = messages[key];

          let statusIcon = <CircleDashed className="w-4 h-4 text-slate-600" />;
          let statusBadge = (
            <span className="text-[10px] text-slate-500 bg-slate-800/60 px-1.5 py-0.5 rounded">
              IDLE
            </span>
          );
          let borderClass = 'border-slate-800/80 bg-slate-950/40';

          if (status === 'running') {
            statusIcon = <div className="w-3.5 h-3.5 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />;
            statusBadge = (
              <span className="text-[10px] text-sky-400 bg-sky-950/60 border border-sky-800/60 px-1.5 py-0.5 rounded animate-pulse font-mono">
                RUNNING
              </span>
            );
            borderClass = 'border-sky-500/50 bg-sky-950/20 shadow-sm shadow-sky-500/10';
          } else if (status === 'ok') {
            statusIcon = <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
            statusBadge = (
              <span className="text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-1.5 py-0.5 rounded font-mono">
                PASSED
              </span>
            );
            borderClass = 'border-emerald-900/60 bg-emerald-950/10';
          } else if (status === 'failed') {
            statusIcon = <AlertCircle className="w-4 h-4 text-rose-400" />;
            statusBadge = (
              <span className="text-[10px] text-rose-400 bg-rose-950/60 border border-rose-800/60 px-1.5 py-0.5 rounded font-mono">
                FAILED
              </span>
            );
            borderClass = 'border-rose-900/60 bg-rose-950/10';
          }

          return (
            <div
              key={key}
              className={`flex items-center justify-between p-2.5 rounded-lg border transition ${borderClass}`}
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1 rounded bg-slate-800/80 text-slate-300">
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="text-xs font-medium text-slate-200">{label}</div>
                  <div className="text-[11px] text-slate-400 truncate max-w-[200px]">
                    {msg || desc}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {statusBadge}
                {statusIcon}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
