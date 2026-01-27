import { X } from 'lucide-react';

interface AIModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  content: string;
}

export function AIModal({ isOpen, onClose, title, content }: AIModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-md"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[80vh] bg-[#1a2332] rounded-2xl border border-white/10 p-6 overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] text-white text-sm rounded-lg shadow-[0_0_20px_rgba(37,99,235,0.4)]">
              🤖 AI Analysis
            </span>
            <h3 className="text-white">{title}</h3>
          </div>
          
          <button
            onClick={onClose}
            className="text-gray-300 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto prose prose-invert max-w-none pr-2">
          {content.split('\n').map((line, idx) => {
            if (line.startsWith('**') && line.endsWith('**')) {
              return <h3 key={idx} className="text-white mt-4 mb-2">{line.replace(/\*\*/g, '')}</h3>;
            }
            if (line.startsWith('# ')) {
              return <h2 key={idx} className="text-xl text-white mb-3 mt-5">{line.slice(2)}</h2>;
            }
            if (line.startsWith('- ')) {
              return <li key={idx} className="text-gray-200 ml-4 mb-1">{line.slice(2)}</li>;
            }
            if (line.trim()) {
              return <p key={idx} className="text-gray-200 mb-3">{line}</p>;
            }
            return <br key={idx} />;
          })}
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-white/10 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gradient-to-r from-[#3b82f6] to-[#2563eb] text-white rounded-lg hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all duration-200 hover:scale-105"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}