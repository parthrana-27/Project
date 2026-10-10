import React from 'react';
import { Play, Sparkles, Terminal, Cpu } from 'lucide-react';

interface PromptPanelProps {
  prompt: string;
  setPrompt: (v: string) => void;
  language: string;
  setLanguage: (v: string) => void;
  maxRepairs: number;
  setMaxRepairs: (v: number) => void;
  onCompile: () => void;
  isCompiling: boolean;
}

const DEMO_PRESETS = [
  {
    label: "Top K Frequent (Python)",
    prompt: "Write a function that returns the k most frequent elements in an array",
    lang: "python",
  },
  {
    label: "Valid Palindrome (C++)",
    prompt: "Check if a string is a valid palindrome ignoring punctuation and case",
    lang: "cpp",
  },
  {
    label: "Merge Intervals (Java)",
    prompt: "Merge overlapping intervals",
    lang: "java",
  },
  {
    label: "Debounce Function (JS)",
    prompt: "Debounce a function by N milliseconds",
    lang: "javascript",
  },
];

export const PromptPanel: React.FC<PromptPanelProps> = ({
  prompt,
  setPrompt,
  language,
  setLanguage,
  maxRepairs,
  setMaxRepairs,
  onCompile,
  isCompiling,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      if (!isCompiling && prompt.trim()) {
        onCompile();
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-sky-400" />
          <h2 className="font-semibold text-slate-100 text-sm tracking-wide uppercase">
            Compiler Input (Natural Language)
          </h2>
        </div>
        <span className="text-xs text-slate-400">Ctrl + Enter to run</span>
      </div>

      {/* Preset Buttons */}
      <div className="mt-3">
        <label className="text-xs font-medium text-slate-400 mb-1.5 block flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Demo Prompts
        </label>
        <div className="grid grid-cols-2 gap-2">
          {DEMO_PRESETS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setPrompt(p.prompt);
                setLanguage(p.lang);
              }}
              className="text-left text-xs bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white px-2.5 py-1.5 rounded-lg border border-slate-700/60 transition truncate"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Prompt Area */}
      <div className="mt-4 flex-1 flex flex-col">
        <label className="text-xs font-medium text-slate-400 mb-1">
          Algorithmic Specification / Problem Prompt
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your algorithm or logic in plain English... e.g. Write a function that returns the k most frequent elements in an array"
          rows={7}
          className="w-full flex-1 bg-slate-950 border border-slate-800 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 rounded-lg p-3 text-sm text-slate-200 resize-none font-sans leading-relaxed outline-none transition"
        />
      </div>

      {/* Target Options */}
      <div className="grid grid-cols-2 gap-3 mt-4">
        <div>
          <label className="text-xs font-medium text-slate-400 mb-1 block">
            Target Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="python">Python 3 (ast.parse)</option>
            <option value="cpp">C++ (std::vector, g++)</option>
            <option value="java">Java (Solution.class)</option>
            <option value="javascript">JavaScript (Node.js)</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-400 mb-1 block">
            Max Self-Repairs: {maxRepairs}
          </label>
          <input
            type="range"
            min="0"
            max="5"
            value={maxRepairs}
            onChange={(e) => setMaxRepairs(parseInt(e.target.value, 10))}
            className="w-full accent-sky-500 mt-2"
          />
        </div>
      </div>

      {/* Compile Button */}
      <button
        type="button"
        disabled={isCompiling || !prompt.trim()}
        onClick={onCompile}
        className={`mt-4 w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-medium text-sm transition ${
          isCompiling || !prompt.trim()
            ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
            : 'bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white shadow-lg shadow-sky-500/20 active:scale-[0.99]'
        }`}
      >
        {isCompiling ? (
          <>
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            <span>Compiling Pipeline...</span>
          </>
        ) : (
          <>
            <Play className="w-4 h-4 fill-current" />
            <span>Compile to Code</span>
          </>
        )}
      </button>
    </div>
  );
};
