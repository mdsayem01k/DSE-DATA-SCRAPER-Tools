# DSE-SCAPER

A Python-based web scraper for collecting and analyzing stock data from the Dhaka Stock Exchange (DSE).

## Overview

DSE-SCAPER is a tool designed to extract real-time and historical stock market data from the Dhaka Stock Exchange website. This project provides various utilities for data collection, processing, and analysis of DSE listed companies.

## Features

- Scrape current stock prices and trading information
- Extract company information and performance metrics
- Generate historical stock data for analysis
- Export data to CSV format for further processing
- Visualize stock trends and market movements

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

## Usage

### Basic Scraping

To start scraping basic DSE data:

```python
from scraper.dse_scraper import DSEScraper

# Initialize the scraper
scraper = DSEScraper()

# Get current market data
market_data = scraper.get_market_data()

# Get specific stock information
stock_info = scraper.get_stock_info("SQUARETEXT")

# Export data to CSV
scraper.export_to_csv(market_data, "market_data.csv")
```

### Advanced Features

For more advanced usage, refer to the examples in the `example.py` file or the documentation.

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
