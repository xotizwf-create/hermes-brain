import { LayoutDashboard, Briefcase, Video, Users, MessageSquare, Bot, BookOpen, Activity, Settings, Zap } from 'lucide-react';
import { cn } from '../lib/utils';
import { TabType } from '../types';

interface SidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const companyItems = [
    { id: 'analytics', label: 'Сводная аналитика', icon: LayoutDashboard },
    { id: 'wb', label: 'WB-кабинет', icon: Briefcase },
    { id: 'zoom', label: 'Зум-разговоры', icon: Video },
    { id: 'team', label: 'Команда', icon: Users },
  ];

  const agentItems = [
    { id: 'dialogs', label: 'Диалоги', icon: MessageSquare, badge: 12 },
    { id: 'agents', label: 'Агенты', icon: Bot, badge: 4 },
    { id: 'knowledge', label: 'База знаний', icon: BookOpen },
    { id: 'monitoring', label: 'Мониторинг', icon: Activity },
  ];

  const otherItems = [
    { id: 'settings', label: 'Настройки', icon: Settings },
  ];

  const renderItem = (item: any) => {
    const isActive = activeTab === item.id;
    return (
      <button
        key={item.id}
        onClick={() => onTabChange(item.id as TabType)}
        className={cn(
          "w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group",
          isActive 
            ? "bg-indigo-50 text-indigo-700" 
            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
        )}
      >
        <div className="flex items-center gap-3">
          <item.icon className={cn("w-4 h-4", isActive ? "text-indigo-600" : "text-gray-400 group-hover:text-gray-600")} />
          <span>{item.label}</span>
        </div>
        {item.badge && (
          <span className={cn(
            "text-xs px-2 py-0.5 rounded-full font-semibold",
            isActive ? "bg-indigo-100 text-indigo-700" : "bg-gray-100 text-gray-500 group-hover:bg-gray-200"
          )}>
            {item.badge}
          </span>
        )}
      </button>
    );
  };

  return (
    <aside className="w-64 bg-white border-r border-gray-200/60 flex flex-col h-screen shrink-0 relative z-10 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
      <div className="p-6 pb-2 flex items-center gap-3">
        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-inner shadow-indigo-400/20">
          <span className="text-white font-bold text-lg leading-none">A</span>
        </div>
        <span className="text-xl font-bold tracking-tight text-gray-900">Albery</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-8 scrollbar-hide">
        
        <div>
          <h3 className="px-3 text-xs font-semibold text-gray-400 tracking-wider uppercase mb-3">Компания</h3>
          <div className="space-y-1">
            {companyItems.map(renderItem)}
          </div>
        </div>

        <div>
          <h3 className="px-3 text-xs font-semibold text-indigo-400 tracking-wider uppercase mb-3">Центр Агента</h3>
          <div className="space-y-1">
            {agentItems.map(renderItem)}
          </div>
        </div>

        <div>
          <h3 className="px-3 text-xs font-semibold text-gray-400 tracking-wider uppercase mb-3">Прочее</h3>
          <div className="space-y-1">
            {otherItems.map(renderItem)}
          </div>
        </div>
      </div>
      
      <div className="p-4 border-t border-gray-100">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm">
            АН
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-900">Александр Н.</span>
            <span className="text-xs text-gray-500">Владелец</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
