# TIA Version Tracker

A web application for tracking and comparing TIA Portal project versions by analyzing `.zap15`/`.zap20` archive files.

## Features

- 📦 **Extract** metadata from TIA Portal `.zap15`/`.zap20` archive files (V15-V20 supported)
- 💾 **Store** version snapshots with timestamps and operator information
- 🔍 **Compare** different snapshots to detect changes
  - ✅ New tags (highlighted in green)
  - ⚠️ Modified tags (highlighted in yellow)
  - ❌ Deleted tags (highlighted in red)
- 📄 **Generate** professional PDF reports
- 🎨 **Visualize** differences in clean, dynamic tables

## Installation

### Prerequisites

- Python 3.11 or higher
- pip

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
copy .env.example .env
```

4. Initialize the database:
```bash
python -m src.tia_tracker.database.db_manager init
```

## Usage

### Quick Start (Recommended)

Double-click `start.bat` or run:

```bash
start.bat
```

This automatically:
- Checks and installs dependencies
- Initializes the database if needed
- Starts the application server

### Manual Start

```bash
python -m src.tia_tracker.main
```

The application will be available at `http://localhost:5000`

### Upload a Snapshot

1. Navigate to the home page
2. Create a new project or select an existing one
3. Upload a `.zap15` or `.zap20` file (depending on your TIA Portal version)
4. Enter the operator name
5. Click "Upload Snapshot"

### Compare Snapshots

1. Select two snapshots from the list
2. Click "Compare Snapshots"
3. View the comparison results in dynamic tables
4. Download a PDF report if needed

## Project Structure

```
tia-version-tracker/
├── src/
│   └── tia_tracker/
│       ├── routes/          # API endpoints
│       ├── services/        # Business logic
│       ├── models/          # Database models
│       ├── utils/           # Utility functions
│       ├── main.py          # Application entry point
│       └── config.py        # Configuration
├── static/                  # Frontend assets
├── templates/               # HTML templates
├── database/                # SQLite database
├── uploads/                 # Temporary file storage
├── reports/                 # Generated PDF reports
└── tests/                   # Test files
```

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Run Linter

```bash
ruff check src/ tests/
```

### Format Code

```bash
ruff format src/ tests/
```

### Generate Favicon Files (Optional)

The application uses an SVG favicon by default. To generate PNG and ICO versions:

```bash
pip install svglib pillow
python generate_favicon.py
```

## License

Proprietary - All rights reserved
