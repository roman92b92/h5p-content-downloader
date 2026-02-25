import csv
import re
import requests
import json
import pickle
import logging
import sys
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class H5PDownloader:
    def __init__(self, username, password, base_url, cookie_file="session_cookies.pkl", debug=False):
        """Initialize downloader with credentials and target platform URL."""
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.base_url = base_url.rstrip('/')
        self.cookie_file = cookie_file
        self.authenticated = False
        self.debug = debug

        # Setup logging
        self.logger = logging.getLogger('H5PDownloader')
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(logging.DEBUG if debug else logging.INFO)
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            console.setFormatter(formatter)
            self.logger.addHandler(console)

        # Mimic a real browser to avoid bot detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        self.logger.info(f"Initialized H5P Downloader for {self.base_url}")

    def format_name(self, name):
        """Convert a content name to a URL-safe, lowercase, dash-separated filename."""
        formatted = name.strip().lower()
        formatted = re.sub(r'\s+', ' ', formatted)
        formatted = formatted.replace(' ', '-')
        formatted = re.sub(r'[^a-z0-9-]', '', formatted)
        return formatted

    def format_folder_name(self, name):
        """Format a name for use as a folder (keeps case, replaces invalid path characters)."""
        formatted = name.strip()
        invalid_chars = r'[<>:"/\\|?*]'
        formatted = re.sub(invalid_chars, '_', formatted)
        formatted = formatted.strip('. ')
        return formatted

    def create_hierarchical_path(self, course, module, section, unit, output_dir="downloads"):
        """Create a nested folder structure: output_dir/Course/Module/Section/

        The unit name is used for the filename, not as a folder.
        """
        path_parts = [output_dir]

        if course:
            path_parts.append(self.format_folder_name(course))
        if module:
            path_parts.append(self.format_folder_name(module))
        if section:
            path_parts.append(self.format_folder_name(section))

        full_path = Path(*path_parts)
        full_path.mkdir(parents=True, exist_ok=True)

        self.logger.debug(f"Folder path: {full_path}")
        return full_path

    def extract_id(self, url):
        """Extract the numeric content ID from an H5P content URL."""
        match = re.search(r'/content/(\d+)', url)
        if match:
            return match.group(1)
        return None

    def construct_download_url(self, content_id, formatted_name):
        """Build the expected H5P export download URL from content ID and name."""
        filename = f"{formatted_name}-{content_id}.h5p"
        download_url = f"{self.base_url}/media/exports/{content_id}/{filename}"
        return download_url, filename

    def save_cookies(self):
        """Persist session cookies to disk for reuse in future runs."""
        try:
            with open(self.cookie_file, 'wb') as f:
                pickle.dump(self.session.cookies, f)
            self.logger.info(f"Session cookies saved to {self.cookie_file}")
        except Exception as e:
            self.logger.warning(f"Could not save cookies: {e}")

    def load_cookies(self):
        """Load previously saved session cookies from disk."""
        try:
            if Path(self.cookie_file).exists():
                with open(self.cookie_file, 'rb') as f:
                    self.session.cookies.update(pickle.load(f))
                self.logger.info(f"Session cookies loaded from {self.cookie_file}")
                return True
            else:
                self.logger.debug(f"No cookie file found at {self.cookie_file}")
        except Exception as e:
            self.logger.warning(f"Could not load cookies: {e}")
        return False

    def test_session(self):
        """Check whether the current session is still authenticated."""
        try:
            self.logger.info("Testing session validity...")
            test_url = f"{self.base_url}/content"
            response = self.session.get(test_url, allow_redirects=False)
            self.logger.debug(f"Session test status: {response.status_code}")

            if response.status_code == 200:
                self.logger.info("Session is valid")
                return True
            else:
                self.logger.warning(f"Session expired or invalid (status: {response.status_code})")
                return False
        except Exception as e:
            self.logger.error(f"Session test failed: {e}")
            return False

    def login(self):
        """Authenticate using H5P.com's two-step email + password login flow."""
        self.logger.info("=" * 60)
        self.logger.info("STARTING H5P.COM TWO-STEP LOGIN")
        self.logger.info("=" * 60)

        try:
            # Step 1: Load the /login/introduce page to get a CSRF token
            introduce_url = f"{self.base_url}/login/introduce"
            self.logger.info(f"Step 1: GET {introduce_url}")
            response = self.session.get(introduce_url)

            if response.status_code != 200:
                self.logger.error(f"Failed to load login page (status: {response.status_code})")
                return False

            soup = BeautifulSoup(response.content, 'html.parser')
            login_form = soup.find('form')

            if not login_form:
                self.logger.error("No login form found on introduce page.")
                return False

            csrf_input = soup.find('input', {'name': '_token'})
            if not csrf_input:
                self.logger.error("No CSRF token found in login form.")
                return False

            csrf_token = csrf_input.get('value')
            form_action = login_form.get('action')
            self.logger.info(f"Step 2: Submitting email to {form_action}")

            # Step 2: Submit the email address
            payload_step1 = {'_token': csrf_token, 'email': self.username}
            response = self.session.post(form_action, data=payload_step1, allow_redirects=True)

            # Detect SSO redirect (unsupported)
            if 'sso' in response.url.lower() or 'saml' in response.url.lower():
                self.logger.error("This account uses SSO/SAML — automated login is not supported.")
                return False

            soup = BeautifulSoup(response.content, 'html.parser')
            password_form = soup.find('form', {'method': re.compile('post', re.I)})
            password_input = soup.find('input', {'type': 'password'}) or soup.find('input', {'name': 'password'})

            if not password_input:
                self.logger.error("No password field found. Possible causes:")
                self.logger.error("  - Email not recognized")
                self.logger.error("  - Account requires SSO")
                self.logger.error("  - Account is locked")
                return False

            # Step 3: Submit password
            csrf_input = soup.find('input', {'name': '_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')

            form_action = password_form.get('action') if password_form else f"{self.base_url}/login"
            if not form_action.startswith('http'):
                form_action = f"{self.base_url}{form_action}" if form_action.startswith('/') else f"{self.base_url}/{form_action}"

            payload_step2 = {'_token': csrf_token, 'email': self.username, 'password': self.password}

            # Include any hidden form fields
            for hidden in soup.find_all('input', {'type': 'hidden'}):
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name and name not in payload_step2:
                    payload_step2[name] = value

            self.logger.info(f"Step 3: Submitting password to {form_action}")
            response = self.session.post(form_action, data=payload_step2, allow_redirects=True)

            # Step 4: Verify login success
            if response.status_code == 200 and 'login' not in response.url.lower():
                self.logger.info("=" * 60)
                self.logger.info("LOGIN SUCCESSFUL")
                self.logger.info("=" * 60)
                self.authenticated = True
                self.save_cookies()
                return True
            else:
                self.logger.error("LOGIN FAILED — check your credentials in config.json")
                return False

        except Exception as e:
            self.logger.error(f"Login exception: {e}", exc_info=self.debug)
            return False

    def ensure_authenticated(self):
        """Use cached session if valid, otherwise perform a fresh login."""
        self.logger.info("Checking authentication...")
        if self.load_cookies() and self.test_session():
            self.authenticated = True
            return True
        self.logger.info("No valid session found — logging in...")
        return self.login()

    def analyze_content_page(self, content_url, content_id):
        """Attempt to extract the real download URL from the H5P content page."""
        self.logger.info(f"Analyzing content page: {content_url}")
        try:
            response = self.session.get(content_url)
            if response.status_code != 200:
                self.logger.error(f"Cannot access content page (status: {response.status_code})")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Method 1: Look for explicit download/export links
            for pattern in [
                soup.find('a', href=re.compile(r'download|export', re.I)),
                soup.find('button', {'data-url': re.compile(r'\.h5p$', re.I)}),
                soup.find('a', {'class': re.compile(r'download', re.I)}),
            ]:
                if pattern:
                    link = pattern.get('href') or pattern.get('data-url')
                    if link:
                        self.logger.info(f"Found download link via page scrape: {link}")
                        return link

            # Method 2: Parse the H5PIntegration JavaScript config block
            for script in soup.find_all('script'):
                if script.string and 'H5PIntegration' in script.string:
                    match = re.search(r'H5PIntegration\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        try:
                            config = json.loads(match.group(1))
                            for content_data in config.get('contents', {}).values():
                                if 'exportUrl' in content_data:
                                    url = content_data['exportUrl']
                                    self.logger.info(f"Found exportUrl in H5PIntegration: {url}")
                                    return url
                        except json.JSONDecodeError:
                            pass

            return None

        except Exception as e:
            self.logger.error(f"Error analyzing content page: {e}", exc_info=self.debug)
            return None

    def download_file(self, url, filename, output_dir="downloads"):
        """Download an H5P file to the specified output directory."""
        self.logger.info("=" * 60)
        self.logger.info(f"DOWNLOADING: {filename}")
        self.logger.info("=" * 60)

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_path = Path(output_dir) / filename

        self.logger.info(f"URL: {url}")
        self.logger.info(f"Destination: {output_path}")

        try:
            head_response = self.session.head(url, allow_redirects=True)
            if head_response.status_code == 404:
                self.logger.error("File not found (404)")
                return False

            response = self.session.get(url, stream=True, allow_redirects=True)
            content_type = response.headers.get('Content-Type', 'unknown')
            content_length = response.headers.get('Content-Length', 'unknown')
            self.logger.info(f"Content-Type: {content_type} | Size: {content_length} bytes")

            if response.status_code == 200:
                if 'text/html' in content_type:
                    self.logger.warning("Received HTML instead of file — authentication may have expired")
                    return False

                total_bytes = 0
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_bytes += len(chunk)

                self.logger.info(f"Saved {total_bytes:,} bytes → {output_path}")
                return True
            else:
                self.logger.error(f"Download failed (HTTP {response.status_code})")
                return False

        except Exception as e:
            self.logger.error(f"Error downloading file: {e}", exc_info=self.debug)
            return False

    def process_csv(self, csv_file, output_dir="downloads"):
        """Read the CSV and download all listed H5P files.

        Supported CSV formats
        ---------------------
        Hierarchical (recommended):
            course, module, section, unit, content_url

        Simple (legacy):
            content_name, content_url
        """
        try:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"PROCESSING: {csv_file}")
            self.logger.info(f"{'='*60}\n")

            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or []
                is_hierarchical = 'course' in fieldnames or 'module' in fieldnames

                self.logger.info(f"Format: {'HIERARCHICAL' if is_hierarchical else 'SIMPLE'}")

                entries = list(reader)

            total = len(entries)
            successful = 0
            failed = 0

            self.logger.info(f"Entries found: {total}\n")

            for idx, row in enumerate(entries, 1):
                self.logger.info(f"\n[{idx}/{total}] ─────────────────────────────────────")

                if is_hierarchical:
                    course   = row.get('course', '').strip()
                    module   = row.get('module', '').strip()
                    section  = row.get('section', '').strip()
                    unit     = row.get('unit', '').strip()
                    content_url = row.get('content_url', '').strip()
                    content_name = unit or section or module or 'untitled'

                    self.logger.info(f"  Course  : {course}")
                    self.logger.info(f"  Module  : {module}")
                    self.logger.info(f"  Section : {section}")
                    self.logger.info(f"  Unit    : {unit}")
                    self.logger.info(f"  URL     : {content_url}")

                    target_dir = self.create_hierarchical_path(course, module, section, unit, output_dir)
                else:
                    content_name = row.get('content_name', '').strip()
                    content_url  = row.get('content_url', '').strip()
                    target_dir   = Path(output_dir)
                    target_dir.mkdir(parents=True, exist_ok=True)

                    self.logger.info(f"  Name : {content_name}")
                    self.logger.info(f"  URL  : {content_url}")

                if not content_url:
                    self.logger.warning("Skipping — no content URL")
                    failed += 1
                    continue

                content_id = self.extract_id(content_url)
                if not content_id:
                    self.logger.error(f"Cannot extract content ID from: {content_url}")
                    failed += 1
                    continue

                formatted_name = self.format_name(content_name) if content_name else f"content-{content_id}"
                self.logger.info(f"  File : {formatted_name}-{content_id}.h5p")

                # Try to find the download URL on the content page first
                actual_url = self.analyze_content_page(content_url, content_id)

                if actual_url:
                    if not actual_url.startswith('http'):
                        actual_url = f"{self.base_url}{actual_url}" if actual_url.startswith('/') else f"{self.base_url}/{actual_url}"
                    download_url = actual_url
                    filename = f"{formatted_name}-{content_id}.h5p"
                else:
                    self.logger.warning("Page analysis found no URL, using constructed path...")
                    download_url, filename = self.construct_download_url(content_id, formatted_name)

                if self.download_file(download_url, filename, str(target_dir)):
                    successful += 1
                else:
                    # Try common H5P export URL fallbacks
                    self.logger.warning("Primary URL failed — trying fallback patterns...")
                    fallbacks = [
                        f"{self.base_url}/wp-content/uploads/h5p/exports/{formatted_name}-{content_id}.h5p",
                        f"{self.base_url}/h5p/exports/{formatted_name}-{content_id}.h5p",
                        f"{self.base_url}/export/{content_id}",
                        f"{self.base_url}/content/{content_id}/download",
                    ]
                    success = False
                    for alt_url in fallbacks:
                        self.logger.info(f"  Trying: {alt_url}")
                        if self.download_file(alt_url, filename, str(target_dir)):
                            successful += 1
                            success = True
                            break
                    if not success:
                        failed += 1

            self.logger.info(f"\n{'='*60}")
            self.logger.info("DOWNLOAD SUMMARY")
            self.logger.info(f"{'='*60}")
            self.logger.info(f"  Total      : {total}")
            self.logger.info(f"  Successful : {successful}")
            self.logger.info(f"  Failed     : {failed}")
            self.logger.info(f"{'='*60}\n")

        except FileNotFoundError:
            self.logger.error(f"CSV file not found: {csv_file}")
        except Exception as e:
            self.logger.error(f"Error processing CSV: {e}", exc_info=self.debug)


def load_config(config_file="config.json"):
    """Load and validate configuration from a JSON file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found.")
        print("Copy config.example.json to config.json and fill in your credentials.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{config_file}': {e}")
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='H5P Content Downloader — batch download .h5p files from an H5P.com platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python h5p_downloader.py
  python h5p_downloader.py --config my_course.json
  python h5p_downloader.py --config my_course.json --debug
        """
    )
    parser.add_argument('--config', default='config.json', metavar='FILE',
                        help='Path to JSON config file (default: config.json)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable verbose debug logging')
    args = parser.parse_args()

    print("=" * 60)
    print("H5P Content Downloader")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.debug:
        print("DEBUG MODE: verbose logging enabled")
    print("=" * 60)

    config = load_config(args.config)
    if not config:
        return

    username   = config.get('username')
    password   = config.get('password')
    base_url   = config.get('base_url', 'https://h5p.com')
    csv_file   = config.get('csv_file', 'examples/sample_hierarchical.csv')
    output_dir = config.get('output_dir', 'downloads')

    if not username or not password:
        print("Error: 'username' and 'password' must be set in your config file.")
        return

    placeholder_values = {'your_email@example.com', 'your_email_here', 'your_password_here'}
    if username in placeholder_values or password in placeholder_values:
        print("\nPlease update config.json with your actual credentials before running.")
        print("See config.example.json for the expected format.")
        return

    print(f"\nConfiguration:")
    print(f"  Platform : {base_url}")
    print(f"  Username : {username}")
    print(f"  CSV file : {csv_file}")
    print(f"  Output   : {output_dir}/")
    print()

    downloader = H5PDownloader(username, password, base_url, debug=args.debug)

    if downloader.ensure_authenticated():
        downloader.process_csv(csv_file, output_dir)
    else:
        print("\nAuthentication failed. Cannot proceed.")
        print("\nTroubleshooting:")
        print("  1. Double-check username/password in config.json")
        print("  2. Try logging in manually at the platform URL")
        print("  3. Confirm the platform does not require SSO/SAML")
        print("  4. Run with --debug for detailed logs")

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
