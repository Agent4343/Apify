# Oil & Gas Job Search Tool

Search for high-paying oil and gas jobs using [Apify](https://console.apify.com/store) actors that scrape LinkedIn, Indeed, Glassdoor, and more.

Built for experienced **Production Operators, Control Room Operators, Production Supervisors, Safety Leads, and Safety Advisors** looking for opportunities in Newfoundland Canada and worldwide.

## Setup

1. **Get an Apify API token:**
   - Sign up at https://console.apify.com
   - Go to **Settings > Integrations** to find your API token
   - Apify gives you $5/month free credit

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your API token** (choose one):
   ```bash
   # Option A: Environment variable (recommended)
   export APIFY_TOKEN=your_token_here

   # Option B: Edit the config file
   # Open job_search_config.py and set APIFY_TOKEN
   ```

## Usage

```bash
# Full search - all roles, all locations (Newfoundland + worldwide)
python job_search.py

# Search Newfoundland only
python job_search.py --location NL

# Search all of Canada (NL + Alberta + Fort McMurray)
python job_search.py --location canada

# Search international high-paying hubs only (Norway, Australia, Middle East, etc.)
python job_search.py --worldwide

# Quick search - core roles only (fewer API calls, saves credits)
python job_search.py --quick

# Quick search, Newfoundland only
python job_search.py --quick --location NL

# Use LinkedIn-specific scraper
python job_search.py --actor linkedin

# Use Indeed-specific scraper
python job_search.py --actor indeed

# Custom job titles
python job_search.py --titles "Drilling Engineer" "Rig Manager" "FPSO Operator"

# Preview what would be searched (no API calls)
python job_search.py --dry-run
```

## Job Titles Searched

### Core Roles
- Production Operator (Oil & Gas)
- Control Room Operator
- Production Supervisor
- Safety Lead / Safety Advisor
- HSE Advisor / HSE Lead

### Senior & High-Paying Roles
- Production Superintendent
- Operations Manager / Supervisor
- Offshore Production Operator
- Offshore Safety Officer / Installation Manager
- Safety Manager / Superintendent
- HSE Manager / Coordinator
- FPSO Production Operator
- LNG Plant Operator
- Process Safety Engineer
- And more...

## Locations Searched

### Canada
- **Newfoundland and Labrador** (St. John's)
- **Alberta** (Fort McMurray)

### Worldwide High-Paying Hubs
- **Norway** - Stavanger (North Sea)
- **UK** - Aberdeen (North Sea)
- **Australia** - Perth (LNG/Offshore)
- **Qatar** - Doha (LNG)
- **UAE** - Abu Dhabi
- **Saudi Arabia** - Dhahran
- **USA** - Houston TX, North Dakota
- **Guyana** - Georgetown (Offshore)
- **Brazil** - Rio de Janeiro (Pre-Salt)
- **Trinidad and Tobago** - Port of Spain

## Output

Results are saved to the `results/` directory as CSV and JSON:
- `results/oil_gas_jobs_YYYYMMDD_HHMMSS.csv`
- `results/oil_gas_jobs_YYYYMMDD_HHMMSS.json`

## Customization

Edit `job_search_config.py` to:
- Add/remove job titles
- Add/remove locations
- Change the default actor (multi-platform, LinkedIn, Indeed)
- Adjust max results and date filters

## Apify Actors Used

From [Apify Store](https://console.apify.com/store):

| Actor | Platforms | ID |
|-------|-----------|-----|
| Job Search Engines API | LinkedIn + Indeed + Glassdoor | `nextapi/job-search-engines` |
| LinkedIn Job Scraper | LinkedIn | `curious_coder/linkedin-jobs-search-scraper` |
| Glassdoor Jobs Scraper | Glassdoor | `bebity/glassdoor-jobs-scraper` |
| Indeed Jobs API | Indeed | `nextapi/indeed-jobs` |
