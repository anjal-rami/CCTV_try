import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ShieldAlert, RefreshCw } from 'lucide-react';

interface Props {
  children?: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught component error:', error, errorInfo);
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-xl mx-auto my-8 shadow-2xl space-y-4 text-center backdrop-blur">
          <div className="w-14 h-14 bg-amber-950/60 border border-amber-800 rounded-full flex items-center justify-center mx-auto text-amber-400">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-wide uppercase">
              {this.props.fallbackTitle || 'Isolated Panel Rendering Fallback'}
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              An isolated runtime rendering exception occurred within this panel. The rest of the platform remains active and stable.
            </p>
          </div>
          {this.state.error && (
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-left">
              <code className="text-[11px] font-mono text-amber-300 block truncate">
                {this.state.error.toString()}
              </code>
            </div>
          )}
          <button
            onClick={this.handleReset}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-xl text-xs font-semibold border border-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Panel State</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
