import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      correlationId: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error with correlation tracking
    const correlationId = Math.random().toString(36).substring(2, 15);
    
    console.error('[ErrorBoundary] React error caught:', {
      error: error.message,
      stack: error.stack,
      errorInfo: errorInfo.componentStack,
      correlationId,
      timestamp: new Date().toISOString()
    });

    this.setState({
      error,
      errorInfo,
      correlationId
    });

    // Report to error tracking service in production
    if (process.env.NODE_ENV === 'production') {
      // TODO: Send to error tracking service (e.g., Sentry, LogRocket)
    }
  }

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      correlationId: null 
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full">
            <div className="text-center mb-6">
              <div className="text-red-500 text-6xl mb-4">⚠️</div>
              <h1 className="text-3xl font-bold text-red-400 mb-2">
                Oops! Something went wrong
              </h1>
              <p className="text-gray-300">
                We encountered an unexpected error. This has been logged for investigation.
              </p>
            </div>

            {/* Error details for development */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="bg-gray-700 p-4 rounded mb-6">
                <h3 className="text-red-400 font-semibold mb-2">Error Details:</h3>
                <p className="text-sm text-gray-300 mb-2">
                  <strong>Message:</strong> {this.state.error.message}
                </p>
                {this.state.correlationId && (
                  <p className="text-sm text-gray-300 mb-2">
                    <strong>Correlation ID:</strong> {this.state.correlationId}
                  </p>
                )}
                <details className="mt-2">
                  <summary className="text-sm text-blue-400 cursor-pointer hover:text-blue-300">
                    Stack Trace
                  </summary>
                  <pre className="text-xs text-gray-400 mt-2 p-2 bg-gray-800 rounded overflow-auto max-h-40">
                    {this.state.error.stack}
                  </pre>
                </details>
                {this.state.errorInfo && (
                  <details className="mt-2">
                    <summary className="text-sm text-blue-400 cursor-pointer hover:text-blue-300">
                      Component Stack
                    </summary>
                    <pre className="text-xs text-gray-400 mt-2 p-2 bg-gray-800 rounded overflow-auto max-h-40">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={this.handleRetry}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={this.handleReload}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Reload Page
              </button>
            </div>

            {/* Support information */}
            <div className="mt-8 text-center text-sm text-gray-400">
              <p>
                If this problem persists, please contact support
                {this.state.correlationId && (
                  <span> with reference ID: <code className="text-blue-400">{this.state.correlationId}</code></span>
                )}
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;