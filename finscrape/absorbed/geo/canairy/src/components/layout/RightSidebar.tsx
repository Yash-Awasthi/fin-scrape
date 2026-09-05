import React from 'react';
import { SignalsList } from '../sidebar/SignalsList';
import { DomainStatusList } from '../sidebar/DomainStatusList';

export const RightSidebar: React.FC = () => {
  return (
    <div className="flex flex-col h-full">
      {/* News Headlines */}
      <section className="p-4 border-b border-olive">
        <h3 className="text-xs font-medium text-olive-tertiary uppercase tracking-wider mb-3">
          News
        </h3>
        <SignalsList />
      </section>

      {/* Domain Status */}
      <section className="p-4 flex-1">
        <h3 className="text-xs font-medium text-olive-tertiary uppercase tracking-wider mb-3">
          Domain Status
        </h3>
        <DomainStatusList />
      </section>
    </div>
  );
};
