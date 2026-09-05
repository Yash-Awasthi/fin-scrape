import React from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Download,
  Settings,
  ExternalLink,
} from 'lucide-react';

interface QuickAction {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  href?: string;
  to?: string;
  external?: boolean;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'report',
    label: 'Generate Report',
    icon: FileText,
    to: '/reports',
  },
  {
    id: 'export',
    label: 'Export Data',
    icon: Download,
    to: '/settings?tab=export',
  },
  {
    id: 'settings',
    label: 'Preferences',
    icon: Settings,
    to: '/settings',
  },
];

export const QuickActionsList: React.FC = () => {
  return (
    <div className="space-y-1">
      {QUICK_ACTIONS.map(action => {
        const content = (
          <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-olive-secondary hover:text-olive-primary hover:bg-white/[0.03] transition-colors">
            <action.icon className="w-4 h-4" />
            <span className="text-sm">{action.label}</span>
            {action.external && (
              <ExternalLink className="w-3 h-3 ml-auto opacity-50" />
            )}
          </div>
        );

        if (action.to) {
          return (
            <Link key={action.id} to={action.to}>
              {content}
            </Link>
          );
        }

        if (action.href) {
          return (
            <a
              key={action.id}
              href={action.href}
              target={action.external ? '_blank' : undefined}
              rel={action.external ? 'noopener noreferrer' : undefined}
            >
              {content}
            </a>
          );
        }

        return <div key={action.id}>{content}</div>;
      })}
    </div>
  );
};
