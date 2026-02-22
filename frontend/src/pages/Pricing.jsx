import React from 'react';
import { Check, Zap, Sparkles, Crown } from 'lucide-react';
import { motion } from 'framer-motion';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const Pricing = () => {
  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: '/month',
      icon: Zap,
      features: [
        'Limited lecture generation (5/month)',
        'Basic summaries',
        'Standard transcription quality',
        'Community support',
      ],
      cta: 'Get Started',
      highlighted: false,
    },
    {
      name: 'Standard',
      price: '$4.99',
      period: '/month',
      icon: Sparkles,
      features: [
        'Unlimited lecture generation',
        'Full transcripts',
        'AI-powered quizzes',
        'Detailed summaries',
        'Flashcard generation',
        'Email support',
      ],
      cta: 'Upgrade to Standard',
      highlighted: true,
    },
    {
      name: 'Pro',
      price: '$9.99',
      period: '/month',
      icon: Crown,
      features: [
        'All Standard features',
        'Advanced analytics dashboard',
        'Export to multiple formats (PDF, DOCX)',
        'Priority processing',
        'Custom AI model fine-tuning',
        'Priority support (24/7)',
        'API access',
      ],
      cta: 'Upgrade to Pro',
      highlighted: false,
    },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden transition-colors duration-500">
      <div className="mesh-bg">
        <div className="mesh-circle-1" />
        <div className="mesh-circle-2" />
      </div>

      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 mb-6"
          >
            <Sparkles size={11} className="text-primary" />
            <span className="text-[9px] uppercase tracking-widest font-bold text-secondary">
              Transparent Pricing
            </span>
          </motion.div>
          
          <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight text-main">
            Choose Your Plan
          </h1>
          <p className="text-secondary text-base max-w-2xl mx-auto leading-relaxed font-medium">
            Unlock the full power of AI-driven learning. Start free, upgrade anytime.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`glass rounded-3xl p-8 relative overflow-hidden transition-all duration-300 ${
                plan.highlighted
                  ? 'border-primary/50 shadow-2xl shadow-primary/10 scale-105'
                  : 'border-white/5 hover:border-white/10'
              }`}
            >
              {plan.highlighted && (
                <div className="absolute top-4 right-4">
                  <span className="text-[8px] font-black uppercase tracking-widest bg-primary text-white px-3 py-1 rounded-full">
                    Most Popular
                  </span>
                </div>
              )}

              {plan.name !== 'Free' && (
                <div className="absolute top-4 left-4">
                  <span className="text-[7px] font-black uppercase tracking-widest bg-amber-500/20 text-amber-500 border border-amber-500/30 px-2 py-0.5 rounded-full">
                    Coming Soon
                  </span>
                </div>
              )}

              <div className="mb-6">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${
                  plan.highlighted ? 'bg-primary/20 text-primary' : 'bg-white/5 text-muted'
                }`}>
                  <plan.icon size={24} />
                </div>
                <h3 className="text-xl font-bold mb-2 text-main">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-main">{plan.price}</span>
                  <span className="text-muted text-sm">{plan.period}</span>
                </div>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm">
                    <Check
                      size={16}
                      className={`shrink-0 mt-0.5 ${
                        plan.highlighted ? 'text-primary' : 'text-muted'
                      }`}
                    />
                    <span className="text-secondary leading-relaxed font-medium">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                disabled={plan.name !== 'Free'}
                className={`w-full py-3 rounded-xl font-semibold text-sm transition-all ${
                  plan.name === 'Free'
                    ? (plan.highlighted 
                        ? 'btn-gradient shadow-lg shadow-primary/20 hover:shadow-primary/40' 
                        : 'bg-white/5 text-white hover:bg-white/10 border border-white/10')
                    : 'bg-white/5 text-muted cursor-not-allowed border border-white/5 opacity-50'
                }`}
              >
                {plan.name === 'Free' ? plan.cta : 'Available Soon'}
              </button>
            </motion.div>
          ))}
        </div>

        {/* FAQ or Additional Info */}
        <div className="mt-20 text-center">
          <p className="text-muted text-sm font-medium">
            All plans include a 14-day money-back guarantee. No questions asked.
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Pricing;
