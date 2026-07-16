import { useState, useRef, useEffect } from 'react';
import { Search, Image as ImageIcon } from 'lucide-react';
import { cn } from '../lib/utils';

// Mock data
const ARTICLES = [
  { id: '1', article: 'ART-12345', name: 'Футболка базовая белая оверсайз', photo: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=150&h=150&fit=crop' },
  { id: '2', article: 'ART-98765', name: 'Джинсы wide leg синие классические', photo: 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=150&h=150&fit=crop' },
  { id: '3', article: 'ART-45678', name: 'Кроссовки летние сетка беговые', photo: 'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=150&h=150&fit=crop' },
  { id: '4', article: 'ART-11223', name: 'Худи унисекс черное базовое', photo: 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=150&h=150&fit=crop' },
];

const DATES = ["20.06","19.06","18.06","17.06","16.06","15.06","14.06","13.06","12.06","11.06","10.06","09.06","08.06","07.06"];

const PLAN_FACT_METRICS = [
  { name: 'План заказов, шт', total: '131 шт', values: ["131 шт","131 шт","131 шт","131 шт","131 шт","131 шт","131 шт","131 шт","131 шт","131 шт","131 шт","131 шт","131 шт","131 шт"] },
  { name: 'Факт заказов, шт', total: '426 шт', values: ["107 шт","103 шт","109 шт","107 шт","107 шт","103 шт","109 шт","107 шт","107 шт","103 шт","109 шт","107 шт","107 шт","103 шт"] },
  { name: '% выполнения плана', total: '81,29%', values: ["81,68%","78,63%","83,21%","81,68%","81,68%","78,63%","83,21%","81,68%","81,68%","78,63%","83,21%","81,68%","81,68%","78,63%"], highlight: true },
  { name: 'План заказов, шт. накопительный', total: '-', values: ["524 шт","393 шт","262 шт","131 шт","524 шт","393 шт","262 шт","131 шт","524 шт","393 шт","262 шт","131 шт","524 шт","393 шт"] },
  { name: 'Факт заказов, шт. накопительный', total: '-', values: ["426 шт","319 шт","216 шт","107 шт","426 шт","319 шт","216 шт","107 шт","426 шт","319 шт","216 шт","107 шт","426 шт","319 шт"] },
  { name: '% выполнения плана накопительный', total: '-', values: ["81,30%","81,17%","82,44%","81,68%","81,30%","81,17%","82,44%","81,68%","81,30%","81,17%","82,44%","81,68%","81,30%","81,17%"], highlight: true },
  { name: 'План заказов, руб', total: '1 200 000 ₽', values: ["300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽","300 000 ₽"] },
  { name: 'Факт заказов, руб', total: '1 866 088 ₽', values: ["473 406 ₽","447 630 ₽","474 144 ₽","470 908 ₽","473 406 ₽","447 630 ₽","474 144 ₽","470 908 ₽","473 406 ₽","447 630 ₽","474 144 ₽","470 908 ₽","473 406 ₽","447 630 ₽"] },
  { name: '% выполнения плана', total: '155,5%', values: ["157,8%","149,2%","158,0%","156,9%","157,8%","149,2%","158,0%","156,9%","157,8%","149,2%","158,0%","156,9%","157,8%","149,2%"], highlight: true },
];

const MAIN_METRICS = [
  { name: 'Заказы, шт', total: '85 шт', values: ["109 шт","103 шт","109 шт","107 шт","109 шт","103 шт","109 шт","107 шт","109 шт","103 шт","109 шт","107 шт","109 шт","103 шт"] },
  { name: 'Заказы, руб', total: '362 900,60 ₽', values: ["474 403,70 ₽","447 630,70 ₽","474 144,40 ₽","470 908,70 ₽","474 403,70 ₽","447 630,70 ₽","474 144,40 ₽","470 908,70 ₽","474 403,70 ₽","447 630,70 ₽","474 144,40 ₽","470 908,70 ₽","474 403,70 ₽","447 630,70 ₽"] },
  { name: 'Раздачи, шт (по дате заказа)', total: '0 шт', values: ["0 шт","0 шт","0 шт","0 шт","0 шт","0 шт","0 шт","0 шт","0 шт","0 шт","0 шт","0 шт","0 шт","0 шт"] },
  { name: '% Выкупа', total: '21,35%', values: ["21,10%","21,36%","21,10%","22,43%","21,10%","21,36%","21,10%","22,43%","21,10%","21,36%","21,10%","22,43%","21,10%","21,36%"], highlight: true },
  { name: 'Продажи, шт. (прогнозные)', total: '18 шт', values: ["23 шт","22 шт","23 шт","24 шт","23 шт","22 шт","23 шт","24 шт","23 шт","22 шт","23 шт","24 шт","23 шт","22 шт"] },
  { name: 'Продажи, руб (прогнозные)', total: '77 551,86 ₽', values: ["99 812,98 ₽","95 360,42 ₽","99 889,72 ₽","105 312,22 ₽","99 812,98 ₽","95 360,42 ₽","99 889,72 ₽","105 312,22 ₽","99 812,98 ₽","95 360,42 ₽","99 889,72 ₽","105 312,22 ₽","99 812,98 ₽","95 360,42 ₽"] },
  { name: 'Затраты РК, руб', total: '10 366,25 ₽', values: ["12 101,49 ₽","9 250,20 ₽","9 351,48 ₽","10 749,73 ₽","12 101,49 ₽","9 250,20 ₽","9 351,48 ₽","10 749,73 ₽","12 101,49 ₽","9 250,20 ₽","9 351,48 ₽","10 749,73 ₽","12 101,49 ₽","9 250,20 ₽"], bad: true },
  { name: 'ДРР РК, %', total: '19,47%', values: ["15,35%","12,37%","14,12%","11,11%","15,35%","12,37%","14,12%","11,11%","15,35%","12,37%","14,12%","11,11%","15,35%","12,37%"] },
  { name: 'ДРР ко всем заказам, %', total: '2,96%', values: ["2,55%","2,07%","1,97%","2,28%","2,55%","2,07%","1,97%","2,28%","2,55%","2,07%","1,97%","2,28%","2,55%","2,07%"] },
  { name: 'ДРР к продажам, %', total: '13,89%', values: ["12,12%","9,70%","9,36%","10,21%","12,12%","9,70%","9,36%","10,21%","12,12%","9,70%","9,36%","10,21%","12,12%","9,70%"] },
  { name: 'Оборачиваемость склада, дн.', total: '57', values: ["50","50","49","50","50","50","49","50","50","50","49","50","50","50"], good: true },
  { name: 'Остаток закончится WB', total: '-', values: ["8.8.2026","6.8.2026","5.8.2026","4.8.2026","8.8.2026","6.8.2026","5.8.2026","4.8.2026","8.8.2026","6.8.2026","5.8.2026","4.8.2026","8.8.2026","6.8.2026"] },
  { name: 'К перечислению на р/сч, руб (прогнозное)', total: '28 608,85 ₽', values: ["37 914,17 ₽","39 194,61 ₽","40 860,23 ₽","43 294,58 ₽","37 914,17 ₽","39 194,61 ₽","40 860,23 ₽","43 294,58 ₽","37 914,17 ₽","39 194,61 ₽","40 860,23 ₽","43 294,58 ₽","37 914,17 ₽","39 194,61 ₽"] },
  { name: 'Опер. прибыль на единицу, руб (прогнозная)', total: '8 643,70 ₽', values: ["12 705,17 ₽","14 980,61 ₽","15 521,23 ₽","16 960,58 ₽","12 705,17 ₽","14 980,61 ₽","15 521,23 ₽","16 960,58 ₽","12 705,17 ₽","14 980,61 ₽","15 521,23 ₽","16 960,58 ₽","12 705,17 ₽","14 980,61 ₽"], good: true },
  { name: 'Прибыль на единицу, руб (прогнозная)', total: '438,21 ₽', values: ["552,40 ₽","680,94 ₽","674,84 ₽","706,69 ₽","552,40 ₽","680,94 ₽","674,84 ₽","706,69 ₽","552,40 ₽","680,94 ₽","674,84 ₽","706,69 ₽","552,40 ₽","680,94 ₽"] },
  { name: 'Рентабельность, %', total: '10,22%', values: ["12,73%","15,71%","15,54%","16,11%","12,73%","15,71%","15,54%","16,11%","12,73%","15,71%","15,54%","16,11%","12,73%","15,71%"], highlight: true },
  { name: 'ROI, %', total: '39,83%', values: ["50,40%","61,87%","61,25%","64,41%","50,40%","61,87%","61,25%","64,41%","50,40%","61,87%","61,25%","64,41%","50,40%","61,87%"] },
];

export function RnpTab() {
  const [search, setSearch] = useState('');
  const [selectedArticle, setSelectedArticle] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsSearching(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredArticles = ARTICLES.filter(a => 
    a.article.toLowerCase().includes(search.toLowerCase()) || 
    a.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6 w-full max-w-full">
      {/* Smart Search */}
      <div className="bg-white p-6 md:p-8 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900 mb-1">Аналитика по артикулу (РНП)</h2>
          <p className="text-sm font-medium text-slate-500">Найдите нужный товар для детального анализа метрик</p>
        </div>
        
        <div className="relative max-w-xl" ref={searchRef}>
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-slate-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-11 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all shadow-sm"
            placeholder="Введите артикул или название (например, ART-12345)..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setIsSearching(true);
            }}
            onFocus={() => {
              setIsSearching(true);
            }}
          />
          {isSearching && (
            <div className="absolute z-50 w-full mt-2 bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
              {filteredArticles.length > 0 ? (
                <ul className="max-h-80 overflow-auto divide-y divide-slate-100">
                  {filteredArticles.map((article) => (
                    <li key={article.id}>
                      <button
                        className="w-full flex items-center gap-4 px-4 py-3 hover:bg-slate-50 transition-colors text-left"
                        onClick={() => {
                          setSelectedArticle(article);
                          setSearch(article.article);
                          setIsSearching(false);
                        }}
                      >
                        <div className="w-12 h-12 rounded-lg overflow-hidden shrink-0 border border-slate-200 bg-white shadow-sm flex items-center justify-center">
                          {article.photo ? (
                            <img src={article.photo} alt={article.name} className="w-full h-full object-cover" />
                          ) : (
                            <ImageIcon className="w-5 h-5 text-slate-400" />
                          )}
                        </div>
                        <div>
                          <div className="font-bold text-slate-900 mb-0.5">{article.article}</div>
                          <div className="text-xs text-slate-500 font-medium line-clamp-1">{article.name}</div>
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="px-4 py-8 text-center flex flex-col items-center justify-center gap-2">
                  <Search className="w-8 h-8 text-slate-300" />
                  <div className="text-sm text-slate-500 font-medium">Ничего не найдено</div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Selected Article Info */}
        {selectedArticle && (
          <div className="flex items-center gap-6 pt-6 border-t border-slate-100 mt-2 animate-in fade-in duration-500">
             <div className="w-28 h-28 rounded-2xl overflow-hidden shrink-0 border border-slate-200 shadow-md bg-white flex items-center justify-center p-1">
                <div className="w-full h-full rounded-xl overflow-hidden bg-slate-50 flex items-center justify-center">
                  {selectedArticle.photo ? (
                    <img src={selectedArticle.photo} alt={selectedArticle.name} className="w-full h-full object-cover" />
                  ) : (
                    <ImageIcon className="w-8 h-8 text-slate-300" />
                  )}
                </div>
             </div>
             <div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-brand-50 text-brand-600 text-[10px] font-bold uppercase tracking-wider mb-3">
                  Выбранный товар
                </div>
                <div className="text-3xl font-black text-slate-900 mb-1.5 tracking-tight">{selectedArticle.article}</div>
                <div className="text-sm font-medium text-slate-500 max-w-md">{selectedArticle.name}</div>
             </div>
          </div>
        )}
      </div>

      {/* Metrics Tables */}
      {selectedArticle && (
        <div className="flex flex-col gap-6 animate-in slide-in-from-bottom-4 fade-in duration-500">
          <MetricsTable title="ПЛАН / ФАКТ" metrics={PLAN_FACT_METRICS} dates={DATES} titleColor="bg-slate-800 text-white" />
          <MetricsTable title="ОСНОВНЫЕ МЕТРИКИ" metrics={MAIN_METRICS} dates={DATES} titleColor="bg-[#8b5cf6] text-white" />
        </div>
      )}
    </div>
  );
}

function MetricsTable({ title, metrics, dates, titleColor }: { title: string, metrics: any[], dates: string[], titleColor: string }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
      <div className={cn("px-6 py-4 font-black text-sm tracking-widest uppercase shrink-0", titleColor)}>
        {title}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse whitespace-nowrap min-w-[800px]">
          <thead className="bg-brand-50 border-y border-brand-100">
            <tr>
              <th className="px-6 py-4 text-[10px] font-bold text-brand-700 uppercase tracking-wider border-b border-brand-100 w-48 text-center sticky left-0 z-10 bg-brand-50">
                Итого / Ср.
              </th>
              <th className="px-6 py-4 text-[10px] font-bold text-brand-700 uppercase tracking-wider border-b border-brand-100 min-w-[280px] sticky left-48 z-10 bg-brand-50 shadow-[1px_0_0_0_#eef2ff]">
                Показатель
              </th>
              {dates.map((date, i) => (
                <th key={i} className="px-6 py-4 text-[11px] font-black text-brand-800 uppercase tracking-wider border-b border-brand-100 text-right">
                  {date}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="text-sm divide-y divide-slate-100">
            {metrics.map((row, idx) => (
              <tr key={idx} className="group hover:bg-slate-50/80 transition-colors">
                <td className="px-6 py-3 font-bold text-slate-900 text-center border-r border-slate-100 bg-white group-hover:bg-slate-50/80 transition-colors sticky left-0 z-10">
                  {row.total}
                </td>
                <td className="px-6 py-3 font-medium text-slate-700 border-r border-slate-100 sticky left-48 z-10 bg-white group-hover:bg-slate-50/80 transition-colors shadow-[1px_0_0_0_#f1f5f9]">
                  {row.name}
                </td>
                {row.values.map((val: string, i: number) => (
                  <td 
                    key={i} 
                    className={cn(
                      "px-6 py-3 text-right font-medium transition-colors",
                      row.highlight && "bg-[#f0f9ff] text-[#0284c7] group-hover:bg-[#e0f2fe]",
                      row.bad && "bg-[#fef2f2] text-[#dc2626] group-hover:bg-[#fee2e2]",
                      row.good && "bg-[#f0fdf4] text-[#16a34a] group-hover:bg-[#dcfce7]",
                      !row.highlight && !row.bad && !row.good && "text-slate-600 group-hover:text-slate-900"
                    )}
                  >
                    {val}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
