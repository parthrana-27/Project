import React, { useState } from 'react';
import { 
  Terminal, 
  History, 
  Code2, 
  Layers, 
  Sparkles, 
  CheckCircle2, 
  Cpu, 
  Github, 
  FileText 
} from 'lucide-react';

import { PromptPanel } from './components/PromptPanel';
import { PipelineTimeline } from './components/PipelineTimeline';
import { IRViewer } from './components/IRViewer';
import { CodeEditor } from './components/CodeEditor';
import { TestResults } from './components/TestResults';
import { HistorySidebar } from './components/HistorySidebar';
import { useCompileStream } from './hooks/useCompileStream';

export const App: React.FC = () => {
  const [prompt, setPrompt] = useState('Write a function that returns the k most frequent elements in an array');
  const [language, setLanguage] = useState('python');
  const [maxRepairs, setMaxRepairs] = useState(3);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const {
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
  } = useCompileStream();

  const handleCompile = () => {
    compile(prompt, language, maxRepairs);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="h-14 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-md shadow-sky-500/20">
            <Cpu className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-tight text-white">NL2Code Compiler</h1>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-950 border border-sky-800 text-sky-400 font-semibold">
                PCD Project
              </span>
            </div>
            <p className="text-[10px] text-slate-400 leading-none">
              Natural Language-to-Code Pipeline with IR & Automated Repair
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsHistoryOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/60 transition"
          >
            <History className="w-3.5 h-3.5 text-sky-400" />
            <span>History</span>
          </button>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-rose-950/80 border-b border-rose-800 text-rose-200 px-6 py-2.5 text-xs flex items-center justify-between">
          <span>{error}</span>
        </div>
      )}

      {/* Main Three-Pane Layout */}
      <main className="flex-1 p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-5 max-w-[1700px] w-full mx-auto">
        {/* Pane 1: Prompt & Controls (col-span-3) */}
        <section className="lg:col-span-3 flex flex-col gap-4">
          <PromptPanel
            prompt={prompt}
            setPrompt={setPrompt}
            language={language}
            setLanguage={setLanguage}
            maxRepairs={maxRepairs}
            setMaxRepairs={setMaxRepairs}
            onCompile={handleCompile}
            isCompiling={isCompiling}
          />
        </section>

        {/* Pane 2: Compiler Timeline & Intermediate Representation (col-span-4) */}
        <section className="lg:col-span-4 flex flex-col gap-4">
          <PipelineTimeline stages={stages} messages={stageMessages} />
          <div className="flex-1">
            <IRViewer ir={ir} />
          </div>
        </section>

        {/* Pane 3: Generated Code Editor & Sandbox Test Suite (col-span-5) */}
        <section className="lg:col-span-5 flex flex-col gap-4">
          <div className="flex-1 min-h-[380px]">
            <CodeEditor
              code={code}
              language={language}
              onChange={setCode}
            />
          </div>
          <div>
            <TestResults
              testSummary={testSummary}
              attemptHistory={attemptHistory}
            />
          </div>
        </section>
      </main>

      {/* Slide-out History Sidebar */}
      <HistorySidebar
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onSelectRecord={(rec) => {
          setPrompt(rec.prompt);
          setLanguage(rec.language);
          loadPastRecord(rec);
        }}
      />
    </div>
  );
};

export default App;
