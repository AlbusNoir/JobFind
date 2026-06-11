#!/usr/bin/env python3
import os
import sys
import re
import pandas as pd
from tabulate import tabulate
import logging

# Before even beginning, establish control for logs to silence the annoying output for sites that blocked us
logging.disable(logging.CRITICAL)


# Attempt to import jobspy
try:
    from jobspy import scrape_jobs
except ImportError:
    print("Error: The 'python-jobspy' package is not installed.")
    print("Please activate your virtual environment and run: uv pip install -r requirements.txt")
    sys.exit(1)

def show_help():
    help_text = """
Job Search CLI Tool
===================
Usage:
  1. Interactive Mode:
     python job_search.py

  2. Configuration File Mode:
     python job_search.py <config_file_path>

Example Configuration File Format (config.txt):
  location: City, State
  radius: 25 miles
  keywords: it, technology, network, support
"""
    print(help_text)

def parse_radius(radius_str):
    # Extract numeric value from radius string (e.g. '25 miles' -> 25)
    if not radius_str:
        return 25
    match = re.search(r'(\d+)', str(radius_str))
    if match:
        return int(match.group(1))
    return 25

def parse_keywords(keywords_str):
    # Split comma separated keywords and strip whitespace
    if not keywords_str:
        return []
    return [kw.strip() for kw in keywords_str.split(',') if kw.strip()]

def parse_config_file(file_path):
    # Parse config from provided file
    if not os.path.exists(file_path):
        print(f"Error: Configuration file '{file_path}' does not exist.")
        sys.exit(1)
        
    config = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or ':' not in line:
                    continue
                key, val = line.split(':', 1)
                config[key.strip().lower()] = val.strip()
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        sys.exit(1)
        
    # Validate required fields
    required = ['location', 'radius', 'keywords']
    missing = [req for req in required if req not in config]
    if missing:
        print(f"Error: Configuration file is missing required fields: {', '.join(missing)}")
        sys.exit(1)
        
    return config

def get_interactive_inputs():
    # Prompt user for search inputs in the terminal
    print("--- Job Search Interactive Mode ---")
    
    keywords_input = ""
    while not keywords_input.strip():
        keywords_input = input("Enter keywords (comma separated, e.g. helpdesk, it, network): ")
        if not keywords_input.strip():
            print("Keywords cannot be empty. Please enter at least one keyword")
            
    location_input = ""
    while not location_input.strip():
        location_input = input("Enter location as a comma-separated value (e.g. City, State): ")
        if not location_input.strip():
            print("Location cannot be empty.")
            
    radius_input = input("Enter search radius (default: 25 miles): ")
    if not radius_input.strip():
        # This is the only value we default. 25 miles seems like a fine default
        radius_input = "25"
        
    return {
        'keywords': keywords_input,
        'location': location_input,
        'radius': radius_input
    }

def clean_preamble_prefixes(text):
    """
    Strip common introductory phrases from the start of a sentence or bullet point
    The follow are what I encountered in testing. There are likely MANY more variations
    """
    prefixes = [
        r'^\s*duties include, but are not limited to\s*',
        r'^\s*duties and responsibilities include\s*',
        r'^\s*duties:\s*duties include\s*',
        r'^\s*under the general supervision of\s*',
        r'^\s*is responsible for\s*',
        r'^\s*responsible for\s*',
        r'^\s*performs other duties as\s*',
        r'^\s*typical duties\s*',
        r'^\s*essential duties and responsibilities\s*',
        r'^\s*primary duties\s*',
        r'^\s*what you will do\s*',
        r'^\s*key responsibilities\s*',
        r'^\s*duties:\s*'
        r'^\s*responsibilities:\s*'
    ]
    cleaned = text.strip()
    for pat in prefixes:
        cleaned = re.sub(pat, '', cleaned, flags=re.IGNORECASE)
    
    # Capitalize the first letter if it was lowercased after stripping. Idk it just looks nicer
    if cleaned and cleaned != text.strip():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned

def is_generic_preamble(text):
    text_lower = text.lower()
    preambles = [
        "essential duties and responsibilities",
        "duties include, but are not limited to",
        "duties and responsibilities include",
        "under the general supervision of",
        "representative of the knowledge",
        "reasonable accommodation may be",
        "reasonable accommodations may be",
        "duties are typical",
        "performing the following duties",
        "following is a summary",
        "the successful candidate will",
        "we are seeking",
        "looking for",
        "performs other duties as",
        "is responsible for performing",
        "reporting directly to",
        "duties: duties include",
        "are representative of",
        "performing other duties",
        "typical duties",
        "general summary",
        "summary of position"
    ]
    return any(p in text_lower for p in preambles)

def is_company_prattle(text, company_name=""):
    text_lower = text.lower()
    
    """
    Common company nonsense that isn't relevant to the job description
    The follow are what I encountered in testing. There are likely MANY more variations
    """
    prattle_patterns = [
        r'\bis a leading\b',
        r'\bis a global\b',
        r'\bis a premier\b',
        r'\bis a fast-growing\b',
        r'\bis a world leader\b',
        r'\bis the go-to\b',
        r'\bheadquartered in\b',
        r'\bnyse:\w*\b',
        r'\bnasdaq:\w*\b',
        r'\bdedicated to\b',
        r'\bcommitted to\b',
        r'\bwe are dedicated\b',
        r'\bour mission is\b',
        r'\bour core values\b',
        r'\bjoin our team\b',
        r'\bwe believe in\b',
        r'\bwe pride ourselves\b',
        r'\bhas an opening for\b',
        r'\binvites applications\b',
    ]
    
    for pat in prattle_patterns:
        if re.search(pat, text_lower):
            return True
            
    """
    WEIRD EDGE CASES THAT WEREN'T HANDLED ABOVE
    """        
    # Check if text starts with "we are", "we're", or company introductions
    if re.match(r'^(we are|we\'re|our team|our mission|about our|at \w+|here at \w+)', text_lower):
        return True
        
    if company_name:
        co_lower = str(company_name).lower().strip()
        # Strip common business suffixes
        co_clean = re.sub(r'\b(inc|llc|corp|co|ltd|corporation|incorporated|limited|technologies|solutions|services|group|systems|government)\b', '', co_lower).strip()
        
        if co_clean and len(co_clean) > 2:
            # Check if sentence starts with the company name
            if text_lower.startswith(co_clean):
                return True
            # Check if sentence contains "[company] is" or "at [company]"
            if f"{co_clean} is" in text_lower or f"at {co_clean}" in text_lower:
                return True
                
    return False

def clean_description(desc_raw, company_name=""):
    # Clean job description text for stuff we looked for above
    if pd.isna(desc_raw) or not desc_raw:
        return "No description available."
    
    # Strip escape chars and strip HTML tags
    desc = re.sub(r'\\([-_*#])', r'\1', str(desc_raw))
    desc = re.sub(r'<[^>]*>', ' ', desc)
    desc = desc.strip()
    
    if not desc:
        return "No description available."

    # Split
    lines = [line.strip() for line in desc.split('\n') if line.strip()]

    """
    NOW we actually look for relevant stuff
    """
    # 1. Look for section headers that describe duties/overview
    overview_headers = r'(overview|summary|about the role|position purpose|job summary|role summary|description)'
    duties_headers = r'(responsibilities|duties|essential functions|what you will do|what you\'ll do|key responsibilities|primary duties)'
    boilerplate_headers = r'(requirements|qualifications|what you bring|skills|education|experience|benefits|perks|about us|about the company)'

    overview_content = []
    duties_content = []
    current_section = None
    
    for line in lines:
        line_lower = line.lower().strip()
        line_clean = re.sub(r'^[*#\s\-]+|[*#\s\-]+$', '', line_lower)
        
        is_header = False
        if len(line_clean) < 40:
            if re.search(overview_headers, line_clean):
                current_section = 'overview'
                is_header = True
            elif re.search(duties_headers, line_clean):
                current_section = 'duties'
                is_header = True
            elif re.search(boilerplate_headers, line_clean):
                current_section = 'boilerplate'
                is_header = True
                
        if is_header:
            continue
            
        if current_section == 'overview':
            overview_content.append(line)
        elif current_section == 'duties':
            duties_content.append(line)

    # 2. Extract best blocks - best is subjective
    extracted_bullets = []
    source_content = duties_content if duties_content else overview_content
    
    for line in source_content:
        # Skip generic preambles or company prattle
        if is_generic_preamble(line) or is_company_prattle(line, company_name):
            continue
            
        # Check if it looks like a list item
        if line.startswith('*') or line.startswith('-') or line.startswith('•') or re.match(r'^\d+\.', line):
            cleaned_line = re.sub(r'^[*•\-\d.\s]+', '', line).strip()
            cleaned_line = clean_preamble_prefixes(cleaned_line)
            # Skip if it is boilerplate or intro
            if cleaned_line and not is_company_prattle(cleaned_line, company_name) and not any(bp in cleaned_line.lower() for bp in ["years of experience", "ability to", "degree in", "must have", "requirements"]):
                extracted_bullets.append(cleaned_line)
        elif len(line) > 30 and not line.startswith('#'):
            cleaned_line = clean_preamble_prefixes(line)
            # Skip if generic or prattle
            if cleaned_line and not is_generic_preamble(cleaned_line) and not is_company_prattle(cleaned_line, company_name):
                extracted_bullets.append(cleaned_line)
            
        if len(extracted_bullets) >= 3:
            break

    # 3. Fallback: Score sentences across the whole description
    if not extracted_bullets:
        sentences = re.split(r'(?<=[.!?])\s+', desc)
        scored_sentences = []
        
        action_verbs = r'\b(maintain|support|install|configur|develop|manag|monitor|administ|coordinat|troubleshoot|resolv|assist|repair|design)\w*\b'
        boilerplate_terms = r'\b(equal opportunity|benefits|salary|hourly|status|years of|degree|must be|requirements|experience|university|amazon|company)\b'
        
        for sent in sentences:
            sent_clean = clean_preamble_prefixes(sent)
            if len(sent_clean) < 15 or len(sent_clean) > 200 or is_generic_preamble(sent_clean) or is_company_prattle(sent_clean, company_name):
                continue
            
            if re.match(r'^(we are|about the|founded in|invites applications|reporting to|our company)', sent_clean.lower()):
                continue
                
            score = 0
            if re.search(action_verbs, sent_clean.lower()):
                score += 5
            if re.search(r'\b(responsible for|duties include|responsibilities)\b', sent_clean.lower()):
                score += 4
            if re.search(boilerplate_terms, sent_clean.lower()):
                score -= 6
                
            scored_sentences.append((score, sent_clean))
            
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        for score, sent in scored_sentences:
            if score > 0:
                extracted_bullets.append(sent)
            if len(extracted_bullets) >= 2:
                break

    # Fallback 2: resort to just using the first few sentences
    if not extracted_bullets:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', desc) if s.strip()]
        for sent in sentences:
            sent_clean = clean_preamble_prefixes(sent)
            if len(sent_clean) > 30 and not is_generic_preamble(sent_clean) and not is_company_prattle(sent_clean, company_name) and not any(bp in sent_clean.lower() for bp in ["equal opportunity", "benefits", "status"]):
                extracted_bullets.append(sent_clean)
            if len(extracted_bullets) >= 2:
                break

    # Absolute last-resort fallback: take whatever sentences we have
    if not extracted_bullets:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', desc) if s.strip()]
        for sent in sentences[:2]:
            extracted_bullets.append(clean_preamble_prefixes(sent))

    # Format the synopsis
    synopsis = " | ".join(extracted_bullets)
    synopsis = re.sub(r'\*\*+', '', synopsis)
    synopsis = synopsis.replace('\\-', '-')
    synopsis = re.sub(r'\s+', ' ', synopsis).strip()
    
    # Truncate to a reasonable length. This can be adjusted to taste. 160 is just a number I found that seems okay for terminal display
    max_len = 160
    if len(synopsis) > max_len:
        split_parts = synopsis[:max_len].rsplit(' ', 1)
        if len(split_parts) > 1:
            synopsis = split_parts[0] + "..."
        else:
            synopsis = synopsis[:max_len] + "..."
    return synopsis

def format_location(row):
    # Combine city and state from row, or fall back to location if city/state missing
    city = row.get('city')
    state = row.get('state')
    
    city_str = str(city).strip() if not pd.isna(city) else ""
    state_str = str(state).strip() if not pd.isna(state) else ""
    
    if city_str and state_str:
        return f"{city_str}, {state_str}"
    elif city_str:
        return city_str
    elif state_str:
        return state_str
    return "N/A"

def score_job(row, keywords):
    # Score a job posting based on how many keywords match the title or description
    title = str(row.get('title', '')).lower()
    description = str(row.get('description', '')).lower()
    company = str(row.get('company', '')).lower()
    
    """
    Data weighing stuff
    """
    score = 0
    for kw in keywords:
        kw_lower = kw.lower()
        # Higher score for matches in the job title
        if kw_lower in title:
            score += 10
        # Medium score for company match (e.g., if user searches technology and company has tech)
        if kw_lower in company:
            score += 3
        # Lower score for matches in the job description
        if kw_lower in description:
            score += 1
            
    return score

def main():
    # 1. Handle command-line arguments
    if len(sys.argv) > 2:
        print("Error: Too many arguments.")
        show_help()
        sys.exit(1)
        
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg in ('-h', '--help'):
            show_help()
            sys.exit(0)
        else:
            print(f"Reading configuration from file: {arg}")
            config = parse_config_file(arg)
    else:
        config = get_interactive_inputs()

    # 2. Parse the configuration fields
    keywords = parse_keywords(config['keywords'])
    location = config['location']
    radius = parse_radius(config['radius'])

    print(f"\nSearching jobs matching: {', '.join(keywords)}")
    print(f"Location: {location} (within {radius} miles)")
    print("Scraping job listings (this may take a moment)...")

    # Construct the query by joining keywords with OR
    # Words with spaces are wrapped in quotes. This is important because it broke things initially lol
    query_parts = []
    for kw in keywords:
        if ' ' in kw:
            query_parts.append(f'"{kw}"')
        else:
            query_parts.append(kw)
    
    search_term = " OR ".join(query_parts)

    # 3. Let python-jobspy do the heavy lifting
    try:
        jobs = scrape_jobs(
            site_name=["indeed", "linkedin", "zip_recruiter", "glassdoor"],
            search_term=search_term,
            location=location,
            distance=radius,
            results_wanted=30,  # Grab extra to score, rank, and deduplicate. 30 is also an arbitrary value. Adjust as needed
            country_indeed='USA',  # Also adjust if needed. If you're not in the USA, then this is probably not where you want to search
            linkedin_fetch_description=True  # Don't turn this off. IDK why LinkedIn is different, but it is
        )
    except Exception as e:
        print(f"\nAn error occurred while scraping jobs: {e}")
        print("Please check your internet connection or try again later.")
        sys.exit(1)

    if jobs.empty:
        print("\nNo jobs found matching your criteria.")
        sys.exit(0)

    # Normalize column names to lowercase
    jobs.columns = [col.lower() for col in jobs.columns]

    # 4. Process, Score, and Deduplicate results
    processed_jobs = []
    for idx, row in jobs.iterrows():
        title = row.get('title', 'N/A')
        company = row.get('company', 'N/A')
        
        # Combine title and company for the Job column
        job_display = f"{title} at {company}" if not pd.isna(company) and company != 'N/A' else title
        
        loc_display = format_location(row)
        if loc_display == "N/A":
            loc_display = location  # Fallback to searched location
            
        desc = row.get('description', '')
        synopsis = clean_description(desc, company)
        
        link = row.get('job_url', 'N/A')
        if pd.isna(link):
            link = 'N/A'
            
        score = score_job(row, keywords)
        
        processed_jobs.append({
            'job': job_display,
            'location': loc_display,
            'synopsis': synopsis,
            'link': link,
            'score': score,
            'title_only': str(title).lower(),
            'company_only': str(company).lower()
        })

    # Convert to DataFrame for easier manipulation
    df_processed = pd.DataFrame(processed_jobs)

    # Deduplicate by job title and company (case-insensitive)
    df_processed = df_processed.drop_duplicates(subset=['title_only', 'company_only'], keep='first')

    # Sort by keyword score descending
    df_processed = df_processed.sort_values(by='score', ascending=False)

    # Select the top 10 jobs
    top_jobs = df_processed.head(10)

    final_table_df = top_jobs[['job', 'location', 'synopsis', 'link']]

    if final_table_df.empty:
        print("\nNo jobs matched the criteria after deduplication.")
        sys.exit(0)

    # 5. Display the table
    print("\nSearch Results (Top 10 Jobs):")
    # Format table for output
    headers = ["Job", "Location", "Synopsis", "Link"]
    table_data = final_table_df.values.tolist()
    
    # Use tabulate with wrapping for nice console output
    print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[30, 20, 50, 40]))

    # 6. Prompt to save
    print()
    save_choice = input("Would you like to save the output to a file? (yes/no): ").strip().lower()
    if save_choice in ('y', 'yes'):
        default_filename = "job_results.csv"
        filename_input = input(f"Enter filename to save (default: {default_filename}): ").strip()
        filename = filename_input if filename_input else default_filename
        
        # Handle user not giving extension. Default to csv
        if not filename.endswith('.csv'):
            print("Note: Appending '.csv' to filename.")
            filename += ".csv"
            
        try:
            final_table_df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"Results successfully saved to '{os.path.abspath(filename)}'")
        except Exception as e:
            print(f"Error saving file: {e}")
    else:
        print("Exiting without saving.")

if __name__ == "__main__":
    main()
