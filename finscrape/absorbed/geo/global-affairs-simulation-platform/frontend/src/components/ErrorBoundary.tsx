import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  /** 当 resetKey 变化时自动清除错误状态（用于路由切换） */
  resetKey?: string
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo)
    this.setState({ errorInfo })
  }

  // resetKey 变化时（路由跳转）自动重置
  componentDidUpdate(prevProps: Props) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.hasError) {
      this.setState({ hasError: false, error: null, errorInfo: null })
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="max-w-sm w-full bg-surface-900 border border-surface-700 rounded-xl p-6 text-center">
            <svg className="w-12 h-12 mx-auto text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h2 className="text-lg font-semibold text-white mb-2">出现了意外错误</h2>
            <p className="text-slate-400 text-sm mb-5">应用程序遇到了问题，请尝试刷新页面或返回上一页。</p>

            {this.state.error && (
              <details className="mb-5 text-left bg-surface-800 rounded-lg p-3">
                <summary className="cursor-pointer text-slate-400 text-xs font-medium mb-1">
                  错误详情 (开发者)
                </summary>
                <pre className="text-xs text-red-400 overflow-auto max-h-32 whitespace-pre-wrap mt-2">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}

            <div className="flex gap-3 justify-center">
              <button
                onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
                className="px-5 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-lg text-sm font-medium transition-colors">
                重试
              </button>
              <button
                onClick={() => window.history.back()}
                className="px-5 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 rounded-lg text-sm font-medium transition-colors">
                返回上页
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
