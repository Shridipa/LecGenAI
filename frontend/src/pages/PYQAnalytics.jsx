import React, { useState } from 'react';
import axios from 'axios';
import { 
  Upload, 
  FileText, 
  Loader2, 
  BookOpen, 
  Youtube, 
  BarChart2, 
  AlertCircle,
  CheckCircle,
  HelpCircle,
  Library,
  Target
} from 'lucide-react';
import { motion } from 'framer-motion';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const PYQAnalytics = () => {
  const [files, setFiles] = useState([]);
  const [driveLink, setDriveLink] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (files.length === 0 && !driveLink) return;

    setIsAnalyzing(true);
    setError(null);

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    if (driveLink) {
      formData.append('drive_link', driveLink);
    }

    try {
      const response = await axios.post('http://localhost:8000/analyze/pyq', formData);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please check your files or link.');
    } finally {
      setIsAnalyzing(false);
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
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-widest mb-6"
          >
            <Library size={14} /> Exam Intelligence
          </motion.div>
          <h1 className="text-4xl md:text-6xl font-bold mb-6 tracking-tight text-main">
            PYQ <span className="text-gradient">Deep Analysis</span>
          </h1>
          <p className="text-base text-muted max-w-2xl mx-auto leading-relaxed">
            Upload your Previous Year Question papers (PDF, DOCX, CSV) to uncover recurring topics, 
            question patterns, and curated study resources.
          </p>
        </div>

        <div className="max-w-xl mx-auto mb-20">
          <div className="glass p-8 rounded-[32px] border-white/10 text-center relative overflow-hidden group">
            <div className={`border-2 border-dashed rounded-2xl p-10 transition-all cursor-pointer ${
              files.length > 0 ? 'border-primary/50 bg-primary/5' : 'border-white/10 hover:border-primary/30 hover:bg-white/[0.02]'
            }`}
            onClick={() => document.getElementById('pyq-upload').click()}
            >
              <input 
                id="pyq-upload" 
                type="file" 
                className="hidden" 
                accept=".pdf,.docx,.txt,.csv"
                multiple
                onChange={handleFileChange} 
              />
              
              <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
                {files.length > 0 ? <FileText size={32} className="text-primary" /> : <Upload size={32} className="text-slate-400" />}
              </div>
              
              <p className="font-bold text-lg mb-2 text-main">
                {files.length > 0 ? `${files.length} Files Selected` : "Drop PYQ Files Here"}
              </p>
              <p className="text-xs font-bold uppercase tracking-widest text-muted">
                PDF • DOCX • CSV • TXT
              </p>
            </div>

            <div className="mt-6 flex items-center gap-4">
              <div className="h-px bg-white/10 flex-1" />
              <span className="text-xs font-bold text-muted uppercase tracking-widest">OR</span>
              <div className="h-px bg-white/10 flex-1" />
            </div>

            <div className="mt-6 relative group/input">
              <input 
                type="text" 
                placeholder="Paste Google Drive Folder Link"
                className="w-full bg-black/20 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-sm focus:outline-none focus:border-primary/50 transition-all text-secondary"
                value={driveLink}
                onChange={(e) => setDriveLink(e.target.value)}
              />
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within/input:text-primary transition-colors">
                 <img src="https://upload.wikimedia.org/wikipedia/commons/1/12/Google_Drive_icon_%282020%29.svg" alt="Drive" className="w-5 h-5 opacity-70 grayscale group-focus-within/input:grayscale-0 transition-all" />
              </div>
            </div>

            {error && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 p-4 bg-error/10 border border-error/20 rounded-xl text-error text-sm font-bold flex items-center gap-3 justify-center"
              >
                <AlertCircle size={16} /> {error}
              </motion.div>
            )}

            <button
              onClick={handleAnalyze}
              disabled={(files.length === 0 && !driveLink) || isAnalyzing}
              className="mt-8 btn-gradient w-full py-4 rounded-xl text-sm font-bold uppercase tracking-widest flex items-center justify-center gap-3 shadow-lg hover:shadow-primary/25 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 size={18} className="animate-spin" /> Analyzing Pattern...
                </>
              ) : (
                <>
                  <BarChart2 size={18} /> Start Analysis
                </>
              )}
            </button>
          </div>
        </div>

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-12"
          >
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
               <div className="glass p-6 rounded-2xl border-white/5 flex items-center gap-5">
                 <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                   <FileText size={24} />
                 </div>
                 <div>
                   <p className="text-xs font-bold uppercase tracking-widest text-muted mb-1">Total Questions</p>
                   <p className="text-2xl font-bold text-main">{result.total_questions}</p>
                 </div>
               </div>
               <div className="glass p-6 rounded-2xl border-white/5 flex items-center gap-5">
                 <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center text-accent">
                   <Target size={24} />
                 </div>
                 <div>
                   <p className="text-xs font-bold uppercase tracking-widest text-muted mb-1">Topics Found</p>
                   <p className="text-2xl font-bold text-main">{result.topics_found}</p>
                 </div>
               </div>
               <div className="glass p-6 rounded-2xl border-white/5 flex items-center gap-5">
                 <div className="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center text-success">
                   <CheckCircle size={24} />
                 </div>
                 <div>
                   <p className="text-xs font-bold uppercase tracking-widest text-muted mb-1">Analysis Status</p>
                   <p className="text-2xl font-bold text-main">{result.summary?.analysis_status || 'Complete'}</p>
                 </div>
               </div>
               <div className="glass p-6 rounded-2xl border-white/5 flex items-center gap-5">
                 <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
                   <BookOpen size={24} />
                 </div>
                 <div>
                   <p className="text-xs font-bold uppercase tracking-widest text-muted mb-1">Resources Found</p>
                   <p className="text-2xl font-bold text-main">{result.summary?.total_resources_found || 0}</p>
                 </div>
               </div>
            </div>

            {/* Classification Breakdown */}
            {result.summary?.classification_breakdown && (
              <div className="glass p-6 rounded-2xl border-white/5 mb-12">
                <h3 className="text-sm font-bold uppercase tracking-widest text-secondary mb-4">Question Classification Breakdown</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 rounded-xl bg-primary/5 border border-primary/10">
                    <p className="text-3xl font-bold text-primary mb-1">{result.summary.classification_breakdown.critical}</p>
                    <p className="text-xs font-bold uppercase tracking-widest text-muted">Critical</p>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-accent/5 border border-accent/10">
                    <p className="text-3xl font-bold text-accent mb-1">{result.summary.classification_breakdown.important}</p>
                    <p className="text-xs font-bold uppercase tracking-widest text-muted">Important</p>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-slate-500/5 border border-slate-500/10">
                    <p className="text-3xl font-bold text-slate-400 mb-1">{result.summary.classification_breakdown.standard}</p>
                    <p className="text-xs font-bold uppercase tracking-widest text-muted">Standard</p>
                  </div>
                </div>
              </div>
            )}

            {/* Topics */}
            <div className="space-y-8">
              {result.analysis.map((topic, idx) => (
                <div key={idx} className="glass rounded-[32px] p-8 md:p-10 border-white/5">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8 border-b border-white/5 pb-8">
                    <div>
                      <h2 className="text-2xl font-bold text-main mb-2">{topic.topic.replace(/['"]+/g, '')}</h2>
                      <p className="text-sm font-medium text-muted">Identified cluster topic from question patterns</p>
                    </div>
                    {topic.resources.length > 0 && (
                       <a 
                         href={topic.resources[0].link}
                         target="_blank"
                         rel="noreferrer"
                         className="flex items-center gap-3 bg-red-600/10 hover:bg-red-600/20 px-5 py-3 rounded-xl border border-red-600/20 transition-all group/yt"
                       >
                         <Youtube size={20} className="text-red-500" />
                         <span className="text-xs font-bold uppercase tracking-wider text-red-500">Watch Tutorial</span>
                       </a>
                    )}
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-4">
                      <h3 className="text-xs font-bold uppercase tracking-widest text-secondary mb-4 flex items-center gap-2">
                        <FileText size={14} /> Key Questions
                      </h3>
                      {topic.questions.map((q, i) => (
                        <div key={i} className="p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-white/5">
                          <div className="flex gap-4">
                            <div className={`w-1.5 h-1.5 rounded-full mt-2 shrink-0 ${
                              q.importance === 'Standard' ? 'bg-slate-500' :
                              q.importance === 'Important' ? 'bg-accent' :
                              'bg-primary animate-pulse'
                            }`} />
                            <div className="flex-1">
                              <div className="text-sm leading-relaxed text-secondary mb-2">
                                {q.text.split(/(!\[Diagram\]\(.*?\))/g).map((part, idx) => {
                                  const match = part.match(/!\[Diagram\]\((.*?)\)/);
                                  if (match) {
                                    return (
                                      <div key={idx} className="my-4 rounded-lg overflow-hidden border border-white/10 max-w-md">
                                        <img src={match[1]} alt="Question Diagram" className="w-full h-auto object-contain bg-white/5 p-2" />
                                      </div>
                                    );
                                  }
                                  return <span key={idx}>{part}</span>;
                                })}
                              </div>
                              <div className="flex gap-2 mb-3">
                                <span className={`text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded ${
                                  q.importance === 'Standard' ? 'bg-slate-800 text-slate-400' :
                                  q.importance === 'Important' ? 'bg-accent/10 text-accent' :
                                  'bg-primary/10 text-primary'
                                }`}>
                                  {q.importance}
                                </span>
                              </div>
                              
                              {q.ai_answer && (
                                <div className="mt-3 p-3 rounded-lg bg-gradient-to-r from-primary/5 to-accent/5 border border-primary/10">
                                  <div className="flex items-start gap-2 mb-2">
                                    <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center shrink-0 mt-0.5">
                                      <svg className="w-3 h-3 text-primary" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                                      </svg>
                                    </div>
                                    <div className="flex-1">
                                      <p className="text-[10px] font-bold uppercase tracking-widest text-primary mb-1">AI-Generated Answer</p>
                                      <p className="text-xs leading-relaxed text-secondary/90">{q.ai_answer}</p>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="space-y-4">
                      <h3 className="text-xs font-bold uppercase tracking-widest text-secondary mb-4 flex items-center gap-2">
                        <BookOpen size={14} /> Curated Resources
                      </h3>
                      
                      {topic.resources && topic.resources.total_count === 0 ? (
                        <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-center">
                          <p className="text-xs text-muted">{topic.resources.message || "No resources found"}</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {/* Video Resources */}
                          {topic.resources?.videos && topic.resources.videos.length > 0 && (
                            <>
                              <p className="text-[10px] font-bold uppercase tracking-widest text-muted mb-2">📹 Video Tutorials</p>
                              {topic.resources.videos.map((res, i) => (
                                <a 
                                  key={`video-${i}`} 
                                  href={res.link}
                                  target="_blank" 
                                  rel="noreferrer"
                                  className="block p-3 rounded-xl bg-black/20 hover:bg-black/40 transition-all border border-white/5 group/res"
                                >
                                  <div className="relative aspect-video rounded-lg overflow-hidden mb-3">
                                    <img src={res.thumbnail} alt={res.title} className="w-full h-full object-cover group-hover/res:scale-105 transition-transform duration-500" />
                                    <div className="absolute bottom-2 right-2 bg-black/80 px-1.5 py-0.5 rounded text-[9px] font-bold text-white">
                                      {res.duration}
                                    </div>
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover/res:opacity-100 transition-opacity flex items-center justify-center">
                                      <Youtube size={32} className="text-white" />
                                    </div>
                                  </div>
                                  <p className="text-xs font-bold line-clamp-2 leading-relaxed text-secondary group-hover/res:text-primary transition-colors">{res.title}</p>
                                </a>
                              ))}
                            </>
                          )}
                          
                          {/* Article Resources */}
                          {topic.resources?.articles && topic.resources.articles.length > 0 && (
                            <>
                              <p className="text-[10px] font-bold uppercase tracking-widest text-muted mb-2 mt-4">📚 Articles & Tutorials</p>
                              {topic.resources.articles.map((res, i) => (
                                <a 
                                  key={`article-${i}`} 
                                  href={res.link}
                                  target="_blank" 
                                  rel="noreferrer"
                                  className="block p-3 rounded-xl bg-gradient-to-r from-accent/5 to-primary/5 hover:from-accent/10 hover:to-primary/10 transition-all border border-accent/10 group/article"
                                >
                                  <div className="flex items-start gap-3">
                                    <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center shrink-0">
                                      <BookOpen size={16} className="text-accent" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <p className="text-xs font-medium text-secondary line-clamp-2 group-hover/article:text-accent transition-colors mb-1">{res.title}</p>
                                      <span className="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-accent/10 text-accent">
                                        {res.platform}
                                      </span>
                                    </div>
                                  </div>
                                </a>
                              ))}
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
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

export default PYQAnalytics;
