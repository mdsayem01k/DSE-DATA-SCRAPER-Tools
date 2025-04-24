# DSE-SCAPER

A Python-based web scraper for collecting and analyzing stock data from the Dhaka Stock Exchange (DSE).

## Overview

DSE-SCAPER is a tool designed to extract real-time and historical stock market data from the Dhaka Stock Exchange website. This project provides various utilities for data collection, processing, and analysis of DSE listed companies.

## Features

- **Comprehensive Data Extraction**: Gathers detailed information on listed companies, sectors, share ratios, and PE ratios.
- **Modular Architecture**: Organized into distinct modules for scalability and maintainability.
- **Scheduled Scraping**: Automates data collection at specified intervals using the integrated scheduler.
- **Logging Mechanism**: Maintains logs for monitoring and debugging purposes.

## Installation

### Prerequisites

- Python 3.7+
- Required Python packages (see `requirements.txt`)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/mdsayem01k/DSE-SCAPER.git
   cd DSE-SCAPER
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## GUI Preview

The application includes a user-friendly interface for scraping and scheduling tasks.

![DSE Data Scraper GUI](path/to/screenshot.png)

### GUI Features

- **Tabbed Navigation**: Switch between modules like Share Scrape, Sector-Company Scrape, Sector Scrape, PE Ratio Scrape, and Company Scrape.
- **Status Display**: Shows current status (e.g., Ready, Running) and elapsed time.
- **Manual & Scheduled Scraping**:
  - Click **Scrape Now** to manually trigger data scraping.
  - Set a time and click **Start Scheduler** to automate scraping.
- **Log Output**: View logs and scraping status directly in the application.
- **Database Configuration**: Easily configure DB settings using the **Edit DB Config** button.

> 🛠 Built with `Tkinter` for a responsive and intuitive desktop interface.


## Project Structure

```
DSE-SCAPER/
├── scraper/             # Core scraper modules
│   ├── __init__.py
│   ├── dse_scraper.py   # Main scraper class
│   └── utils.py         # Utility functions
├── data/                # Directory for storing collected data
├── examples/            # Example usage scripts
├── LICENSE              # License information
└── README.md            # Project documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes only. Users are responsible for ensuring their usage complies with DSE's terms of service and relevant regulations regarding web scraping and data usage.

## Author

- **Md Sayem** - [mdsayem01k](https://github.com/mdsayem01k)

## Acknowledgments

- Dhaka Stock Exchange for providing the public data interface
- Contributors and the open-source community
