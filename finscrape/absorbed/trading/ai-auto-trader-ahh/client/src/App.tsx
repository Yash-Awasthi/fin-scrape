import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import Layout from './components/Layout';
import AuthGate from './components/AuthGate';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Strategies = lazy(() => import('./pages/Strategies'));
const Config = lazy(() => import('./pages/Config'));
const Logs = lazy(() => import('./pages/Logs'));
const Backtest = lazy(() => import('./pages/Backtest'));
const Debate = lazy(() => import('./pages/Debate'));
const Equity = lazy(() => import('./pages/Equity'));
const History = lazy(() => import('./pages/History'));
const Ranking = lazy(() => import('./pages/Ranking'));

const PageLoader = () => (
  <div className="flex items-center justify-center h-screen">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
  </div>
);

function App() {
  return (
    <AuthGate>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={
              <Suspense fallback={<PageLoader />}>
                <Dashboard />
              </Suspense>
            } />
            <Route path="backtest" element={
              <Suspense fallback={<PageLoader />}>
                <Backtest />
              </Suspense>
            } />
            <Route path="debate" element={
              <Suspense fallback={<PageLoader />}>
                <Debate />
              </Suspense>
            } />
            <Route path="equity" element={
              <Suspense fallback={<PageLoader />}>
                <Equity />
              </Suspense>
            } />
            <Route path="history" element={
              <Suspense fallback={<PageLoader />}>
                <History />
              </Suspense>
            } />
            <Route path="ranking" element={
              <Suspense fallback={<PageLoader />}>
                <Ranking />
              </Suspense>
            } />
            <Route path="strategies" element={
              <Suspense fallback={<PageLoader />}>
                <Strategies />
              </Suspense>
            } />
            <Route path="config" element={
              <Suspense fallback={<PageLoader />}>
                <Config />
              </Suspense>
            } />
            <Route path="logs" element={
              <Suspense fallback={<PageLoader />}>
                <Logs />
              </Suspense>
            } />
            {/* Catch-all: redirect non-existent paths to root */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthGate>
  );
}

export default App;
