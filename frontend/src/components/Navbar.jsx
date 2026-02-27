import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Brain } from 'lucide-react';
import { motion } from 'framer-motion';
import { useSettings } from '../context/SettingsContext';
import { translations } from '../translations';

const Navbar = () => {
  const location = useLocation();
  const { language } = useSettings();
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
                <motion.div
                  layoutId="activeNav"
                  className="absolute -bottom-1 left-0 right-0 h-0.5 bg-primary"
                />
              )}
            </Link>
          ))}
        </div>

        {/* Action Gap Container - Keeps layout balanced */}
        <div className="flex items-center gap-3">
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
