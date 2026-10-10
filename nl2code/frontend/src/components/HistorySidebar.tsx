import React, { useEffect, useState } from 'react';
import { History, X, CheckCircle, XCircle, Trash2, Download, RefreshCw, ChevronRight } from 'lucide-react';
import { fetchHistory, fetchHistoryDetail, deleteHistoryItem, HistoryItem } from '../lib/api';

interface HistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRecord: (record: any) => void;
}

export const HistorySidebar: React.FC<HistorySidebarProps> = ({
  isOpen,
  onClose,
  onSelectRecord,
}) => {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchHistory();
      setItems(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const handleSelect = async (id: string) => {
    try {
      const full = await fetchHistoryDetail(id);
      onSelectRecord(full);
      onClose();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await deleteHistoryItem(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-80 md:w-96 bg-slate-900 border-l border-slate-800 shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-sky-400" />
          <h3 className="font-semibold text-slate-100 text-sm">Compilation History</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="p-1 text-slate-400 hover:text-slate-100 rounded hover:bg-slate-800"
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-100 rounded hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading && items.length === 0 ? (
          <div className="flex items-center justify-center p-8 text-slate-500 text-xs">
            Loading compilation history...
          </div>
        ) : items.length === 0 ? (
          <div className="text-center p-8 text-slate-500 text-xs">
            No previous compilations saved yet.
          </div>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              onClick={() => handleSelect(item.id)}
              className="p-3 rounded-lg bg-slate-950 hover:bg-slate-800/80 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition group"
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5">
                  {item.success ? (
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <XCircle className="w-3.5 h-3.5 text-rose-400" />
                  )}
                  <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-sky-300 uppercase">
                    {item.language}
                  </span>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                  <a
                    href={`/api/history/${item.id}/export`}
                    onClick={(e) => e.stopPropagation()}
                    download
                    className="p-1 text-slate-400 hover:text-sky-300 rounded"
                    title="Export JSON"
                  >
                    <Download className="w-3 h-3" />
                  </a>
                  <button
                    onClick={(e) => handleDelete(e, item.id)}
                    className="p-1 text-slate-400 hover:text-rose-400 rounded"
                    title="Delete Record"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>

              <p className="text-xs text-slate-300 font-sans line-clamp-2 leading-relaxed">
                {item.prompt}
              </p>

              <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                <span className="flex items-center gap-1 text-slate-400 group-hover:text-sky-400">
                  Inspect <ChevronRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
