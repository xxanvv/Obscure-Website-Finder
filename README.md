# Obscure Website Finder (OWF) 🌐

Find hidden corners of the internet. OWF is a tool that discovers obscure websites by scanning random IP addresses, complete with a sleek viewer for exploring what you find.

## Features

- Discovers unknown websites across the internet
- Smart filtering to find specific types of sites
- Built-in gallery to preview your discoveries
- Multi-threaded scanning
- Dark-themed website viewer with screenshots
- Saves everything you find automatically

## Quick Start

1. Make sure you have Python 3.7+ installed
2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/obscure-website-finder.git
   cd obscure-website-finder
   ```

3. If you're on Windows, just run:
   ```bash
   start.bat
   ```
   This will set up everything automatically.

4. For manual setup on other systems:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install requests pillow urllib3 tk ipaddress playwright nest_asyncio
   playwright install chromium
   ```

5. Start exploring:
   ```bash
   python OWF.py
   ```

## How It Works

OWF has two main parts:

### 1. The Finder
- Scans random IPs looking for unknown websites
- Filters out common sites to find the obscure ones
- Saves everything it finds to `found_websites.txt`
- Shows you stats while it works
- Stop anytime with Ctrl+C

### 2. The Viewer
- Browse through everything you've found
- See screenshots of each site
- Visit interesting sites directly
- Dark theme for late-night exploring
- Pages through your discoveries

## Tips for Finding Cool Stuff

- Use "Advanced Settings" to filter for specific kinds of sites
- Try filtering titles to find particular pages (like "personal blog" or "home server")
- Look for specific server types to find hobby projects

## Important Notes

- This is for exploring the internet and finding interesting sites
- Some websites might not like automated visitors
- Consider using a VPN while scanning

## Contributing

Found a bug? Have an idea? Feel free to:
- Open an issue
- Submit a pull request
- Suggest new features
- Improve the documentation
- Add more filtering options

## Copyright

© 2025 - All Rights Reserved
