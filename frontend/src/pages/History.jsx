import React, { useState } from 'react';
import { 
  Search, 
  Filter, 
  ExternalLink, 
  Trash2, 
  Download, 
  Youtube, 
  Upload, 
  Type, 
  Clock, 
  FileText 
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useSettings } from '../context/SettingsContext';
import { translations } from '../translations';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const History = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [historyData, setHistoryData] = useState([]);
  const [loading, setLoading] = useState(true);
  const { language } = useSettings();
  const t = translations[language];
  const navigate = useNavigate();

  const API_BASE_URL = 'http://localhost:8000';

  React.useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/history`);
        const data = await response.json();
        setHistoryData(data);
      } catch (error) {
        console.error("Failed to fetch history:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const filteredHistory = historyData.filter(item => {
    // Some types might be 'video'/'audio' in backend but 'upload' in frontend
    const uiType = (item.type === 'video' || item.type === 'audio') ? 'upload' : item.type;
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterType === 'all' || uiType === filterType;
    return matchesSearch && matchesFilter;
  });

  const handleView = (lecture) => {
    navigate('/results', { state: { result: lecture.result, taskId: lecture.id, title: lecture.title } });
  };

  const handleDelete = async (id) => {
    try {
      const response = await fetch(`${API_BASE_URL}/history/${id}`, { method: 'DELETE' });
      if (response.ok) {
        setHistoryData(prev => prev.filter(item => item.id !== id));
      }
    } catch (error) {
      console.error("Delete failed:", error);
    }
  };

  const handleDownload = (id) => {
    window.open(`${API_BASE_URL}/history/download/${id}`, '_blank');
  };

  const getSourceIcon = (type) => {
    switch (type) {
      case 'youtube': return <Youtube size={16} className="text-red-500" />;
      case 'upload': return <Upload size={16} className="text-secondary" />;
      case 'text': return <Type size={16} className="text-primary" />;
      default: return null;
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden transition-colors duration-500">
      <div className="mesh-bg">
        <div className="mesh-circle-1" />
        <div className="mesh-circle-2" />
      </div>

      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-12 relative z-10">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold mb-2 tracking-tight text-main">{t.history}</h1>
            <p className="text-muted text-sm font-medium">Review and manage your generated lecture materials</p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 items-center">
            <div className="relative group w-full sm:w-64">
              <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" />
              <input 
                type="text" 
                placeholder="Search history..."
                className="w-full bg-black/20 border border-white/10 rounded-xl pl-12 pr-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-all"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            <div className="flex p-1 bg-black/20 rounded-xl border border-white/10 w-full sm:w-auto">
              {['all', 'youtube', 'upload', 'text'].map((type) => (
                <button
                  key={type}
                  onClick={() => setFilterType(type)}
                  className={`px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${
                    filterType === type ? 'bg-primary text-white' : 'text-muted hover:text-secondary'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence mode="popLayout">
            {loading ? (
              // Loading Skeletons
              [...Array(3)].map((_, i) => (
                <div key={`skeleton-${i}`} className="glass rounded-3xl p-6 border-white/5 opacity-50 animate-pulse">
                  <div className="w-12 h-12 rounded-2xl bg-white/10 mb-6" />
                  <div className="h-6 bg-white/10 rounded-lg w-3/4 mb-4" />
                  <div className="h-4 bg-white/10 rounded-lg w-1/2 mb-6" />
                  <div className="h-10 bg-white/10 rounded-xl w-full" />
                </div>
              ))
            ) : (
              filteredHistory.map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ delay: index * 0.05 }}
                  layout
                  className="glass rounded-3xl p-6 border-white/5 hover:border-white/10 transition-all group"
                >
                  <div className="flex justify-between items-start mb-6">
                    <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10 group-hover:border-primary/30 transition-colors">
                      {getSourceIcon(item.type)}
                    </div>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleDownload(item.id)}
                        className="p-2 rounded-lg bg-white/5 text-muted hover:text-main hover:bg-white/10 transition-all"
                      >
                        <Download size={16} />
                      </button>
                      <button 
                        onClick={() => handleDelete(item.id)}
                        className="p-2 rounded-lg bg-white/5 text-muted hover:text-error hover:bg-error/10 transition-all"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>

                  <h3 className="text-lg font-bold mb-2 group-hover:text-primary transition-colors text-main">{item.title}</h3>
                  
                  <div className="flex items-center gap-4 text-xs font-bold mb-6 text-muted">
                    <div className="flex items-center gap-1.5">
                      <Clock size={14} />
                      {item.date}
                    </div>
                    <div className="flex items-center gap-1.5">
                      <FileText size={14} />
                      {item.wordCount} {t.words || 'words'}
                    </div>
                  </div>

                  <button 
                    onClick={() => handleView(item)}
                    className="w-full py-3 rounded-xl bg-white/5 hover:bg-primary hover:text-white transition-all text-xs font-bold uppercase tracking-widest border border-white/5 hover:border-transparent flex items-center justify-center gap-2"
                  >
                    View Result <ExternalLink size={14} />
                  </button>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>

        {!loading && filteredHistory.length === 0 && (
          <div className="text-center py-20">
            <p className="opacity-50 text-sm">No items found matching your search.</p>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
};

export default History;
