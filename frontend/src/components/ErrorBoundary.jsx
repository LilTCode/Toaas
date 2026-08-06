import { Component } from "react";

/**
 * Catches render-time exceptions in a subtree.
 *
 * Without this, any error thrown while rendering unmounts the whole React tree
 * and the user sees a blank page with no explanation. Network failures are
 * already handled inside the pages themselves; this is the last resort for
 * everything else.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error, info) {
    console.error("Unhandled render error:", error, info);
  }

  retry = () => this.setState({ failed: false });

  render() {
    if (!this.state.failed) return this.props.children;

    return (
      <div className="grid min-h-[320px] place-items-center rounded-3xl border-[3px] border-black bg-white p-10 text-center shadow-[8px_8px_0_0_#000]">
        <div>
          <p className="text-lg font-black text-black">
            {this.props.title || "Something went wrong"}
          </p>
          <p className="mt-2 max-w-sm text-sm font-bold text-gray-600">
            {this.props.message || "Please try again in a moment."}
          </p>
          <button
            onClick={this.retry}
            className="mt-5 rounded-xl border-[2px] border-black bg-black px-5 py-2.5 text-sm font-black text-white shadow-[3px_3px_0_0_#000] transition-all active:shadow-none"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }
}
