import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Code2, Download, Copy, Check, FileCheck } from 'lucide-react';

interface CodeEditorProps {
  code: string;
  language: string;
  onChange?: (val: string) => void;
  readOnly?: boolean;
}

const LANG_MAP: Record<string, string> = {
  python: 'python',
  cpp: 'cpp',
  java: 'java',
  javascript: 'javascript',
};

const EXT_MAP: Record<string, string> = {
  python: 'py',
  cpp: 'cpp',
  java: 'java',
  javascript: 'js',
};

export const CodeEditor: React.FC<CodeEditorProps> = ({
  code,
  language,
  onChange,
  readOnly = false,
}) => {
  const [copied, setCopied] = useState(false);

  const monacoLang = LANG_MAP[language.toLowerCase()] || 'python';
  const ext = EXT_MAP[language.toLowerCase()] || 'txt';

  const handleCopy = () => {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!code) return;
    const blob = new Blob([code], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `solution.${ext}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-950 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Code2 className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Synthesized Target Source ({language.toUpperCase()})
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={handleCopy}
            disabled={!code}
            className="flex items-center gap-1 px-2.5 py-1 text-xs text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition disabled:opacity-40"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>Copy</span>
          </button>
          <button
            onClick={handleDownload}
            disabled={!code}
            className="flex items-center gap-1 px-2.5 py-1 text-xs text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition disabled:opacity-40"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download .{ext}</span>
          </button>
        </div>
      </div>

      {/* Editor Body */}
      <div className="flex-1 min-h-[350px] relative bg-slate-950">
        {!code ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-600 font-mono text-xs">
            <FileCheck className="w-8 h-8 mb-2 opacity-30" />
            <span>Awaiting synthesized code from compiler pipeline...</span>
          </div>
        ) : (
          <Editor
            height="100%"
            language={monacoLang}
            theme="vs-dark"
            value={code}
            onChange={(val) => onChange && onChange(val || '')}
            options={{
              readOnly: readOnly,
              minimap: { enabled: false },
              fontSize: 13,
              fontFamily: "'Fira Code', monospace",
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 4,
              padding: { top: 12, bottom: 12 },
            }}
          />
        )}
      </div>
    </div>
  );
};
