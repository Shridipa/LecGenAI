import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Youtube, 
  Upload, 
  Type, 
  FileText, 
  Zap, 
  HelpCircle, 
  Layers,
  AlertCircle,
  Brain,
  Sparkles,
  ArrowRight,
  Layout
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSettings } from '../context/SettingsContext';
import { translations } from '../translations';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const API_BASE_URL = 'http://localhost:8000';

const Home = () => {
  const [inputType, setInputType] = useState('youtube');
  const [inputValue, setInputValue] = useState('');
  const [file, setFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('processing');
  const [error, setError] = useState(null);
  
  const { language } = useSettings();
  const t = translations[language];
  const navigate = useNavigate();
  const pollIntervalRef = useRef(null);

  const startPolling = (taskId) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/tasks/${taskId}`);
        const { status, result, error: taskError } = response.data;
        
        setProcessingStatus(status);
        
        if (status === 'completed') {
          clearInterval(pollIntervalRef.current);
          navigate('/results', { state: { result, taskId, title: result.title || 'Analysis Result' } });
        } else if (status === 'failed') {
          setError(taskError || 'Processing failed.');
          setIsProcessing(false);
          clearInterval(pollIntervalRef.current);
        }
      } catch {
        // Silently retry
      }
    }, 2000);
  };

  const handleProcess = async () => {
    if (!inputValue && !file) return;
    
    // File size check (10MB)
    if (inputType === 'upload' && file && file.size > 10 * 1024 * 1024) {
       // We will show a notification but proceed as the backend handles compression
       // But let's check if the user wants to know
    }

    setIsProcessing(true);
    setError(null);
    setProcessingStatus('pending');

    try {
      let response;
      const formData = new FormData();

      if (inputType === 'youtube') {
        formData.append('url', inputValue);
        response = await axios.post(`${API_BASE_URL}/process/youtube`, formData);
      } else if (inputType === 'text') {
        formData.append('text', inputValue);
        response = await axios.post(`${API_BASE_URL}/process/text`, formData);
      } else if (inputType === 'upload' && file) {
        formData.append('file', file);
        response = await axios.post(`${API_BASE_URL}/process/file`, formData);
      }

      if (response && response.data && response.data.task_id) {
        startPolling(response.data.task_id);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'The AI engine is currently unavailable. Please ensure the backend is running.');
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden transition-colors duration-500">
      <div className="mesh-bg">
        <div className="mesh-circle-1" />
        <div className="mesh-circle-2" />
      </div>

      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-8 relative z-10">
        {!isProcessing ? (
          <>
            {/* Hero Section */}
            <section className="text-center mb-16 mt-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-2xl mx-auto"
              >
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-6 font-outfit">
                  <Sparkles size={12} className="text-primary" />
                  <span className="text-[10px] uppercase tracking-widest font-semibold opacity-70">
                    Neural Knowledge Extraction • 1 Min Rapid Gen
                  </span>
                </div>
                <h2 className="text-4xl md:text-5xl font-bold mb-4 leading-tight tracking-tight text-main">
                  {t.heroTitle.split(' ').slice(0, -1).join(' ')} <span className="text-primary italic">{t.heroTitle.split(' ').pop()}</span>
                </h2>
                <p className="text-secondary text-base mb-6 leading-relaxed max-w-xl mx-auto">
                  {t.heroSubtitle}
                </p>
                <button 
                  onClick={() => document.getElementById('studio-input').scrollIntoView({ behavior: 'smooth' })}
                  className="btn-gradient px-8 py-3 text-xs uppercase tracking-widest shadow-lg shadow-primary/20 hover:shadow-primary/40"
                >
                  {t.generateNow}
                </button>
              </motion.div>
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start" id="studio-input">
              {/* Left: Input Controller */}
              <div className="lg:col-span-5 flex flex-col gap-6">
                <motion.section 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="glass p-8 rounded-3xl relative overflow-hidden border-white/5"
                >
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center border border-white/10">
                      <Zap size={20} className="text-primary" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-main">{t.studioTitle}</h3>
                      <p className="text-[11px] font-medium text-muted">{t.studioDesc}</p>
                    </div>
                  </div>

                  {/* Step 1: Source Selection */}
                  <div className="mb-6">
                    <div className="flex p-1 bg-black/10 rounded-xl border border-white/5">
                      {[
                        { id: 'youtube', icon: Youtube, label: t.link },
                        { id: 'upload', icon: Upload, label: t.file },
                        { id: 'text', icon: Type, label: t.notes },
                      ].map((type) => (
                        <button
                          key={type.id}
                          onClick={() => { setInputType(type.id); setInputValue(''); setFile(null); }}
                          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg transition-all duration-300 font-semibold text-[10px] tracking-wide uppercase ${
                            inputType === type.id 
                            ? 'bg-white/10 text-main shadow-md' 
                            : 'text-muted hover:text-secondary'
                          }`}
                        >
                          <type.icon size={14} />
                          {type.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Step 2: Content Input */}
                  <div className="space-y-6">
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={inputType}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                      >
                        {inputType === 'youtube' && (
                          <div className="relative group">
                            <input 
                              type="text" 
                              placeholder="Paste YouTube Link..."
                              className="input-premium pl-12 h-14 text-sm"
                              value={inputValue}
                              onChange={(e) => setInputValue(e.target.value)}
                            />
                            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-red-500 transition-colors">
                              <Youtube size={18} />
                            </div>
                          </div>
                        )}

                        {inputType === 'text' && (
                          <textarea 
                            placeholder="Paste your content here..."
                            className="input-premium min-h-[180px] resize-none leading-relaxed text-sm p-5"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                          />
                        )}

                        {inputType === 'upload' && (
                          <div className="space-y-4">
                            <div 
                              className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer group/upload ${
                                file ? 'border-primary/50 bg-primary/5' : 'border-white/10 hover:border-primary/30 hover:bg-white/[0.02]'
                              }`}
                              onClick={() => document.getElementById('fileInput').click()}
                            >
                              <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mx-auto mb-3 group-hover/upload:scale-110 transition-transform">
                                {file ? <FileText className="text-primary" size={24} /> : <Upload className="text-slate-400" size={24} />}
                              </div>
                              <p className="font-semibold text-sm mb-1">{file ? file.name : "Click to Upload File"}</p>
                              <p className="text-[10px] opacity-40">MP4, MP3, WAV (Max 10MB)</p>
                              <input id="fileInput" type="file" className="hidden" accept="video/*,audio/*" onChange={(e) => setFile(e.target.files[0])} />
                            </div>
                            
                            {file && file.size > 10 * 1024 * 1024 && (
                              <div className="flex items-center gap-3 text-primary text-[10px] p-3 bg-primary/5 rounded-xl border border-primary/10 font-bold uppercase tracking-wider">
                                <AlertCircle size={14} />
                                <span>Large file detected. It will be auto-compressed.</span>
                              </div>
                            )}
                          </div>
                        )}
                      </motion.div>
                    </AnimatePresence>

                    <button 
                      className="btn-gradient w-full h-14 text-xs font-bold uppercase tracking-widest flex items-center justify-center gap-2 shadow-lg hover:shadow-primary/25 relative overflow-hidden group/btn"
                      onClick={handleProcess}
                      disabled={isProcessing || (!inputValue && !file)}
                    >
                      <span>{t.generateBtn}</span>
                      <ArrowRight size={16} className="group-hover/btn:translate-x-1 transition-transform" />
                    </button>
                    
                    {error && (
                      <div className="flex items-center gap-3 text-error text-xs p-4 bg-error/10 rounded-xl border border-error/20">
                        <AlertCircle size={16} />
                        <span>{error}</span>
                      </div>
                    )}
                  </div>
                </motion.section>
              </div>

              {/* Right: Vision Dashboard */}
              <div className="lg:col-span-7">
                <div className="flex flex-col gap-6 h-full">
                  <motion.div 
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="glass p-8 rounded-3xl border-white/5 relative overflow-hidden h-full flex flex-col justify-center"
                  >
                    <div className="absolute top-0 right-0 p-12 opacity-[0.02] pointer-events-none transform translate-x-10 -translate-y-10">
                      <Layout size={300} />
                    </div>
                    
                    <div className="relative">
                      <h3 className="text-2xl font-bold mb-2 text-main">{t.workspaceTitle}</h3>
                      <p className="text-secondary text-sm mb-8 max-w-md font-medium">
                        {t.workspaceDesc}
                      </p>
                      
                      <div className="grid grid-cols-2 gap-4">
                        {[
                          { label: t.fastSummaries, icon: Zap, desc: 'Condensed knowledge' },
                          { label: t.flashcards, icon: Layers, desc: 'Active recall system' },
                          { label: t.quizzes, icon: HelpCircle, desc: 'Adaptive testing' },
                          { label: t.scripts, icon: FileText, desc: 'Verbatim logs' }
                        ].map((feat, i) => (
                          <div key={i} className="bg-white/5 p-4 rounded-xl border border-white/5 hover:border-primary/20 transition-colors group/feat">
                            <feat.icon size={20} className="text-primary/70 group-hover/feat:text-primary mb-3 transition-colors" />
                            <h4 className="text-xs font-bold mb-1">{feat.label}</h4>
                            <p className="text-[10px] opacity-40 leading-normal font-medium">{feat.desc}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                </div>
              </div>
            </div>
          </>
        ) : (
          /* Processing State */
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="min-h-[60vh] flex flex-col items-center justify-center p-8"
          >
            <div className="relative mb-12">
              <div className="w-32 h-32 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Brain size={40} className="text-primary animate-pulse" />
              </div>
            </div>
            <h2 className="text-2xl font-bold mb-2 text-main">
              {processingStatus === 'compressing' ? 'Compressing File...' : 
               processingStatus === 'optimizing' ? 'Optimizing Content...' :
               'Synthesizing Knowledge'}
            </h2>
            <p className="text-muted text-xs mb-8 font-bold uppercase tracking-widest text-center max-w-sm">
               {processingStatus === 'compressing' ? 
                 'Your file is being compressed, this may take some time before generation begins.' : 
                (processingStatus === 'processing' || processingStatus === 'optimizing') && file && file.size < 5 * 1024 * 1024 ?
                 'File size compressed for faster processing • Max 1 Minute' :
                 'Extraction in progress • Max 1 Minute'}
            </p>
            <div className="flex flex-col gap-3 max-w-xs w-full">
              {[
                { label: 'Analyzing Audio Stream', status: !['compressing', 'optimizing'].includes(processingStatus) },
                { label: 'Neural Knowledge Synthesis', status: processingStatus === 'processing' },
                { label: 'Building Study Path', status: false }
              ].map((step, i) => (
                <div key={i} className={`flex items-center gap-3 text-sm font-bold transition-opacity duration-500 ${step.status ? 'opacity-100' : 'opacity-30'}`}>
                  <div className={`w-2 h-2 rounded-full ${step.status ? 'bg-primary animate-pulse' : 'bg-slate-700'}`} />
                  <span>{step.label}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </main>

      <Footer />
    </div>
  );
};

export default Home;
