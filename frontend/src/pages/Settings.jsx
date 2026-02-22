import React from 'react';
import { Moon, Sun, Globe, Bell, User, Lock } from 'lucide-react';
import { motion } from 'framer-motion';
import { useSettings } from '../context/SettingsContext';
import { translations } from '../translations';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const Settings = () => {
  const { theme, setTheme, language, setLanguage, notifications, setNotifications } = useSettings();
  const t = translations[language];

  const settingsSections = [
    {
      title: t.appearance,
      icon: theme === 'dark' ? Moon : Sun,
      items: [
        {
          label: t.theme,
          type: 'toggle',
          options: [
            { value: 'light', label: t.light },
            { value: 'dark', label: t.dark },
          ],
          value: theme,
          onChange: setTheme,
        },
      ],
    },
    {
      title: t.languageRegion,
      icon: Globe,
      items: [
        {
          label: t.language,
          type: 'select',
          options: [
            { value: 'en', label: 'English' },
            { value: 'es', label: 'Español' },
            { value: 'fr', label: 'Français' },
          ],
          value: language,
          onChange: setLanguage,
        },
      ],
    },
    {
      title: t.notifications,
      icon: Bell,
      items: [
        {
          label: t.emailNotifications,
          type: 'checkbox',
          checked: notifications.email,
          onChange: () => setNotifications({ ...notifications, email: !notifications.email }),
        },
        {
          label: t.pushNotifications,
          type: 'checkbox',
          checked: notifications.push,
          onChange: () => setNotifications({ ...notifications, push: !notifications.push }),
        },
        {
          label: t.weeklySummary,
          type: 'checkbox',
          checked: notifications.weekly,
          onChange: () => setNotifications({ ...notifications, weekly: !notifications.weekly }),
        },
      ],
    },
    {
      title: t.account,
      icon: User,
      items: [
        {
          label: 'Email',
          type: 'display',
          value: 'user@example.com',
        },
        {
          label: 'Plan',
          type: 'display',
          value: t.proMember,
        },
      ],
    },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden transition-colors duration-500">
      <div className="mesh-bg">
        <div className="mesh-circle-1" />
        <div className="mesh-circle-2" />
      </div>

      <Navbar />

      <main className="max-w-4xl mx-auto px-6 py-12 relative z-10">
        <div className="mb-12">
          <h1 className="text-3xl md:text-4xl font-bold mb-3 tracking-tight text-main">{t.settings}</h1>
          <p className="text-secondary text-sm font-medium">
            Customize your LecGen AI experience
          </p>
        </div>

        <div className="space-y-6">
          {settingsSections.map((section, index) => (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="glass rounded-2xl p-6 border-white/5"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-primary">
                  <section.icon size={20} />
                </div>
                <h2 className="text-lg font-bold text-main">{section.title}</h2>
              </div>

              <div className="space-y-4">
                {section.items.map((item, i) => (
                  <div key={i} className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
                    <span className="text-sm font-semibold text-secondary">{item.label}</span>
                    
                    {item.type === 'toggle' && (
                      <div className="flex gap-2 bg-black/20 p-1 rounded-xl">
                        {item.options.map((opt) => (
                          <button
                            key={opt.value}
                            onClick={() => item.onChange(opt.value)}
                            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                              item.value === opt.value
                                ? 'bg-primary text-white shadow-lg'
                                : 'text-muted hover:text-secondary'
                            }`}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    )}

                    {item.type === 'select' && (
                      <select
                        value={item.value}
                        onChange={(e) => item.onChange(e.target.value)}
                        className="bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-primary/50 text-main font-semibold"
                      >
                        {item.options.map((opt) => (
                          <option key={opt.value} value={opt.value} className="bg-bg-dark text-main">
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    )}

                    {item.type === 'checkbox' && (
                      <button
                        onClick={item.onChange}
                        className={`w-12 h-6 rounded-full transition-all relative ${
                          item.checked ? 'bg-primary' : 'bg-white/10'
                        }`}
                      >
                        <motion.div
                          animate={{ x: item.checked ? 24 : 2 }}
                          className="absolute w-5 h-5 bg-white rounded-full top-0.5 shadow-sm"
                        />
                      </button>
                    )}

                    {item.type === 'display' && (
                      <span className="text-sm font-bold text-primary">{item.value}</span>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          ))}

          {/* Security Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="glass rounded-2xl p-6 border-white/5"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-error">
                <Lock size={20} />
              </div>
              <h2 className="text-lg font-bold">{t.security}</h2>
            </div>

            <div className="space-y-3">
              <button className="w-full px-6 py-3 bg-white/5 hover:bg-white/10 rounded-xl text-sm font-bold transition-all text-left text-main">
                {t.changePassword}
              </button>
              <button className="w-full px-6 py-3 bg-white/5 hover:bg-white/10 rounded-xl text-sm font-bold transition-all text-left text-main">
                {t.twoFactor}
              </button>
              <button className="w-full px-6 py-3 bg-error/10 hover:bg-error/20 rounded-xl text-sm font-bold text-error transition-all text-left border border-error/20">
                {t.deleteAccount}
              </button>
            </div>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Settings;
