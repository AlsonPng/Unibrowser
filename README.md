# Unibrowser
A modern, minimal, and professional browser built with Python and PyQt5.

## Features
- Edge-to-edge web content with no extra containers
- Tabs in the custom title bar (top)
- Navigation/search bar below tabs
- DuckDuckGo as the default search engine
- Modern, clean, and responsive UI (light theme, gradients, rounded corners)
- Keyboard shortcuts:
  - **Ctrl+T**: New Tab
  - **Ctrl+L**: Focus/Search URL
  - **Ctrl+W**: Close Tab
- Window controls: minimize, maximize/restore, close
- Smart URL/search detection

## Requirements
- Python 3.7+
- PyQt5
- PyQtWebEngine

## Installation
Install dependencies with pip:

```sh
pip install -r requirements.txt
```

## Usage
Run Unibrowser from the project directory:

```sh
python unibrowser/main.py
```

## UI Overview
- **Tabs**: Appear in the title bar for a compact, modern look.
- **Navigation Bar**: Below the tabs, includes back/forward/reload buttons and a search/address bar that expands to fill the width.
- **Web Content**: Fills the entire window below the navigation bar, with no extra borders or containers.
- **Window Controls**: Minimize, maximize/restore, and close buttons are in the top right.

## Tips
- Enter a full URL (with or without `https://`) or type a search query directly.
- All navigation and tab actions are accessible via keyboard shortcuts for efficiency.

## Troubleshooting
If you encounter issues with missing dependencies or Git not being recognized:
- Ensure Python and pip are installed and available in your PATH.
- For Git, add its installation directory (e.g., `C:\Program Files\Git\cmd`) to your Windows PATH environment variable.

---

Unibrowser is open source and welcomes contributions!
