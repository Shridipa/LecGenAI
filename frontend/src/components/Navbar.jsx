import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Brain } from 'lucide-react';
import { motion as Motion } from 'framer-motion';
import { useSettings } from '../context/SettingsContext';
import { translations } from '../translations';
import { useAuth } from '../context/AuthContext';
import { LogOut, User as UserIcon } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();
  const { language } = useSettings();
  const { user, logout } = useAuth();
  const t = translations[language];
  
  const navLinks = [
    { path: '/', label: t.workspace },
    { path: '/history', label: t.history },
    { path: '/pyq-analysis', label: 'PYQ Analysis' },
    { path: '/settings', label: t.settings },
  ];

  return (
    <nav className="sticky top-0 z-50 px-6 py-4 transition-all duration-300">
      <div className="max-w-7xl mx-auto glass rounded-2xl px-6 py-3 flex justify-between items-center shadow-lg shadow-black/10">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative w-9 h-9 bg-gradient-to-tr from-primary via-accent to-secondary rounded-xl flex items-center justify-center shadow-inner">
            <Brain className="text-white drop-shadow-sm" size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight leading-none">
              LecGen <span className="text-primary italic">AI</span>
            </h1>
          </div>
        </Link>
        
        <div className="hidden lg:flex items-center gap-8 text-[10px] font-semibold uppercase tracking-widest text-secondary">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`hover:text-primary transition-colors relative ${
                location.pathname === link.path ? 'text-primary' : ''
              }`}
            >
              {link.label}
              {location.pathname === link.path && (
                <Motion.div
                  layoutId="activeNav"
                  className="absolute -bottom-1 left-0 right-0 h-0.5 bg-primary"
                />
              )}
            </Link>
          ))}
        </div>

        {/* Action Gap Container - Keeps layout balanced */}
        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3">
              {/* User avatar icon — no personal info shown */}
              <div
                className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary via-accent to-secondary flex items-center justify-center shadow-inner"
                title={user.name}
              >
                <UserIcon size={18} className="text-white" />
              </div>
              <button 
                onClick={logout}
                className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-muted hover:text-error hover:bg-error/10 transition-all border border-white/5"
                title="Logout"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link 
                to="/login"
                className="text-[10px] font-bold uppercase tracking-widest text-muted hover:text-primary transition-all px-3 py-2"
              >
                Login
              </Link>
              <Link 
                to="/signup"
                className="btn-gradient px-5 py-2 rounded-xl text-[9px] font-bold uppercase tracking-widest"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
