"""Simple web handler for one-click unsubscribe from email."""

from flask import Flask, request, render_template_string
import asyncio
import os
import json
from pathlib import Path


class UnsubscribeWebHandler:
    """Handle web-based unsubscribe requests."""

    def __init__(self, port: int = 5000):
        self.port = port
        self.app = Flask(__name__)
        self.pending_file = Path.home() / '.gmail-cleaner-pending.json'
        self._setup_routes()

    def _setup_routes(self):
        """Set up Flask routes."""

        @self.app.route('/')
        def index():
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                           text-align: center; padding: 50px; background: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background: white;
                                padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    h1 { color: #667eea; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📧 No Thanks</h1>
                    <p>Web handler is running!</p>
                    <p>Click the unsubscribe button in your daily email to use this.</p>
                </div>
            </body>
            </html>
            """

        @self.app.route('/unsubscribe/<token>')
        def unsubscribe(token):
            """Handle unsubscribe request."""
            # Load pending suggestion
            if not self.pending_file.exists():
                return self._render_error("No pending suggestion found. The link may have expired.")

            try:
                with open(self.pending_file, 'r') as f:
                    data = json.load(f)

                if data.get('token') != token:
                    return self._render_error("Invalid token. The link may have expired.")

                sender_address = data.get('sender_address')

                # Trigger unsubscribe
                # Note: This will be handled by the daily cron job checking for approval
                approval_file = Path.home() / '.gmail-cleaner-approved.json'
                with open(approval_file, 'w') as f:
                    json.dump({'sender': sender_address, 'approved': True}, f)

                return self._render_success(sender_address)

            except Exception as e:
                return self._render_error(f"Error processing request: {e}")

        @self.app.route('/skip/<token>')
        def skip(token):
            """Handle skip request."""
            if not self.pending_file.exists():
                return self._render_error("No pending suggestion found.")

            try:
                with open(self.pending_file, 'r') as f:
                    data = json.load(f)

                if data.get('token') != token:
                    return self._render_error("Invalid token.")

                # Mark as skipped
                approval_file = Path.home() / '.gmail-cleaner-approved.json'
                with open(approval_file, 'w') as f:
                    json.dump({'approved': False}, f)

                return """
                <html>
                <head>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                               text-align: center; padding: 50px; background: #f5f5f5; }
                        .container { max-width: 600px; margin: 0 auto; background: white;
                                    padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                        h1 { color: #667eea; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>⏭️ Skipped</h1>
                        <p>No problem! We'll suggest a different sender tomorrow.</p>
                    </div>
                </body>
                </html>
                """

            except Exception as e:
                return self._render_error(f"Error: {e}")

    def _render_success(self, sender_address: str) -> str:
        """Render success page."""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                       text-align: center; padding: 50px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white;
                            padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                h1 {{ color: #10b981; }}
                .checkmark {{ font-size: 72px; margin: 20px 0; }}
                .sender {{ background: #f8f9fa; padding: 15px; border-radius: 6px;
                          font-family: monospace; margin: 20px 0; word-break: break-all; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="checkmark">✓</div>
                <h1>Approved!</h1>
                <p>The unsubscribe process will begin shortly for:</p>
                <div class="sender">{sender_address}</div>
                <p style="color: #6c757d;">You can close this window.</p>
            </div>
        </body>
        </html>
        """

    def _render_error(self, message: str) -> str:
        """Render error page."""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                       text-align: center; padding: 50px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white;
                            padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                h1 {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>❌ Error</h1>
                <p>{message}</p>
            </div>
        </body>
        </html>
        """

    def run(self):
        """Start the web server."""
        self.app.run(host='127.0.0.1', port=self.port, debug=False)


def start_web_server(port: int = 5000):
    """Start the web server in the background."""
    handler = UnsubscribeWebHandler(port=port)
    handler.run()
