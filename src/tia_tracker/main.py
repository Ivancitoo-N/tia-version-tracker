"""Main Flask application for TIA Version Tracker."""

from pathlib import Path
from flask import Flask, render_template
from flask_cors import CORS

from .config import settings
from .routes.api import api_bp


def create_app():
    """Create and configure the Flask application.

    Returns:
        Flask application instance
    """
    # Get the project root directory (where templates/ and static/ are located)
    package_dir = Path(__file__).parent.parent.parent
    template_dir = package_dir / "templates"
    static_dir = package_dir / "static"
    
    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir)
    )

    # Configuration
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_size

    # Enable CORS
    CORS(app)

    # Register blueprints
    app.register_blueprint(api_bp)

    # Web routes
    @app.route("/")
    def index():
        """Home page."""
        return render_template("index.html")

    @app.route("/comparison")
    def comparison():
        """Comparison results page."""
        return render_template("comparison.html")

    return app


def main():
    """Entry point for running the application."""
    app = create_app()
    app.run(host=settings.host, port=settings.port, debug=settings.debug)


if __name__ == "__main__":
    main()
