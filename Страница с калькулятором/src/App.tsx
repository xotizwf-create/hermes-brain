/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ArrowRight, ArrowLeft, RotateCcw, Wallet, Percent, Receipt, TrendingUp, Calculator, CheckCircle2 } from 'lucide-react';

type FormData = {
  revenue: string;
  spp: string;
  cost: string;
  ads: string;
};

const steps = [
  { id: 'revenue', key: 'revenue', title: 'Цена реализации (ДО СПП)', subtitle: 'Введите цену реализации', placeholder: '1 000 000', icon: Wallet, symbol: '₽' },
  { id: 'spp', key: 'spp', title: '% СПП', subtitle: 'Введите процент СПП', placeholder: '15', icon: Percent, symbol: '%' },
  { id: 'cost', key: 'cost', title: 'Себестоимость', subtitle: 'Введите себестоимость проданных товаров', placeholder: '300 000', icon: Receipt, symbol: '₽' },
  { id: 'ads', key: 'ads', title: 'Реклама', subtitle: 'Введите затраты на рекламу', placeholder: '50 000', icon: TrendingUp, symbol: '₽' },
] as const;

export default function App() {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState<FormData>({
    revenue: '',
    spp: '',
    cost: '',
    ads: ''
  });

  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input automatically on step change
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [step]);

  const handleNext = () => {
    if (step < steps.length) {
      setStep(s => s + 1);
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(s => s - 1);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && formData[steps[step].key as keyof FormData]) {
      handleNext();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const key = steps[step].key as keyof FormData;
    const rawValue = e.target.value.replace(/\D/g, '');
    
    if (!rawValue) {
      setFormData(prev => ({ ...prev, [key]: '' }));
      return;
    }

    // Format with spaces for thousands
    const formatted = rawValue.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    setFormData(prev => ({ ...prev, [key]: formatted }));
  };

  const currentStepData = step < steps.length ? steps[step] : null;
  const StepIcon = currentStepData?.icon;

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-4 sm:p-8 font-sans selection:bg-amber-500/30 overflow-x-hidden text-zinc-100">
      
      {/* Decorative background gradients */}
      <div className="fixed top-0 inset-x-0 h-[500px] bg-gradient-to-b from-amber-500/5 to-transparent pointer-events-none" />
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-amber-500/5 rounded-full blur-[120px] pointer-events-none" />

      {step < steps.length ? (
        <div className="w-full max-w-xl relative z-10 flex flex-col items-center">
          
          {/* Progress & Summary */}
          <div className="w-full flex flex-col items-center gap-6 mb-12">
            <div className="w-full flex items-center gap-3 max-w-[200px]">
              {steps.map((s, i) => (
                <div 
                  key={s.id} 
                  className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${
                    i === step ? 'bg-amber-500 scale-y-125' : i < step ? 'bg-amber-500/50' : 'bg-zinc-800'
                  }`} 
                />
              ))}
            </div>

            {/* Entered Values Summary */}
            <div className="flex flex-wrap justify-center gap-2 max-w-md min-h-[32px]">
              <AnimatePresence>
                {step > 0 && steps.slice(0, step).map((s) => (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.9, y: 10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9, y: -10 }}
                    key={s.id} 
                    className="text-xs sm:text-sm bg-zinc-900/60 text-zinc-400 px-3 py-1.5 rounded-full border border-zinc-800/50 backdrop-blur-sm"
                  >
                    {s.title}: <span className="text-zinc-200 font-medium ml-1">{formData[s.key as keyof FormData]} {s.symbol}</span>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 20, filter: 'blur(4px)' }}
              animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0, x: -20, filter: 'blur(4px)' }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col items-center w-full"
            >
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-zinc-800 to-zinc-900 border border-zinc-700/50 flex items-center justify-center mb-8 shadow-2xl">
                {StepIcon && <StepIcon className="w-8 h-8 text-amber-500" />}
              </div>

              <h2 className="text-3xl sm:text-4xl font-light text-white mb-4 text-center tracking-tight">
                {currentStepData?.title}
              </h2>
              <p className="text-zinc-400 mb-12 text-center text-lg sm:text-xl">
                {currentStepData?.subtitle}
              </p>

              <div className="relative w-full max-w-sm mx-auto mb-16">
                <input
                  ref={inputRef}
                  type="text"
                  inputMode="numeric"
                  autoFocus
                  value={currentStepData ? formData[currentStepData.key as keyof FormData] : ''}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  placeholder={currentStepData?.placeholder}
                  className="w-full bg-transparent border-b-2 border-zinc-800 text-5xl sm:text-6xl text-center py-4 focus:border-amber-500 focus:outline-none transition-colors text-white placeholder:text-zinc-800 font-light px-10"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 text-2xl sm:text-3xl text-zinc-600 font-light pointer-events-none">
                  {currentStepData?.symbol}
                </div>
              </div>

              <div className="flex items-center gap-4 w-full max-w-sm">
                {step > 0 && (
                  <button
                    onClick={handleBack}
                    className="w-14 h-14 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 hover:border-zinc-700 transition-all flex-shrink-0"
                  >
                    <ArrowLeft className="w-5 h-5" />
                  </button>
                )}
                <button
                  onClick={handleNext}
                  disabled={currentStepData ? !formData[currentStepData.key as keyof FormData] : true}
                  className="flex-1 h-14 rounded-full bg-amber-500 hover:bg-amber-400 text-zinc-950 font-medium text-lg flex items-center justify-center gap-3 transition-all disabled:opacity-30 disabled:hover:bg-amber-500 shadow-[0_0_30px_-10px_rgba(245,158,11,0.5)]"
                >
                  <span>{step === steps.length - 1 ? 'Получить расчет' : 'Далее'}</span>
                  {step < steps.length - 1 && <ArrowRight className="w-5 h-5" />}
                </button>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      ) : (
        <Results 
          data={formData} 
          onReset={() => { 
            setStep(0); 
            setFormData({ revenue: '', spp: '', cost: '', ads: '' }); 
          }} 
        />
      )}
    </div>
  );
}

function Results({ data, onReset }: { data: FormData, onReset: () => void }) {
  const revenue = parseFloat(data.revenue.replace(/\s/g, '')) || 0;
  const spp = parseFloat(data.spp.replace(/\s/g, '')) || 0;
  const cost = parseFloat(data.cost.replace(/\s/g, '')) || 0;
  const ads = parseFloat(data.ads.replace(/\s/g, '')) || 0;

  // Business Logic 
  const taxBase = revenue - (revenue * (spp / 100)); // Цена реализации - СПП
  const commission = revenue * 0.46;
  const payout = revenue - commission - ads;
  const margin = revenue - commission - cost;

  return (
    <motion.div
      key="results"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 1.05 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="w-full max-w-3xl mx-auto flex flex-col items-center relative z-10"
    >
      {/* Success Icon */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.6 }}
        className="w-20 h-20 rounded-full bg-gradient-to-br from-amber-400/20 to-amber-600/10 flex items-center justify-center mb-8 border border-amber-500/20 shadow-[0_0_40px_-10px_rgba(245,158,11,0.2)]"
      >
        <CheckCircle2 className="w-10 h-10 text-amber-400" />
      </motion.div>
      
      <motion.h2 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.6 }}
        className="text-4xl sm:text-5xl font-light text-white mb-4 tracking-tight text-center"
      >
        Расчет готов
      </motion.h2>

      {/* Input Summary Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.6 }}
        className="w-full grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-12"
      >
        {steps.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.id} className="relative overflow-hidden bg-zinc-900/30 border border-zinc-800/50 rounded-3xl p-4 sm:p-5 flex flex-col items-start backdrop-blur-sm transition-all duration-300 hover:bg-zinc-900/50 hover:border-amber-500/30 group">
              {/* Decorative background icon */}
              <div className="absolute -right-4 -bottom-4 opacity-[0.03] transition-transform duration-700 group-hover:scale-110 group-hover:opacity-[0.06]">
                <Icon className="w-24 h-24" />
              </div>
              
              <div className="w-8 h-8 rounded-full bg-zinc-800/50 flex items-center justify-center mb-3">
                <Icon className="w-4 h-4 text-amber-500/80" />
              </div>
              
              <span className="text-[10px] sm:text-[11px] text-zinc-500 font-medium tracking-widest uppercase mb-1 w-full truncate">
                {s.title.replace(' (ДО СПП)', '')}
              </span>
              
              <span className="text-lg sm:text-xl text-zinc-100 font-light truncate w-full">
                {data[s.key as keyof typeof data] || '0'}
                <span className="text-zinc-600 ml-1 font-normal text-sm">{s.symbol}</span>
              </span>
            </div>
          );
        })}
      </motion.div>
      
      <motion.p 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.6 }}
        className="text-zinc-400 mb-10 text-center text-lg sm:text-xl max-w-md"
      >
        Работая с нами, вы получите следующие показатели:
      </motion.p>

      <div className="w-full grid gap-4 mb-10">
        <ResultCard 
          title="Налогооблагаемая база" 
          value={taxBase} 
          subtitle="Цена реализации - СПП" 
          delay={0.45} 
        />
        <ResultCard 
          title="Общая комиссия (46%)" 
          value={commission} 
          subtitle="ВБ + Эквайринг + Агентская комиссия" 
          delay={0.5} 
        />
        <ResultCard 
          title="К переводу от Нас" 
          value={payout} 
          subtitle="Цена реализации - Общая комиссия - Реклама" 
          highlight 
          delay={0.6} 
        />
        <ResultCard 
          title="Маржинальный доход" 
          value={margin} 
          subtitle="Цена реализации - Общая комиссия - Себестоимость" 
          highlight 
          delay={0.7} 
        />
      </div>

      <motion.a 
        href="https://t.me/your_bot_link_here" 
        target="_blank" 
        rel="noopener noreferrer"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.6 }}
        className="mb-8 w-full sm:w-auto text-center bg-amber-500 hover:bg-amber-400 text-zinc-950 font-medium text-lg py-4 px-12 rounded-full transition-all shadow-[0_0_40px_-10px_rgba(245,158,11,0.5)] hover:shadow-[0_0_50px_-5px_rgba(245,158,11,0.6)] flex items-center justify-center scale-100 hover:scale-[1.02] active:scale-[0.98]"
      >
        Давайте сотрудничать!
      </motion.a>

      <motion.button 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.9, duration: 0.6 }}
        onClick={onReset} 
        className="group flex items-center gap-3 text-zinc-400 hover:text-white transition-colors py-3 px-6 rounded-full hover:bg-zinc-900 border border-transparent hover:border-zinc-800"
      >
        <RotateCcw className="w-5 h-5 group-hover:-rotate-180 transition-transform duration-500" />
        <span className="font-medium">Выполнить новый расчет</span>
      </motion.button>
    </motion.div>
  );
}

function ResultCard({ title, value, subtitle, highlight = false, delay = 0 }: { title: string, value: number, subtitle: string, highlight?: boolean, delay?: number }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={`p-6 sm:p-8 rounded-3xl border ${
        highlight 
          ? 'bg-gradient-to-br from-zinc-800/80 to-zinc-900/80 border-amber-500/30 shadow-[0_0_30px_-10px_rgba(245,158,11,0.15)]' 
          : 'bg-zinc-900/40 border-zinc-800/50'
      } backdrop-blur-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all duration-300 hover:border-amber-500/40`}
    >
      <div className="flex-1">
        <h3 className={`text-lg sm:text-xl ${highlight ? 'text-zinc-100 font-medium' : 'text-zinc-300'}`}>
          {title}
        </h3>
        <p className="text-sm sm:text-base text-zinc-500 mt-1">
          {subtitle}
        </p>
      </div>
      <div className={`text-3xl sm:text-4xl font-light tracking-tight ${highlight ? 'text-amber-400' : 'text-white'}`}>
        {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(value)}
      </div>
    </motion.div>
  );
}
