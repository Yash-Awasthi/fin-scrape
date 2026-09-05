import { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useStore } from './store';
import { wsService } from './services/api';
import { PageSkeleton } from './components/LoadingSkeleton';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AppShell } from './components/layout/AppShell';

// Lazy-loaded pages for code splitting
const Landing = lazy(() => import('./pages/Landing').then(m => ({ default: m.Landing })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const Indicators = lazy(() => import('./pages/Indicators').then(m => ({ default: m.Indicators })));
const IndicatorDetails = lazy(() => import('./pages/IndicatorDetails').then(m => ({ default: m.IndicatorDetails })));
const FamilyActionPlan = lazy(() => import('./pages/FamilyActionPlan').then(m => ({ default: m.FamilyActionPlan })));
const News = lazy(() => import('./pages/News').then(m => ({ default: m.News })));
const Analytics = lazy(() => import('./pages/Analytics').then(m => ({ default: m.Analytics })));
const Alerts = lazy(() => import('./pages/Alerts').then(m => ({ default: m.Alerts })));
const Reports = lazy(() => import('./pages/Reports').then(m => ({ default: m.Reports })));
const Settings = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })));
const NotFound = lazy(() => import('./pages/NotFound').then(m => ({ default: m.NotFound })));

function App() {
  const { refreshAll, updateIndicator } = useStore();

  useEffect(() => {
    // Initial data fetch (includes synthesis)
    refreshAll();

    // Set up WebSocket connection
    wsService.connect();

    // Subscribe to WebSocket events
    wsService.on('indicator:update', (data: unknown) => {
      const payload = data as { id: string };
      updateIndicator(payload.id, payload);
    });

    wsService.on('hopi:update', () => {
      refreshAll();
    });

    // Set up polling interval - refresh all data including synthesis
    const interval = setInterval(() => {
      refreshAll();
    }, 60000);

    return () => {
      clearInterval(interval);
      wsService.disconnect();
    };
  }, []);

  return (
    <ErrorBoundary>
      <Router>
        <Suspense fallback={<PageSkeleton />}>
          <Routes>
            {/* Landing page - standalone, no shell */}
            <Route path="/" element={<Landing />} />

            {/* All pages inside the shared shell with sidebar + header */}
            <Route element={<AppShell />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/indicators" element={<Indicators />} />
              <Route path="/indicator/:id" element={<IndicatorDetails />} />
              <Route path="/action-plan" element={<FamilyActionPlan />} />
              <Route path="/news" element={<News />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
