import argparse
from bs4 import BeautifulSoup
import requests
import subprocess
import re
from collections import deque
import os
from colorama import init, Fore, Style
import sqlite3
import random
import time
from urllib.parse import urljoin
import json
import socks
import socket
import itertools

init()  # Initialize colorama

user_agent_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
]
user_agent_cycle = itertools.cycle(user_agent_list)
delay_range = (1, 3)

def check_tor_service():
    try:
        sock = socket.create_connection(("127.0.0.1", 9050), timeout=5)
        sock.close()
        return True
    except (socket.error, socket.timeout):
        return False

def get_command_arguments():
    parser = argparse.ArgumentParser(description='File metadata finder')
    parser.add_argument('-u', '--url', required=True, help='URL to search on the website')
    parser.add_argument('-o', '--output', required=True, help='Name of the output file or database')
    parser.add_argument('-t', '--types', help='File types to process (comma-separated, e.g., doc,docx,pdf). If not specified, all file types will be processed.')
    args = parser.parse_args()
    return args

class MetadataFinder:
    def __init__(self):
        self.output_file_name = ''
        self.conn = None
        self.cursor = None

    def connect_to_database(self, db_name):
        try:
            self.conn = sqlite3.connect(db_name)
            self.cursor = self.conn.cursor()
            # Modification in the database structure
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    url TEXT,
                    file_type TEXT,
                    file_name TEXT,
                    mime_type TEXT,
                    pdf_version TEXT,
                    linearized TEXT,
                    author TEXT,
                    create_date TEXT,
                    modify_date TEXT,
                    language TEXT,
                    tagged_pdf TEXT,
                    xmp_toolkit TEXT,
                    format TEXT,
                    creator TEXT,
                    creator_tool TEXT,
                    metadata_date TEXT,
                    producer TEXT,
                    document_id TEXT,
                    instance_id TEXT,
                    page_count INTEGER,
                    additional_metadata TEXT  
                )
            """)
           
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            exit(1)

    # Modified insert_metadata function
    def insert_metadata(self, url, file_type, metadata):
        try:
            # Extract known fields
            known_fields = ['FileName', 'MIMEType', 'PDFVersion', 'Linearized', 'Author', 'CreateDate',
                            'ModifyDate', 'Language', 'TaggedPDF', 'XMPToolkit', 'Format', 'Creator',
                            'CreatorTool', 'MetadataDate', 'Producer', 'DocumentID', 'InstanceID', 'PageCount']
            
            # Create a dictionary with additional fields
            additional_fields = {k: v for k, v in metadata.items() if k not in known_fields}
            
            self.cursor.execute(
                "INSERT INTO metadata (url, file_type, file_name, mime_type, pdf_version, linearized, "
                "author, create_date, modify_date, language, tagged_pdf, xmp_toolkit, format, creator, "
                "creator_tool, metadata_date, producer, document_id, instance_id, page_count, additional_metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (url, file_type, metadata.get('FileName'), metadata.get('MIMEType'), metadata.get('PDFVersion'),
                 metadata.get('Linearized'), metadata.get('Author'), metadata.get('CreateDate'),
                 metadata.get('ModifyDate'), metadata.get('Language'), metadata.get('TaggedPDF'),
                 metadata.get('XMPToolkit'), metadata.get('Format'), metadata.get('Creator'),
                 metadata.get('CreatorTool'), metadata.get('MetadataDate'), metadata.get('Producer'),
                 metadata.get('DocumentID'), metadata.get('InstanceID'), metadata.get('PageCount'),
                 json.dumps(additional_fields))  # Convert additional fields to JSON
            )
            self.conn.commit()
        except Exception as e:
            print(f"Error inserting into the database: {e}")

    def close_database_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def main(self, args):
        self.output_file_name = args.output

        # Get all file types that Exiftool can process
        all_file_types = self.get_exiftool_supported_types()

        # Define the file types to process
        if args.types:
            file_types = args.types.split(',')
        else:
            file_types = all_file_types

        # Create the link pattern based on file types
        link_pattern = re.compile(r'https?://\S+\.(' + '|'.join(file_types) + ')$', re.IGNORECASE)

        # Connect to the database if necessary
        if self.output_file_name.endswith('.db'):
            self.connect_to_database(self.output_file_name)
        
        url = args.url
        visited = set()
        queue = deque([url])

        print(f'Searching for metadata in {url}')
        print(f'File types to process: {", ".join(file_types)}')

        while queue:
            current_url = queue.popleft()
            if current_url not in visited:
                visited.add(current_url)
                print(f'Visiting {current_url}')
                if not current_url.startswith(('http', 'https')):
                    print(f'The URL does not start with "http" or "https": {current_url}')
                    continue
                try:
                    headers = {'User-Agent': next(user_agent_cycle)}
                    response = session.get(current_url, headers=headers, timeout=300)
                    print(f'Received response from {current_url}. Status code: {response.status_code}')
                except requests.exceptions.RequestException as e:
                    print(f'Error fetching {current_url}: {e}')
                    continue

                soup = BeautifulSoup(response.text, 'lxml')
                links = [link.get('href') for link in soup.find_all('a')]

                for link in links:
                    if isinstance(link, str):
                        time.sleep(random.uniform(delay_range[0], delay_range[1]))

                        # Convert relative links to absolute ones
                        link = urljoin(url, link)

                        if link_pattern.match(link):
                            self.process_file(link)
                        elif link.startswith('http'):
                            if link not in visited and link not in queue:
                                queue.append(link)

        # Close the database connection if necessary
        self.close_database_connection()

    def process_file(self, link):
        try:
            headers = {'User-Agent': next(user_agent_cycle)}
            file_type = link.split('.')[-1]
            
            # Use curl to get the content and pass it directly to ExifTool
            command = f"curl -s -L -A '{headers['User-Agent']}' '{link}' | exiftool -fast -json -"
            output = subprocess.check_output(command, shell=True).decode('utf-8')
            
            metadata = json.loads(output)[0]  # ExifTool returns a list with a dictionary
            
            # Extract the original file name from the URL
            file_name = os.path.basename(link)
            
            # Add the file name and URL to the metadata
            metadata['FileName'] = file_name
            metadata['SourceURL'] = link
            
            if metadata:
                print(Fore.GREEN + f"Metadata found in the file {link}" + Style.RESET_ALL)
                for key, value in metadata.items():
                    print(f"{key}: {value}")
                
                if self.output_file_name.endswith('.db'):
                    self.insert_metadata(link, file_type, metadata)
                else:
                    with open(self.output_file_name, 'a') as output_file:
                        for key, value in metadata.items():
                            output_file.write(f"Found the data {key}: {value} in the file {link}\n")
            else:
                print(f'No metadata found in the file {link}')
                if self.output_file_name.endswith('.db'):
                    self.insert_metadata(link, file_type, {})
        except Exception as e:
            print(f'Error processing the file {link}: {e}')

    def get_exiftool_supported_types(self):
        try:
            output = subprocess.check_output(['exiftool', '-listf']).decode('utf-8')
            return [line.strip() for line in output.split('\n') if line.strip()]
        except Exception as e:
            print(f"Error getting file types supported by ExifTool: {e}")
            return ['doc', 'docx', 'pdf', 'jpg', 'jpeg', 'png', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'epub', 'txt']

if __name__ == '__main__':
    args = get_command_arguments()
    tor_service_running = check_tor_service()
    
    if tor_service_running:
        # Configure the Tor proxy
        socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 9050)
        socket.socket = socks.socksocket
    
    session = requests.Session()

    finder = MetadataFinder()
    finder.main(args)
