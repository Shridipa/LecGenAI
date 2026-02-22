import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  FileText, 
  Search,
  Download, 
  ArrowLeft, 
  Check,
  Copy,
  Brain,
  HelpCircle,
  ClipboardCheck,
  Zap,
  Sparkles,
  X,
  Trophy,
  ChevronRight,
  RotateCcw
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSettings } from '../context/SettingsContext';
import { translations } from '../translations';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const Results = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const taskId = location.state?.taskId;
  const initialResult = location.state?.result;
  
  const { language } = useSettings();
  const t = translations[language];
  
  const [result, setResult] = useState(initialResult);
  const [activeTab, setActiveTab] = useState('notes');
  const [searchQuery, setSearchQuery] = useState('');
  const [copied, setCopied] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [selectedLang, setSelectedLang] = useState('es');
  
  const resultRef = useRef(null);

  useEffect(() => {
    if (!result) {
      navigate('/');
    }
  }, [result, navigate]);

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTranslate = async () => {
    if (!taskId) return;
    setIsTranslating(true);
    try {
      const formData = new FormData();
      formData.append('target_lang', selectedLang);
      const response = await axios.post(`http://localhost:8000/translate/${taskId}`, formData);
      if (response.data.status === 'success') {
        setResult(response.data.result);
      }
    } catch (err) {
      console.error('Translation failed', err);
    } finally {
      setIsTranslating(false);
    }
  };

  if (!result) return null;

  const tabs = [
    { id: 'notes', label: 'Lecture Notes', icon: ClipboardCheck },
    { id: 'qa', label: 'Important Q&A', icon: HelpCircle },
    { id: 'transcript', label: t.transcript, icon: FileText },
    { id: 'quiz', label: t.examLab, icon: Zap },
    { id: 'flashcards', label: t.flashcards, icon: Brain },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden transition-colors duration-500">
      <div className="mesh-bg">
        <div className="mesh-circle-1" />
        <div className="mesh-circle-2" />
      </div>

      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-8">
        <header className="flex flex-col xl:flex-row xl:items-center justify-between gap-6 mb-8 bg-white/5 p-6 rounded-3xl border border-white/10 glass">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => navigate('/')}
              className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-slate-400 hover:text-primary hover:bg-white/10 transition-all border border-white/5"
            >
              <ArrowLeft size={18} />
            </button>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-xl font-bold tracking-tight text-main">
                  {isTranslating ? 'Refining Knowledge' : 'Generation Complete'}
                </h2>
                {result.language && result.language !== 'en' && (
                  <span className="px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20 text-[9px] font-black uppercase tracking-widest text-primary">
                    {result.language === 'es' ? 'Spanish' : 
                     result.language === 'fr' ? 'French' : 
                     result.language === 'de' ? 'German' : 
                     result.language === 'hi' ? 'Hindi' : result.language}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted font-medium">
                {isTranslating ? 'Translating… this may take a few seconds.' : 'Translation available — select your preferred language.'}
              </p>
            </div>
          </div>
          
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center bg-black/20 rounded-xl border border-white/5 p-1">
              <select 
                value={selectedLang}
                onChange={(e) => setSelectedLang(e.target.value)}
                disabled={isTranslating}
                className="bg-transparent text-[10px] font-bold uppercase tracking-wider px-3 py-1.5 focus:outline-none disabled:opacity-50"
              >
                <option value="es" className="bg-bg-dark">Español</option>
                <option value="fr" className="bg-bg-dark">Français</option>
                <option value="de" className="bg-bg-dark">Deutsch</option>
                <option value="hi" className="bg-bg-dark">Hindi</option>
                <option value="ja" className="bg-bg-dark">Japanese</option>
                <option value="ko" className="bg-bg-dark">Korean</option>
              </select>
              <button 
                onClick={handleTranslate}
                disabled={isTranslating}
                className="bg-primary/10 hover:bg-primary/20 text-primary px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all disabled:opacity-50 flex items-center gap-2"
              >
                {isTranslating ? <div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin" /> : <Sparkles size={12} />}
                {isTranslating ? 'Translating' : 'Translate'}
              </button>
            </div>

            <button 
              className="px-5 py-2.5 rounded-xl border border-white/10 text-xs font-bold text-slate-300 hover:text-primary hover:bg-white/5 transition-all uppercase tracking-wide flex items-center gap-2"
            >
              <Download size={14} /> Export JSON
            </button>
          </div>
        </header>

        <div className="glass rounded-[32px] overflow-hidden border border-white/5 min-h-[70vh] flex flex-col">
          {/* Tabs */}
          <div className="flex items-center border-b border-white/5 px-8 pt-6 gap-8 overflow-x-auto no-scrollbar">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`pb-4 text-[11px] font-bold uppercase tracking-widest transition-colors relative whitespace-nowrap flex items-center gap-2 ${
                  activeTab === tab.id ? 'text-primary border-primary' : 'text-slate-500 hover:text-slate-300 border-transparent'
                }`}
              >
                <tab.icon size={14} />
                {tab.label}
                {activeTab === tab.id && (
                  <motion.div layoutId="activeResultTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                )}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 p-8 md:p-12 overflow-y-auto custom-scroll" ref={resultRef}>
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
              >
                {activeTab === 'notes' && (
                  <div className="max-w-3xl mx-auto">
                    <div className="flex items-center justify-between mb-8">
                       <h3 className="text-2xl font-bold tracking-tight">Structured Lecture Notes</h3>
                       <button 
                         onClick={() => handleCopy(result.notes)}
                         className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-muted hover:text-primary transition-colors"
                       >
                         {copied ? <Check size={14} className="text-success" /> : <Copy size={14} />}
                         {copied ? 'Copied' : 'Copy Notes'}
                       </button>
                    </div>
                    <div className="space-y-6">
                      {result.notes.split('\n').filter(l => l.trim()).map((line, i) => (
                        <div key={i} className="flex gap-5 group">
                          <div className="w-1.5 h-1.5 rounded-full bg-primary/40 mt-2.5 shrink-0 group-hover:bg-primary transition-all duration-300" />
                          <p className="text-secondary leading-relaxed text-base">{line.replace(/^- /, '')}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'qa' && (
                  <div className="max-w-4xl mx-auto">
                    <div className="mb-10">
                      <h3 className="text-2xl font-bold tracking-tight text-main">Important Q&A</h3>
                      <p className="text-muted text-sm font-medium">Curated list of critical questions and comprehensive answers</p>
                    </div>
                    <div className="space-y-6">
                      {(result.qa || []).map((item, i) => (
                        <div key={i} className="glass p-6 rounded-2xl border-white/5 hover:border-white/10 transition-all">
                          <div className="flex items-center gap-3 mb-4">
                            <span className={`px-2 py-0.5 rounded-full text-[8px] font-black tracking-widest uppercase border ${
                              item.type === 'long' ? 'text-primary border-primary/20 bg-primary/5' : 'text-accent border-accent/20 bg-accent/5'
                            }`}>
                              {item.type === 'long' ? 'Critical Analysis' : 'Short Insight'}
                            </span>
                          </div>
                          <h4 className="text-lg font-bold mb-3 text-main">Q: {item.question}</h4>
                          <p className="text-secondary leading-relaxed text-sm bg-white/5 p-4 rounded-xl">
                            <span className="font-bold text-primary mr-2">A:</span>
                            {item.answer}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'transcript' && (
                  <div className="max-w-4xl mx-auto">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                      <div>
                        <h3 className="text-2xl font-bold tracking-tight text-main">Full Transcript</h3>
                        <p className="text-muted text-sm font-medium">Verbatim text indexed by neural network</p>
                      </div>
                      <div className="relative w-full md:w-64 group">
                        <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" />
                        <input 
                          type="text" 
                          placeholder="Search text..."
                          className="w-full bg-black/20 border border-white/10 rounded-xl pl-12 pr-4 py-2.5 text-sm focus:outline-none focus:border-primary/50 transition-all"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                        />
                      </div>
                    </div>
                    <div className="bg-black/10 rounded-3xl p-10 font-inter text-base leading-loose whitespace-pre-wrap border border-white/5 relative selection:bg-primary/30">
                      {result.transcript.split('\n').map((para, i) => {
                        if (!searchQuery) return <p key={i} className="mb-6">{para}</p>;
                        
                        const parts = para.split(new RegExp(`(${searchQuery})`, 'gi'));
                        return (
                          <p key={i} className="mb-6">
                            {parts.map((part, j) => 
                              part.toLowerCase() === searchQuery.toLowerCase() 
                                ? <span key={j} className="bg-primary/40 rounded px-1">{part}</span> 
                                : part
                            )}
                          </p>
                        );
                      })}
                    </div>
                  </div>
                )}

                {activeTab === 'quiz' && (
                  <QuizEngine questions={result.quiz || []} t={t} />
                )}

                {activeTab === 'flashcards' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                     {result.flashcards.map((card, i) => (
                        <Flashcard key={i} front={card.front} back={card.back} t={t} />
                     ))}
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

const QuizEngine = ({ questions }) => {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [isFinished, setIsFinished] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  // Limited to 20 for free version logic
  const displayQuestions = questions.slice(0, 20);

  const handleAnswer = (option) => {
    if (answers[currentIdx]) return;

    const q = displayQuestions[currentIdx];
    const isCorrect = option.toLowerCase() === q.correct.toLowerCase();
    
    setAnswers({
      ...answers,
      [currentIdx]: { selected: option, isCorrect }
    });
    
    setShowExplanation(true);
  };

  const handleNext = () => {
    if (currentIdx < displayQuestions.length - 1) {
      setCurrentIdx(currentIdx + 1);
      setShowExplanation(false);
    } else {
      setIsFinished(true);
    }
  };

  const calculateScore = () => {
    const correctCount = Object.values(answers).filter(a => a.isCorrect).length;
    const total = displayQuestions.length;
    const percentage = Math.round((correctCount / total) * 100);
    return { correctCount, total, percentage };
  };

  if (!displayQuestions.length) return <div>No questions generated.</div>;

  if (isFinished) {
    const { correctCount, total, percentage } = calculateScore();
    return (
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-2xl mx-auto text-center py-12"
      >
        <div className="w-24 h-24 bg-gradient-to-tr from-primary to-accent rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-primary/20">
          <Trophy size={48} className="text-white" />
        </div>
        <h3 className="text-3xl font-bold mb-2 tracking-tight text-main">Quiz Session Complete</h3>
        <p className="text-muted mb-12 font-medium">Here's your performance breakdown</p>

        <div className="grid grid-cols-3 gap-6 mb-12">
          <div className="glass p-6 rounded-2xl border-white/5">
            <p className="text-xs font-bold opacity-50 uppercase tracking-widest mb-1">Score</p>
            <p className="text-2xl font-bold">{correctCount} / {total}</p>
          </div>
          <div className="glass p-6 rounded-2xl border-white/5">
            <p className="text-xs font-bold opacity-50 uppercase tracking-widest mb-1">Percentage</p>
            <p className="text-2xl font-bold text-primary">{percentage}%</p>
          </div>
          <div className="glass p-6 rounded-2xl border-white/5">
            <p className="text-xs font-bold opacity-50 uppercase tracking-widest mb-1">Status</p>
            <p className={`text-2xl font-bold ${percentage >= 70 ? 'text-success' : 'text-error'}`}>
              {percentage >= 70 ? 'Passed' : 'Review'}
            </p>
          </div>
        </div>

        <button 
          onClick={() => {
            setCurrentIdx(0);
            setAnswers({});
            setIsFinished(false);
          }}
          className="btn-gradient px-8 py-3 rounded-xl text-xs font-bold uppercase tracking-widest flex items-center gap-2 mx-auto"
        >
          <RotateCcw size={16} /> Retake Examination
        </button>
      </motion.div>
    );
  }

  const q = displayQuestions[currentIdx];

  return (
    <div className="max-w-3xl mx-auto py-4">
      <div className="mb-12">
        <div className="flex items-center justify-between mb-3">
           <span className="text-[10px] font-black uppercase tracking-widest text-muted">
              Examination Module <span className="text-primary ml-1">{currentIdx + 1} / {displayQuestions.length}</span>
           </span>
        </div>
        <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
           <motion.div 
             className="h-full bg-primary"
             initial={{ width: 0 }}
             animate={{ width: `${((currentIdx + 1) / displayQuestions.length) * 100}%` }}
           />
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={currentIdx}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          className="space-y-8"
        >
          <div className="glass p-10 rounded-[40px] border-white/5 relative overflow-hidden">
            <div className="relative">
              <div className="flex items-center gap-3 mb-6">
                <span className={`px-3 py-1 rounded-full text-[9px] font-black tracking-widest uppercase border ${
                  q.type === 'mcq' ? 'text-primary border-primary/20 bg-primary/5' : 
                  q.type === 'short' ? 'text-accent border-accent/20 bg-accent/5' : 
                  'text-secondary border-secondary/20 bg-secondary/5'
                }`}>
                  {q.type === 'mcq' ? 'Multiple Choice' : q.type === 'short' ? 'Short Practice' : 'Case Analysis'}
                </span>
              </div>

              <h2 className="text-xl md:text-2xl font-bold mb-10 leading-tight text-main">
                {q.question}
              </h2>

              {q.type === 'mcq' ? (
                <div className="grid grid-cols-1 gap-4">
                  {q.options.map((opt, i) => {
                    const isSelected = answers[currentIdx]?.selected === opt;
                    const isCorrect = opt.toLowerCase() === q.correct.toLowerCase();
                    const hasAnswered = !!answers[currentIdx];

                    let variantClass = "bg-white/5 border-white/5 hover:border-white/10 opacity-80";
                    if (hasAnswered) {
                      if (isCorrect) variantClass = "bg-success/10 border-success/40 text-success shadow-[0_0_20px_rgba(16,185,129,0.1)]";
                      else if (isSelected) variantClass = "bg-error/10 border-error/40 text-error";
                      else variantClass = "opacity-40 grayscale pointer-events-none";
                    }

                    return (
                      <button
                        key={i}
                        disabled={hasAnswered}
                        onClick={() => handleAnswer(opt)}
                        className={`w-full p-5 rounded-2xl border text-left text-sm font-semibold transition-all duration-300 flex items-center justify-between group ${variantClass}`}
                      >
                        <span className="flex items-center gap-4">
                          <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-[10px] font-bold border ${
                             isSelected ? 'bg-current text-white border-transparent' : 'bg-white/5 border-white/10'
                          }`}>
                            {String.fromCharCode(65 + i)}
                          </span>
                          {opt}
                        </span>
                        {hasAnswered && isCorrect && <Check size={18} />}
                        {hasAnswered && isSelected && !isCorrect && <X size={18} />}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="space-y-6">
                   <div className="bg-black/20 border border-white/5 rounded-2xl p-6 relative">
                      <textarea 
                        placeholder="Draft your response here..."
                        className="w-full bg-transparent border-none focus:outline-none text-sm min-h-[120px] resize-none leading-relaxed"
                      />
                   </div>
                   
                   {!showExplanation && (
                     <button 
                       onClick={() => setShowExplanation(true)}
                       className="text-[10px] font-black uppercase tracking-[0.2em] text-primary hover:text-primary-light transition-colors flex items-center gap-2 p-2"
                     >
                       Evaluate and Show Logic <ChevronRight size={14} />
                     </button>
                   )}
                </div>
              )}

              {showExplanation && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-10 p-6 rounded-2xl bg-white/[0.03] border border-white/5"
                >
                  <p className="text-sm font-bold mb-2 text-main">{q.correct}</p>
                  <p className="text-xs text-muted leading-relaxed font-bold">
                    {q.explanation}
                  </p>
                </motion.div>
              )}
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <button
               onClick={handleNext}
               disabled={!showExplanation}
               className={`group flex items-center gap-3 px-10 py-4 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] transition-all shadow-xl ${
                 showExplanation 
                 ? 'btn-gradient shadow-primary/20 text-white' 
                 : 'bg-white/5 text-slate-600 border border-white/5 cursor-not-allowed'
               }`}
            >
              {currentIdx === displayQuestions.length - 1 ? 'Finish Exam' : 'Next Question'}
              <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

const Flashcard = ({ front, back }) => {
  const [isFlipped, setIsFlipped] = useState(false);

  return (
    <div 
      className="h-80 perspective-1000 cursor-pointer group"
      onClick={() => setIsFlipped(!isFlipped)}
    >
      <div 
        className={`relative w-full h-full text-center transition-transform duration-700 transform-style-3d preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`}
      >
        <div className="absolute inset-0 backface-hidden glass-card p-10 flex flex-col items-center justify-center text-center border border-white/5 shadow-2xl group-hover:border-primary/30 transition-all rounded-[32px]">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 border border-primary/20">
            <Brain size={24} className="text-primary" />
          </div>
          <h3 className="font-bold text-lg leading-tight mb-4 text-main">{front}</h3>
          <div className="absolute bottom-8 flex items-center gap-2 text-primary font-bold text-[10px] tracking-widest uppercase opacity-60 group-hover:opacity-100 transition-all">
            <span>Tap to Flip</span>
          </div>
        </div>
        
        <div 
          className="absolute inset-0 backface-hidden glass-card p-10 flex flex-col items-center justify-center bg-gradient-to-br from-primary/10 to-indigo-950/40 border border-primary/30 rounded-[32px] rotate-y-180"
        >
          <p className="text-[10px] font-black uppercase tracking-widest text-primary mb-6">Mastery Answer</p>
          <p className="font-medium text-lg leading-relaxed">{back}</p>
        </div>
      </div>
    </div>
  );
};

export default Results;
