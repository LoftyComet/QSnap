import React, { useCallback, useState } from 'react';
import { UploadCloud } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function UploadZone({ onUploadComplete }: { onUploadComplete: (paper: any) => void }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUpload(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleUpload(e.target.files[0]);
    }
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_URL}/upload`, formData);
      // Wait a bit or trigger processing immediately?
      // Let's trigger processing here for UX flow
      const paperId = res.data.id;
      await axios.post(`${API_URL}/process/${paperId}`);
      
      // Fetch full paper details
      const paperRes = await axios.get(`${API_URL}/papers/${paperId}`);
      onUploadComplete(paperRes.data);
      
    } catch (err) {
      console.error(err);
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div 
      className={`relative group cursor-pointer border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ease-in-out ${
        isDragging 
          ? 'border-blue-500 bg-blue-50 scale-[1.02] shadow-lg' 
          : 'border-gray-200 hover:border-blue-400 hover:bg-gray-50'
      } bg-white`}
      onDragOver={handleDragOver}
      onDragLeave={handleLeave}
      onDrop={handleDrop}
      onClick={() => document.getElementById('file-upload')?.click()}
    >
      <div className="flex flex-col items-center justify-center space-y-4 pointer-events-none">
        <div className={`p-4 rounded-full transition-colors ${
            isDragging || uploading ? 'bg-blue-100' : 'bg-gray-100 group-hover:bg-blue-50'
        }`}>
            <UploadCloud className={`w-10 h-10 ${
                uploading ? 'animate-bounce text-blue-600' : 'text-gray-400 group-hover:text-blue-500'
            }`} />
        </div>
        
        <div className="space-y-2">
          <p className="text-xl font-semibold text-gray-700 group-hover:text-blue-600 transition-colors">
            {uploading ? 'Processing Image...' : 'Upload Exam Paper'}
          </p>
          <p className="text-sm text-gray-500 max-w-sm mx-auto">
            Drag and drop your exam paper image here, or click to browse files.
            <br />
            <span className="text-xs text-gray-400 mt-1 inline-block uppercase">Supports PNG, JPG</span>
          </p>
        </div>

        <input 
          type="file" 
          className="hidden" 
          id="file-upload" 
          onChange={handleFileSelect}
          accept="image/*"
          disabled={uploading}
        />
        
        {!uploading && (
            <button 
              className="mt-4 px-6 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-sm transition-all hover:shadow-md pointer-events-auto"
              onClick={(e) => {
                  e.stopPropagation();
                  document.getElementById('file-upload')?.click();
              }}
            >
              Select File
            </button>
        )}
      </div>
    </div>
  );
}
