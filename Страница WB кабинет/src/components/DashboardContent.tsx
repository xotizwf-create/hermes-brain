import { useState } from "react";
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { Info, LayoutDashboard } from "lucide-react";
import { cn } from "../lib/utils";
import { DatePicker, BrandSelect } from "./shared/FormControls";
import { RnpTab } from "./RnpTab";
import { SettingsContent } from "./SettingsContent";

const sparklineDataBase = [ {v: 10}, {v: 12}, {v: 11}, {v: 14}, {v: 10}, {v: 15}, {v: 16}, {v: 14}, {v: 18}, {v: 17}, {v: 20}, {v: 25}, {v: 22}, {v: 28} ];
const profitData = sparklineDataBase.map(d => ({ v: d.v * 1.5 + Math.random() * 5 }));
const ordersData = sparklineDataBase.map(d => ({ v: d.v + Math.random() * 2 }));
const salesData = sparklineDataBase.map(d => ({ v: d.v * 0.9 + Math.random() * 2 }));
const logisticsData = sparklineDataBase.map(d => ({ v: d.v * 0.5 + Math.random() * 2 }));
const adsData = sparklineDataBase.map(d => ({ v: d.v * 0.2 + Math.random() * 2 }));
const servicesData = sparklineDataBase.map(d => ({ v: d.v * 1.2 + Math.random() * 2 }));

const TABS = [
  "Общий дашборд",
  "РНП",
  "ОПиУ",
  "ДДС",
  "По артикулам",
  "Налоговый калькулятор",
  "Настройка"
];

const BRAND_OPTIONS = ["Все", "Alberi", "Тестовый Бренд"];

function Sparkline({ data, color }: { data: any[], color: string }) {
  const gradientId = `color-${color.replace('#', '')}`;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="v" stroke={color} strokeWidth={2} fillOpacity={1} fill={`url(#${gradientId})`} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function DashboardContent() {
  const [startDate, setStartDate] = useState('2026-03-01');
  const [endDate, setEndDate] = useState('2026-03-08');
  const [brand, setBrand] = useState('Все');
  const [activeTab, setActiveTab] = useState('Общий дашборд');

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-y-auto bg-slate-100">
      
      {/* Top Banner */}
      <div className="bg-[#f3ece7] text-slate-700 px-4 md:px-8 py-4 text-xs md:text-sm font-medium">
        WEB-отчеты дают сводную и детальную картину по маркетплейсам прямо в личном кабинете.
      </div>

      <div className="p-4 md:p-8 flex flex-col gap-6">
        
        {/* Filters */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-6 bg-white p-4 rounded-2xl shadow-sm self-start w-full sm:w-auto">
          <div className="flex flex-wrap sm:flex-nowrap items-center gap-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider hidden sm:block">Период</span>
            <DatePicker value={startDate} onChange={setStartDate} />
            <span className="text-slate-300 hidden sm:block">—</span>
            <DatePicker value={endDate} onChange={setEndDate} />
          </div>
          
          <div className="hidden sm:block w-px h-6 bg-slate-200"></div>
          
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider hidden sm:block">Бренд</span>
            <div className="w-full sm:w-auto">
              <BrandSelect value={brand} onChange={setBrand} options={BRAND_OPTIONS} />
            </div>
          </div>
        </div>

        {/* Main Area */}
        <div className="flex flex-col lg:flex-row items-start gap-6">
          
          {/* Tabs */}
          <div className="w-full lg:w-64 shrink-0 flex flex-row lg:flex-col gap-2 overflow-x-auto pb-2 lg:pb-0 scrollbar-hide">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "whitespace-nowrap lg:whitespace-normal w-auto lg:w-full text-left px-5 py-3.5 rounded-xl text-sm font-bold transition-all border",
                  activeTab === tab 
                    ? "bg-white text-brand-600 border-brand-600 shadow-md shadow-brand-500/10" 
                    : "bg-white text-slate-700 border-transparent hover:border-slate-200 shadow-sm hover:shadow"
                )}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Right Content */}
          <div className="flex-1 min-w-0 w-full flex flex-col gap-6">
            
            {activeTab === 'РНП' ? (
              <RnpTab />
            ) : activeTab === 'Настройка' ? (
              <SettingsContent />
            ) : activeTab === 'Общий дашборд' ? (
              <>
                {/* Top Row Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-4">
                  
                  {/* Card 1: Реализация */}
                  <div className="bg-white p-6 rounded-2xl shadow-sm flex flex-col border border-slate-100 transition-shadow hover:shadow-md">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">Реализация</div>
                    <div className="text-3xl font-black text-slate-900 mb-6 tracking-tight">23 604 877</div>
                    
                    <div className="h-2 w-full bg-slate-100 rounded-full flex mb-6 overflow-hidden">
                      <div className="bg-[#10b981] h-full" style={{ width: '98%' }}></div>
                      <div className="bg-[#ef4444] h-full" style={{ width: '2%' }}></div>
                    </div>
                    
                    <div className="space-y-3 text-[11px]">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#10b981] ring-4 ring-[#10b981]/10"></div>
                          <span className="text-slate-500 font-medium text-xs">Продажи</span>
                        </div>
                        <span className="font-bold text-slate-800 text-xs">23 882 233</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#ef4444] ring-4 ring-[#ef4444]/10"></div>
                          <span className="text-slate-500 font-medium text-xs">Возвраты</span>
                        </div>
                        <span className="font-bold text-slate-800 text-xs">277 357</span>
                      </div>
                    </div>
                  </div>

                  {/* Card 2: Услуги */}
                  <div className="bg-white p-6 rounded-2xl shadow-sm flex flex-col border border-slate-100 transition-shadow hover:shadow-md">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">Услуги</div>
                    <div className="flex items-baseline gap-3 mb-6">
                      <div className="text-3xl font-black text-slate-900 tracking-tight">11 316 890</div>
                      <div className="text-[11px] font-bold bg-slate-100 text-slate-500 px-2 py-1 rounded-md">48%</div>
                    </div>
                    
                    <div className="h-2 w-full bg-slate-100 rounded-full flex mb-6 overflow-hidden">
                      <div className="bg-[#f59e0b] h-full" style={{ width: '80%' }}></div>
                      <div className="bg-[#60a5fa] h-full" style={{ width: '15%' }}></div>
                      <div className="bg-[#a855f7] h-full" style={{ width: '3%' }}></div>
                      <div className="bg-[#3b82f6] h-full" style={{ width: '2%' }}></div>
                    </div>
                    
                    <div className="space-y-2.5 text-[11px]">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#f59e0b]"></div>
                          <span className="text-slate-500 font-medium text-xs">Комиссия</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 text-xs w-20 text-right">9 187 889</span>
                          <span className="text-[10px] font-bold bg-slate-50 text-slate-400 px-1.5 py-0.5 rounded w-8 text-center">39%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#60a5fa]"></div>
                          <span className="text-slate-500 font-medium text-xs">Логистика</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 text-xs w-20 text-right">1 595 939</span>
                          <span className="text-[10px] font-bold bg-slate-50 text-slate-400 px-1.5 py-0.5 rounded w-8 text-center">7%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#a855f7]"></div>
                          <span className="text-slate-500 font-medium text-xs">Реклама</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 text-xs w-20 text-right">222 717</span>
                          <span className="text-[10px] font-bold bg-slate-50 text-slate-400 px-1.5 py-0.5 rounded w-8 text-center">1%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#3b82f6]"></div>
                          <span className="text-slate-500 font-medium text-xs">Остальные</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 text-xs w-20 text-right">310 345</span>
                          <span className="text-[10px] font-bold bg-slate-50 text-slate-400 px-1.5 py-0.5 rounded w-8 text-center">1%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Card 3: Налоги и затраты */}
                  <div className="bg-white p-6 rounded-2xl shadow-sm flex flex-col border border-slate-100 transition-shadow hover:shadow-md">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">Налоги и затраты</div>
                    <div className="flex items-baseline gap-3 mb-6">
                      <div className="text-3xl font-black text-slate-900 tracking-tight">7 085 617</div>
                      <div className="text-[11px] font-bold bg-slate-100 text-slate-500 px-2 py-1 rounded-md">30%</div>
                    </div>
                    
                    <div className="h-2 w-full bg-slate-100 rounded-full flex mb-6 overflow-hidden">
                      <div className="bg-[#f97316] h-full" style={{ width: '5%' }}></div>
                      <div className="bg-[#ec4899] h-full" style={{ width: '10%' }}></div>
                      <div className="bg-[#a1a1aa] h-full" style={{ width: '85%' }}></div>
                    </div>
                    
                    <div className="space-y-2 text-[11px]">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#f97316]"></div>
                          <span className="text-slate-500 font-medium text-xs">Налог</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 text-xs w-20 text-right">183 033</span>
                          <span className="text-[10px] font-bold bg-slate-50 text-slate-400 px-1.5 py-0.5 rounded w-8 text-center">1%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#ec4899]"></div>
                          <span className="text-slate-500 font-medium text-xs">НДС к уплате</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 text-xs w-20 text-right">617 000</span>
                          <span className="text-[10px] font-bold bg-slate-50 text-slate-400 px-1.5 py-0.5 rounded w-8 text-center">3%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#a1a1aa]"></div>
                          <span className="text-slate-500 font-medium text-[11px] truncate w-24">Себестоимость продаж</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 text-xs w-20 text-right">6 285 584</span>
                          <span className="text-[10px] font-bold bg-slate-50 text-slate-400 px-1.5 py-0.5 rounded w-8 text-center">27%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#78350f]"></div>
                          <span className="text-slate-500 font-medium text-[11px] truncate w-24">Себестоимость самовыкупов</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 text-xs w-20 text-right">0</span>
                          <span className="text-[10px] font-bold bg-slate-50 text-slate-400 px-1.5 py-0.5 rounded w-8 text-center">0%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2.5">
                          <div className="w-2 h-2 rounded-full bg-[#84cc16]"></div>
                          <span className="text-slate-500 font-medium text-xs">Затраты</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 text-xs w-20 text-right">0</span>
                          <span className="text-[10px] font-bold bg-slate-50 text-slate-400 px-1.5 py-0.5 rounded w-8 text-center">0%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Card 4: Операционная прибыль */}
                  <div className="bg-gradient-to-br from-white to-slate-50 p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col relative transition-shadow hover:shadow-md">
                    <div className="flex justify-between items-center mb-2">
                      <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Операционная прибыль</div>
                      <Info className="w-4 h-4 text-slate-300 hover:text-brand-500 transition-colors cursor-help" />
                    </div>
                    <div className="text-4xl font-black text-[#10b981] mb-6 tracking-tight drop-shadow-sm">5 202 368 <span className="text-2xl text-slate-400 font-bold">₽</span></div>
                    
                    <div className="space-y-3 mb-6">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500 font-medium text-sm">Маржинальность</span>
                        <span className="font-black text-slate-800 bg-white shadow-sm border border-slate-100 px-2 py-0.5 rounded-lg">22%</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500 font-medium text-sm">Рентабельность</span>
                        <span className="font-black text-slate-800 bg-white shadow-sm border border-slate-100 px-2 py-0.5 rounded-lg">83%</span>
                      </div>
                    </div>

                    <div className="h-24 mt-auto -mx-2 -mb-2">
                      <Sparkline data={profitData} color="#10b981" />
                    </div>
                  </div>
                </div>

                {/* Bottom Row Cards */}
                <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
                  
                  {/* Заказы */}
                  <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col h-40 transition-shadow hover:shadow-md">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Заказы</div>
                    <div className="text-[10px] font-medium text-slate-400 mb-2">08.03.2026</div>
                    <div className="text-xl font-black text-slate-900 mb-1 tracking-tight">29 190 647</div>
                    <div className="text-[11px] font-bold text-[#ef4444] mb-2">-16% за день</div>
                    <div className="h-12 mt-auto -mx-2 -mb-2">
                      <Sparkline data={ordersData} color="#f97316" />
                    </div>
                  </div>

                  {/* Продажи */}
                  <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col h-40 transition-shadow hover:shadow-md">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Продажи</div>
                    <div className="text-[10px] font-medium text-slate-400 mb-2">08.03.2026</div>
                    <div className="text-xl font-black text-slate-900 mb-1 tracking-tight">23 882 233</div>
                    <div className="text-[11px] font-bold text-[#ef4444] mb-2">-18% за день</div>
                    <div className="h-12 mt-auto -mx-2 -mb-2">
                      <Sparkline data={salesData} color="#10b981" />
                    </div>
                  </div>

                  {/* Логистика */}
                  <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col h-40 transition-shadow hover:shadow-md">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Логистика</div>
                    <div className="text-[10px] font-medium text-slate-400 mb-2">08.03.2026</div>
                    <div className="text-xl font-black text-slate-900 mb-1 tracking-tight">1 595 939</div>
                    <div className="text-[11px] font-bold text-[#10b981] mb-2">-13% за день</div>
                    <div className="h-12 mt-auto -mx-2 -mb-2">
                      <Sparkline data={logisticsData} color="#3b82f6" />
                    </div>
                  </div>

                  {/* Реклама */}
                  <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col h-40 transition-shadow hover:shadow-md">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Реклама</div>
                    <div className="text-[10px] font-medium text-slate-400 mb-2">08.03.2026</div>
                    <div className="text-xl font-black text-slate-900 mb-1 tracking-tight">222 717</div>
                    <div className="text-[11px] font-bold text-[#10b981] mb-2">-2% за день</div>
                    <div className="h-12 mt-auto -mx-2 -mb-2">
                      <Sparkline data={adsData} color="#a855f7" />
                    </div>
                  </div>

                  {/* Все услуги */}
                  <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col h-40 transition-shadow hover:shadow-md">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Все услуги</div>
                    <div className="text-[10px] font-medium text-slate-400 mb-2">08.03.2026</div>
                    <div className="text-xl font-black text-slate-900 mb-1 tracking-tight">11 316 890</div>
                    <div className="text-[11px] font-bold text-[#10b981] mb-2">-18% за день</div>
                    <div className="h-12 mt-auto -mx-2 -mb-2">
                      <Sparkline data={servicesData} color="#3b82f6" />
                    </div>
                  </div>

                </div>
              </>
            ) : (
              <div className="bg-white p-12 rounded-2xl shadow-sm border border-slate-100 flex flex-col items-center justify-center text-center">
                <LayoutDashboard className="w-16 h-16 text-slate-200 mb-4" />
                <h2 className="text-xl font-bold text-slate-900 mb-2">Раздел в разработке</h2>
                <p className="text-slate-500">Вкладка "{activeTab}" будет доступна в ближайшем обновлении.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
