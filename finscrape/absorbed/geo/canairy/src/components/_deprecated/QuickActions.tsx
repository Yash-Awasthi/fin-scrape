import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, FileText, Phone, Printer, Share2, MessageCircle } from 'lucide-react';
import { canairyMessages } from '../../content/canairy-messages';
import { cn } from '../../utils/cn';

interface QuickActionsProps {
  status: 'allGood' | 'attention' | 'action';
}

export const QuickActions: React.FC<QuickActionsProps> = ({ status }) => {
  const actions = canairyMessages.actions[status === 'allGood' ? 'green' : status === 'attention' ? 'amber' : 'red'];

  const quickButtons = [
    {
      icon: FileText,
      label: 'Family Plan',
      action: () => console.log('Open family plan'),
      color: 'bg-canairy-teal text-white',
    },
    {
      icon: Phone,
      label: 'Contacts',
      action: () => console.log('Open contacts'),
      color: 'bg-canairy-green text-white',
    },
    {
      icon: Printer,
      label: 'Print Checklist',
      action: () => window.print(),
      color: 'bg-canairy-yellow text-canairy-charcoal',
    },
    {
      icon: Share2,
      label: 'Share',
      action: () => console.log('Share'),
      color: 'bg-canairy-amber text-canairy-charcoal',
    },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Quick Action Buttons */}
      <motion.div
        className="card-canairy"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <h3 className="text-lg font-bold text-canairy-charcoal mb-4">
          Quick Actions
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {quickButtons.map((button, index) => (
            <motion.button
              key={button.label}
              className={cn(
                "flex flex-col items-center gap-2 p-4 rounded-xl transition-all duration-200",
                button.color,
                "hover:scale-105 hover:shadow-feather"
              )}
              onClick={button.action}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <button.icon className="w-6 h-6" />
              <span className="text-sm font-medium">{button.label}</span>
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Today's Actions */}
      <motion.div
        className="card-canairy"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-canairy-charcoal">
            {actions.title}
          </h3>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <CheckCircle className="w-5 h-5 text-canairy-green" />
          </motion.div>
        </div>
        <div className="space-y-2">
          {actions.items.slice(0, 3).map((item, index) => (
            <motion.label
              key={index}
              className="checklist-item cursor-pointer"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <input
                type="checkbox"
                className="checklist-checkbox"
              />
              <span className="text-sm text-canairy-charcoal">{item}</span>
            </motion.label>
          ))}
        </div>
        <button className="btn-canairy btn-primary-canairy w-full mt-4">
          <MessageCircle className="w-4 h-4" />
          <span>See All Actions</span>
        </button>
      </motion.div>
    </div>
  );
};