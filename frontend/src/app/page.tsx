"use client";

import React, { useState } from 'react';
import UploadZone from '../components/UploadZone';
import Workspace from '../components/Workspace';
import Dashboard from '../components/Dashboard';
import axios from 'axios';
import { Layout } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function Home() {
  const [view, setView] = useState<'dashboard' | 'workspace'>('dashboard');
  const [currentPaperData, setCurrentPaperData] = useState<any>(null);

  const handleUploadComplete = (paperData: any) => {
    setCurrentPaperData(paperData);
    setView('workspace');
  };

  const handleSelectPaper = async (id: number) => {
    try {
        const res = await axios.get(`${API_URL}/papers/${id}`);
        setCurrentPaperData(res.data);
        setView('workspace');
    } catch (e) {
        alert('Could not load paper');
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900">
       {/* Global Nav */}
       <nav className="bg-white border-b px-6 py-4 flex justify-between items-center sticky top-0 z-10">
          <div 
             className="flex items-center space-x-2 cursor-pointer"
             onClick={() => setView('dashboard')}
          >
             <div className="bg-blue-600 text-white p-1 rounded">
                <Layout className="w-6 h-6" />
             </div>
             <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                QSnap
             </span>
          </div>
          <div className="text-sm text-gray-500">Academic AI Assistant</div>
       </nav>

       {view === 'dashboard' ? (
           <div className="max-w-5xl mx-auto p-6 space-y-12">
              <section>
                 <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-900">Create New Solution</h1>
                    <p className="text-gray-500 mt-2">Upload a new exam paper to start detecting and solving questions.</p>
                 </div>
                 <UploadZone onUploadComplete={handleUploadComplete} />
              </section>

              <div className="border-t border-gray-200" />

              <section>
                 <div className="mb-6 flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-gray-900">Recent Papers</h2>
                 </div>
                 <Dashboard onSelectPaper={handleSelectPaper} />
              </section>
           </div>
       ) : (
           currentPaperData && (
             <Workspace 
                data={currentPaperData} 
                onBack={() => setView('dashboard')} 
             />
           )
       )}
    </main>
  );
}
