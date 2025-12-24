#!/usr/bin/env python3
"""Simple HTTP health check server for smoke testing."""
import http.server
import socketserver
import json
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

PORT = 8080


class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for health checks."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            # Test imports
            health_status = {"status": "healthy", "checks": {}}

            try:
                import game_engine

                health_status["checks"]["game_engine"] = "ok"
            except ImportError as e:
                health_status["checks"]["game_engine"] = f"error: {e}"
                health_status["status"] = "unhealthy"

            try:
                import command_parser

                health_status["checks"]["command_parser"] = "ok"
            except ImportError as e:
                health_status["checks"]["command_parser"] = f"error: {e}"
                health_status["status"] = "unhealthy"

            try:
                import gm_handler

                health_status["checks"]["gm_handler"] = "ok"
            except ImportError as e:
                health_status["checks"]["gm_handler"] = f"error: {e}"
                health_status["status"] = "unhealthy"

            try:
                from game_engine import DiceRoller

                result, _ = DiceRoller.roll("1d20")
                if 1 <= result <= 20:
                    health_status["checks"]["dice_rolling"] = "ok"
                else:
                    health_status["checks"]["dice_rolling"] = "error: invalid result"
                    health_status["status"] = "unhealthy"
            except Exception as e:
                health_status["checks"]["dice_rolling"] = f"error: {e}"
                health_status["status"] = "unhealthy"

            response = json.dumps(health_status, indent=2)
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server():
    """Run the health check server."""
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        print(f"Health check server running on http://localhost:{PORT}/health")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")


if __name__ == "__main__":
    run_server()
