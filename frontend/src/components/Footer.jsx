import React from 'react';
import { Link } from 'react-router-dom';
import { Brain } from 'lucide-react';

const Footer = () => {
  const footerLinks = [
    { label: 'About', href: '#' },
    { label: 'Contact', href: '#' },
    { label: 'Privacy Policy', href: '#' },
    { label: 'Terms of Service', href: '#' },
  ];

  return (
    <footer className="mt-20 text-center text-slate-400 text-sm pb-12">
      <div className="max-w-7xl mx-auto border-t border-white/5 pt-12 px-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6 opacity-70">
          <div className="flex items-center gap-2">
            <Brain size={18} className="text-primary" />
            <p className="font-semibold tracking-tight text-white text-sm">
              LecGen AI Engine 
              <span className="text-[9px] bg-primary/20 text-primary px-2 py-0.5 rounded ml-2">v2.5.0</span>
            </p>
          </div>
          
          <div className="flex items-center gap-6 text-[9px] font-semibold uppercase tracking-[0.15em]">
            {footerLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="hover:text-primary transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>
          
          <p className="font-medium text-[9px] tracking-widest uppercase">
            © 2026 QUANTUM EDUCATION LABS
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
