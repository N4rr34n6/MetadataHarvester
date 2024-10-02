### README.md

# MetadataHarvester

MetadataHarvester is an advanced file metadata extraction tool designed for cybersecurity professionals, researchers, and analysts. This tool efficiently scans websites for downloadable files, extracts metadata using ExifTool, and stores the information in a structured format, allowing for comprehensive analysis. With capabilities for deep web searches through the Tor network, MetadataHarvester offers unparalleled versatility for collecting crucial metadata from a wide range of file types.

## Key Features

- **Comprehensive Metadata Extraction**: Extract detailed metadata from various file types, including PDF, DOC, DOCX, JPG, PNG, and many more.
- **Tor Network Compatibility**: Seamlessly integrates with the Tor network to ensure anonymity and access to .onion domains, expanding its reach into the deep web.
- **Automatic Data Logging**: Store metadata in SQLite databases for easy management and future analysis.
- **User-Defined File Types**: Customize file type searches based on specific needs, or scan for all supported file types.
- **Efficient Web Crawling**: Employs user-agent rotation and randomized delays to crawl web pages without triggering security defenses.
- **Integrated with ExifTool**: Leverages the power of ExifTool to provide accurate and detailed metadata extraction from supported files.
- **Simple Output Options**: Save the results in a database or as a simple text file.

## Installation

Before using MetadataHarvester, ensure you have the required dependencies installed.

### Prerequisites

- Python 3.6+
- Tor service installed and running
- ExifTool installed (`sudo apt-get install libimage-exiftool-perl` on Debian-based systems)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/n4rr34n6/MetadataHarvester.git
   cd MetadataHarvester
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Ensure the Tor service is active and configured correctly:
   ```bash
   sudo service tor start
   ```

## Usage

Run the script by specifying the target URL and output file:

```bash
python3 MetadataHarvester.py -u https://example.com -o output.db
```

You can also specify the file types to search for:

```bash
python3 MetadataHarvester.py -u https://example.com -o output.db -t pdf,docx
```

## Technical Details

- **Web Scraping**: Uses `BeautifulSoup` for HTML parsing and `requests` to handle HTTP and HTTPS connections.
- **Tor Integration**: Uses SOCKS5 proxies for routing traffic through the Tor network.
- **ExifTool**: Extracts metadata from files, and results are stored in SQLite databases or text files for flexible output options.

## Ethical Use and Legal Considerations

MetadataHarvester is intended for use in lawful research, cybersecurity analysis, and file management. Unauthorized scanning or data extraction from websites may violate terms of service and legal statutes. The developers are not responsible for any misuse of this tool.

## License

This project is provided under the GNU Affero General Public License v3.0. You can find the full license text in the [LICENSE](LICENSE) file.
