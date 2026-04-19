import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  errorMessage: string | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, errorMessage: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, errorMessage: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[Guardian ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="shell shell--centered" style={{ textAlign: "center", padding: 40 }}>
          <p
            className="section-card__eyebrow"
            style={{ marginBottom: 12, letterSpacing: "0.12em" }}
          >
            Guardian of the Gulf
          </p>
          <h2 style={{ fontFamily: "Outfit, sans-serif", marginBottom: 16 }}>
            Something went wrong
          </h2>
          <p className="body-copy" style={{ maxWidth: "40ch", margin: "0 auto 24px" }}>
            {this.state.errorMessage ?? "An unexpected error occurred."}
          </p>
          <button
            className="auth-submit"
            style={{ maxWidth: 260, margin: "0 auto" }}
            onClick={() => {
              this.setState({ hasError: false, errorMessage: null });
              window.location.reload();
            }}
          >
            Reload application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
