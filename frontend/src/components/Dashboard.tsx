import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { FileText, Clock } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function Dashboard({ onSelectPaper }: { onSelectPaper: (id: number) => void }) {
  const [papers, setPapers] = useState<any[]>([]);

  useEffect(() => {
    fetchPapers();
  }, []);

  const fetchPapers = async () => {
    try {
      const res = await axios.get(`${API_URL}/papers`);
      setPapers(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-6">
      {papers.map((p) => (
        <div 
            key={p.id} 
            onClick={() => onSelectPaper(p.id)}
            className="group bg-white p-5 rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-blue-200 cursor-pointer transition-all duration-200 transform hover:-translate-y-1"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="p-2.5 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors">
                <FileText className="w-6 h-6 text-blue-600" />
            </div>
            {p.is_processed ? (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Processed
                </span>
            ) : (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    Processing
                </span>
            )}
          </div>
          
          <h3 className="text-lg font-semibold text-gray-900 truncate pr-2 group-hover:text-blue-600 transition-colors">
              {p.filename}
          </h3>
          
          <div className="flex items-center mt-3 text-sm text-gray-500">
            <Clock className="w-4 h-4 mr-1.5" />
            <span>{new Date(p.created_at).toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            })}</span>
          </div>
        </div>
      ))}
      {papers.length === 0 && (
        <div className="col-span-full flex flex-col items-center justify-center py-16 px-4 text-center bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
            <div className="p-4 bg-white rounded-full shadow-sm mb-4">
                <FileText className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900">No papers yet</h3>
            <p className="mt-1 text-sm text-gray-500 max-w-sm">
                Upload your first exam paper above to start generating AI solutions.
            </p>
        </div>
      )}
    </div>
  );
}
