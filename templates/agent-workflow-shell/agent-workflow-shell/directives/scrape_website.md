# Directive: Scrape Website Content

## Goal
Extract text content, links, and metadata from a given website URL and save it in a structured format.

## Inputs
- **URL** (required): The website URL to scrape
- **Depth** (optional): How many levels deep to follow links (default: 1)
- **Selector** (optional): CSS selector for specific content (default: entire page)

## Execution Scripts to Use
1. `execution/scrape_single_site.py` - For single page scraping
2. `execution/parse_html_content.py` - To clean and structure the HTML
3. `execution/save_to_json.py` - To save results

## Workflow
1. Validate the URL format
2. Call `scrape_single_site.py` with the URL
3. If scraping fails (403, 404, timeout), report error to user
4. Parse the HTML content using `parse_html_content.py`
5. Save results to `outputs/scraped_[domain]_[timestamp].json`
6. Return summary to user: pages scraped, total content size, key metadata

## Outputs
- JSON file with structure:
  ```json
  {
    "url": "https://example.com",
    "timestamp": "2024-01-27T10:30:00Z",
    "title": "Page Title",
    "content": "Extracted text content...",
    "links": ["url1", "url2"],
    "metadata": {
      "word_count": 1500,
      "description": "Meta description",
      "author": "Author name"
    }
  }
  ```

## Edge Cases
- **403 Forbidden**: Try with different user agent, if fails inform user
- **Rate limiting**: Wait and retry with exponential backoff
- **Invalid URL**: Validate before scraping, ask user for correction
- **JavaScript-heavy sites**: Inform user that basic scraping may not capture dynamic content
- **Large sites**: If depth > 3, confirm with user first

## Error Handling
- Network errors: Retry up to 3 times with 2-second delays
- Parsing errors: Save raw HTML and inform user
- Timeout: Set 30-second timeout, inform user if exceeded

## Success Criteria
- Successfully retrieved and parsed content
- Saved to outputs directory
- User receives summary with word count and link count

## Notes
- Always respect robots.txt
- Add 1-second delay between requests to be polite
- Use appropriate user agent string
