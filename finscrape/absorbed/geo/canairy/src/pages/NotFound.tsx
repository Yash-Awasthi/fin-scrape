import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';

export const NotFound: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="text-8xl font-bold text-white/5 mb-4">404</div>
        <h1 className="text-2xl font-display font-semibold text-white mb-2">Page Not Found</h1>
        <p className="text-white/30 mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={() => window.history.back()}
            className="btn btn-secondary"
          >
            <ArrowLeft className="w-4 h-4" />
            Go Back
          </button>
          <Link to="/dashboard" className="btn btn-primary">
            <Home className="w-4 h-4" />
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
};
