# Oil & Gas Job Search Tool

Search for high-paying oil and gas jobs using [Apify](https://console.apify.com/store) actors that scrape LinkedIn, Indeed, Glassdoor, and more.

Built for experienced **Production Operators, Control Room Operators, Production Supervisors, Safety Leads, and Safety Advisors** looking for opportunities in Newfoundland Canada and worldwide.

## Deploy to Railway

### 1. Get an Apify API token
- Sign up at https://console.apify.com
- Go to **Settings > Integrations** to find your API token
- Apify gives you $5/month free credit

### 2. Deploy on Railway
1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) and create a new project
3. Select **"Deploy from GitHub repo"** and connect this repository
4. Railway will auto-detect Python and install dependencies

### 3. Set environment variable
In your Railway project dashboard:
1. Go to your service -> **Variables** tab
2. Add: `APIFY_TOKEN` = `your_apify_token_here`
3. Railway will redeploy automatically

That's it! Your job search app will be live at the Railway-provided URL.

## How It Works

The web app lets you:
- Pick which **job titles** to search (your core roles are pre-selected)
- Pick which **locations** to search (Newfoundland, Canada, or worldwide hubs)
- Choose the **platform** (LinkedIn + Indeed + Glassdoor, or individual)
- Filter by **time posted**, sort by **salary**, filter by **platform**
- **Download results** as CSV or JSON

Searches run in the background with a live progress bar. Results show job title, company, location, salary (when available), and direct apply links.

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set your token
export APIFY_TOKEN=your_token_here

# Run the web app locally
python app.py
# Opens at http://localhost:5000

# Or use the CLI version
python job_search.py --location NL --quick
```

### CLI Usage

```bash
python job_search.py                          # Full search all locations
python job_search.py --location NL            # Newfoundland only
python job_search.py --location canada        # All Canadian locations
python job_search.py --worldwide              # International hubs only
python job_search.py --quick                  # Core roles only (saves credits)
python job_search.py --quick --location NL    # Quick search, NL only
python job_search.py --actor linkedin         # Use LinkedIn-specific actor
python job_search.py --actor indeed           # Use Indeed-specific actor
python job_search.py --dry-run                # Preview without running
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

## Project Structure

```
├── app.py                  # Flask web app (Railway runs this)
├── job_search.py           # CLI version
├── job_search_config.py    # Job titles, locations, Apify actor config
├── templates/
│   └── index.html          # Web UI
├── Procfile                # Railway process definition
├── railway.json            # Railway deployment config
├── runtime.txt             # Python version
├── requirements.txt        # Python dependencies
└── README.md
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `APIFY_TOKEN` | Yes | Your Apify API token from https://console.apify.com/account/integrations |
| `PORT` | No | Auto-set by Railway (default: 5000 locally) |

## Apify Actors Used

From [Apify Store](https://console.apify.com/store):

| Actor | Platforms | ID |
|-------|-----------|-----|
| Job Search Engines API | LinkedIn + Indeed + Glassdoor | `nextapi/job-search-engines` |
| LinkedIn Job Scraper | LinkedIn | `curious_coder/linkedin-jobs-search-scraper` |
| Glassdoor Jobs Scraper | Glassdoor | `bebity/glassdoor-jobs-scraper` |
| Indeed Jobs API | Indeed | `nextapi/indeed-jobs` |
