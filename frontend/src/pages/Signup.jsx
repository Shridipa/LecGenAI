import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { Mail, Lock, User, UserPlus, AlertCircle } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const Signup = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    
    try {
      await signup(name, email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="mesh-bg">
        <div className="mesh-circle-1" />
        <div className="mesh-circle-2" />
      </div>

      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-20 relative z-10 flex items-center justify-center">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass p-8 md:p-12 rounded-[32px] border-white/10 w-full max-w-md shadow-2xl shadow-primary/10"
        >
          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold mb-3 tracking-tight text-main">Join LecGen AI</h1>
            <p className="text-secondary text-sm font-medium">Create a free account to save your study progress</p>
          </div>

          {error && (
            <div className="flex items-center gap-3 text-error text-xs p-4 bg-error/10 rounded-xl border border-error/20 mb-6">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-muted ml-1">Full Name</label>
              <div className="relative group">
                <input 
                  type="text"
                  required
                  placeholder="John Doe"
                  className="input-premium pl-12 h-14"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors">
                  <User size={18} />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-muted ml-1">Email Address</label>
              <div className="relative group">
                <input 
                  type="email"
                  required
                  placeholder="name@example.com"
                  className="input-premium pl-12 h-14"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors">
                  <Mail size={18} />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-muted ml-1">Password</label>
              <div className="relative group">
                <input 
                  type="password"
                  required
                  placeholder="Create a strong password"
                  className="input-premium pl-12 h-14"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors">
                  <Lock size={18} />
                </div>
              </div>
            </div>

            <button 
              type="submit"
              disabled={isSubmitting}
              className="btn-gradient w-full h-14 text-xs font-bold uppercase tracking-widest flex items-center justify-center gap-3 shadow-lg hover:shadow-primary/25 disabled:opacity-50"
            >
              {isSubmitting ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <UserPlus size={18} /> Get Started
                </>
              )}
            </button>
          </form>

          <footer className="mt-8 pt-8 border-t border-white/5 text-center">
            <p className="text-muted text-sm font-medium">
              Already have an account? <Link to="/login" className="text-primary hover:text-primary-light transition-colors font-bold">Sign In</Link>
            </p>
          </footer>
        </motion.div>
      </main>

      <Footer />
    </div>
  );
};

export default Signup;
