/**
 * React Error Boundary Component with fallback UI and error reporting
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetKeys?: Array<string | number>;
  resetOnPropsChange?: boolean;
  isolate?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

export class ErrorBoundary extends Component<Props, State> {
  private resetTimeoutId: number | null = null;
  private errorCounter = 0;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.errorCounter++;
    
    // Log to console in development
    if (import.meta.env.DEV) {
      console.error('Error Boundary caught an error:', error, errorInfo);
    }

    // Update state with error details
    this.setState({
      errorInfo,
      errorCount: this.errorCounter
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Report to error tracking service
    this.reportError(error, errorInfo);

    // Auto-reset after 10 seconds if error count is low
    if (this.errorCounter <= 3) {
      this.resetTimeoutId = window.setTimeout(() => {
        this.resetErrorBoundary();
      }, 10000);
    }
  }

  componentDidUpdate(prevProps: Props): void {
    const { resetKeys, resetOnPropsChange } = this.props;
    const { hasError } = this.state;
    
    // Reset on prop changes if specified
    if (hasError && prevProps.resetKeys !== resetKeys) {
      if (resetKeys?.some((key, idx) => key !== prevProps.resetKeys?.[idx])) {
        this.resetErrorBoundary();
      }
    }
    
    if (hasError && resetOnPropsChange && prevProps.children !== this.props.children) {
      this.resetErrorBoundary();
    }
  }

  componentWillUnmount(): void {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  private reportError(error: Error, errorInfo: ErrorInfo): void {
    // Send to error tracking service (e.g., Sentry, LogRocket)
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent
    };

    // In production, send to error tracking service
    if (import.meta.env.PROD) {
      // Example: Send to your error tracking endpoint
      fetch('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorReport)
      }).catch(console.error);
    }
  }

  private resetErrorBoundary = (): void => {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
      this.resetTimeoutId = null;
    }

    this.errorCounter = 0;
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    });
  };

  private handleGoHome = (): void => {
    window.location.href = '/';
  };

  render(): ReactNode {
    const { hasError, error, errorCount } = this.state;
    const { children, fallback, isolate } = this.props;

    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Isolated error boundary shows minimal UI
      if (isolate) {
        return (
          <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
            <p className="text-red-400 text-sm">
              Something went wrong in this section.
            </p>
            <button
              onClick={this.resetErrorBoundary}
              className="mt-2 text-xs text-red-300 hover:text-red-200 underline"
            >
              Try again
            </button>
          </div>
        );
      }

      // Full error boundary UI — dark theme matching app
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#0A0A0C] px-4">
          <div className="max-w-md w-full">
            <div className="glass-card p-8">
              <div className="flex items-center justify-center w-16 h-16 mx-auto bg-red-500/10 rounded-full border border-red-500/20">
                <AlertTriangle className="w-8 h-8 text-red-400" />
              </div>

              <h1 className="mt-4 text-2xl font-bold text-center text-white">
                Something went wrong
              </h1>

              <p className="mt-2 text-center text-white/30">
                {errorCount > 3
                  ? "We're experiencing persistent issues. Please try again later."
                  : "An unexpected error occurred. The issue has been reported."}
              </p>

              {import.meta.env.DEV && error && (
                <details className="mt-4 p-4 bg-white/[0.03] rounded-lg border border-white/[0.04]">
                  <summary className="cursor-pointer text-sm font-medium text-white/50">
                    Error Details (Development Only)
                  </summary>
                  <pre className="mt-2 text-xs text-white/20 overflow-auto max-h-48">
                    {error.message}
                    {'\n\n'}
                    {error.stack}
                  </pre>
                </details>
              )}

              <div className="mt-6 space-y-3">
                <button
                  onClick={this.resetErrorBoundary}
                  className="w-full flex items-center justify-center px-4 py-2.5 bg-white/10 text-white rounded-xl hover:bg-white/15 transition-colors font-medium"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </button>

                <button
                  onClick={this.handleGoHome}
                  className="w-full flex items-center justify-center px-4 py-2.5 bg-white/5 text-white/50 rounded-xl hover:bg-white/[0.08] transition-colors font-medium"
                >
                  <Home className="w-4 h-4 mr-2" />
                  Go to Dashboard
                </button>
              </div>

              {errorCount > 1 && (
                <p className="mt-4 text-xs text-center text-white/20">
                  Error occurred {errorCount} times
                </p>
              )}
            </div>
          </div>
        </div>
      );
    }

    return children;
  }
}

// HOC for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
): React.ComponentType<P> {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

// Hook for error handling
export function useErrorHandler() {
  return (error: Error) => {
    throw error; // This will be caught by the nearest error boundary
  };
}