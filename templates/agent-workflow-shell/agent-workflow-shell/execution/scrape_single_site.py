#!/usr/bin/env python3
"""
Scrape a single website and extract content.

Usage:
    python scrape_single_site.py <url> [--selector <css_selector>] [--output <path>]

Example:
    python scrape_single_site.py https://example.com --selector "article.main"
"""

import sys
import json
import argparse
from datetime import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import time


def scrape_website(url, selector=None, timeout=30):
    """
    Scrape content from a website URL.
    
    Args:
        url (str): The URL to scrape
        selector (str, optional): CSS selector for specific content
        timeout (int): Request timeout in seconds
    
    Returns:
        dict: Scraped content and metadata
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract content based on selector
        if selector:
            content_elements = soup.select(selector)
            content = '\n\n'.join([elem.get_text(strip=True) for elem in content_elements])
        else:
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            content = soup.get_text(strip=True, separator='\n')
        
        # Extract metadata
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else 'No title'
        
        description_tag = soup.find('meta', attrs={'name': 'description'})
        description = description_tag['content'] if description_tag and 'content' in description_tag.attrs else ''
        
        # Extract all links
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert relative URLs to absolute
            if href.startswith('/'):
                parsed = urlparse(url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            elif not href.startswith('http'):
                continue
            links.append(href)
        
        # Build result
        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'title': title_text,
            'content': content,
            'links': list(set(links)),  # Remove duplicates
            'metadata': {
                'word_count': len(content.split()),
                'description': description,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'selector_used': selector
            }
        }
        
        return result
        
    except requests.exceptions.Timeout:
        return {'error': 'Request timed out', 'url': url}
    except requests.exceptions.HTTPError as e:
        return {'error': f'HTTP error: {e.response.status_code}', 'url': url}
    except requests.exceptions.RequestException as e:
        return {'error': f'Request error: {str(e)}', 'url': url}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}', 'url': url}


def main():
    parser = argparse.ArgumentParser(description='Scrape a single website')
    parser.add_argument('url', help='URL to scrape')
    parser.add_argument('--selector', help='CSS selector for content', default=None)
    parser.add_argument('--output', help='Output file path', default=None)
    parser.add_argument('--timeout', help='Request timeout', type=int, default=30)
    
    args = parser.parse_args()
    
    # Scrape the website
    result = scrape_website(args.url, args.selector, args.timeout)
    
    # Save to file if output path provided
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {args.output}")
    else:
        # Print to stdout
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Exit with error code if scraping failed
    if 'error' in result:
        sys.exit(1)


if __name__ == '__main__':
    main()
