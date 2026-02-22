"""
Configuration for Oil & Gas Job Search
Customize your job titles, locations, and search parameters here.
"""

# =============================================================================
# YOUR APIFY API TOKEN
# Get yours at: https://console.apify.com/account/integrations
# =============================================================================
APIFY_TOKEN = "YOUR_APIFY_TOKEN_HERE"

# =============================================================================
# JOB TITLES TO SEARCH
# Based on your experience as a Production Operator, Control Room Operator,
# Production Supervisor, Safety Lead, and Safety Advisor in Oil & Gas
# =============================================================================
JOB_TITLES = [
    # --- Your Core Oil & Gas Roles ---
    "Production Operator Oil Gas",
    "Control Room Operator Oil Gas",
    "Production Supervisor Oil Gas",
    "Safety Lead Oil Gas",
    "Safety Advisor Oil Gas",
    "HSE Advisor Oil Gas",
    "HSE Lead Oil Gas",

    # --- Senior / High-Paying Oil & Gas Roles ---
    "Production Superintendent Oil Gas",
    "Operations Supervisor Oil Gas",
    "Operations Manager Oil Gas",
    "Plant Operator Oil Gas",
    "Process Operator Oil Gas",
    "Field Operator Oil Gas",
    "Offshore Production Operator",
    "Offshore Safety Officer",
    "Safety Superintendent",
    "Safety Manager Oil Gas",
    "HSE Manager",
    "HSE Coordinator Oil Gas",
    "Emergency Response Coordinator Oil Gas",

    # --- High-Paying International / FIFO Roles ---
    "FPSO Production Operator",
    "LNG Plant Operator",
    "Drilling Safety Advisor",
    "Pipeline Safety Advisor",
    "Offshore Installation Manager",
    "Process Safety Engineer",
    "Loss Prevention Advisor Oil Gas",
]

# =============================================================================
# LOCATIONS TO SEARCH
# Primary: Newfoundland, Canada
# Secondary: High-paying oil & gas hubs worldwide
# =============================================================================
LOCATIONS = {
    # --- CANADA ---
    "Newfoundland, Canada": {
        "country": "Canada",
        "location": "Newfoundland and Labrador",
    },
    "St. John's, NL": {
        "country": "Canada",
        "location": "St. John's",
    },
    "Alberta, Canada": {
        "country": "Canada",
        "location": "Alberta",
    },
    "Fort McMurray, Canada": {
        "country": "Canada",
        "location": "Fort McMurray",
    },

    # --- HIGH-PAYING INTERNATIONAL HUBS ---
    "Norway (North Sea)": {
        "country": "Norway",
        "location": "Stavanger",
    },
    "United Kingdom (North Sea)": {
        "country": "United Kingdom",
        "location": "Aberdeen",
    },
    "Australia (LNG/Offshore)": {
        "country": "Australia",
        "location": "Perth",
    },
    "Qatar (LNG)": {
        "country": "Qatar",
        "location": "Doha",
    },
    "UAE (Abu Dhabi/Dubai)": {
        "country": "United Arab Emirates",
        "location": "Abu Dhabi",
    },
    "Saudi Arabia": {
        "country": "Saudi Arabia",
        "location": "Dhahran",
    },
    "USA - Texas": {
        "country": "United States",
        "location": "Houston",
    },
    "USA - North Dakota": {
        "country": "United States",
        "location": "North Dakota",
    },
    "Guyana (Offshore)": {
        "country": "Guyana",
        "location": "Georgetown",
    },
    "Brazil (Pre-Salt)": {
        "country": "Brazil",
        "location": "Rio de Janeiro",
    },
    "Trinidad and Tobago": {
        "country": "Trinidad and Tobago",
        "location": "Port of Spain",
    },
}

# =============================================================================
# SEARCH SETTINGS
# =============================================================================
MAX_RESULTS_PER_SEARCH = 50       # Max jobs per search term per platform
POSTED_SINCE = "1 months"         # How recent: "1 days", "1 weeks", "1 months"
OUTPUT_FORMAT = "both"             # "csv", "json", or "both"
OUTPUT_DIR = "results"             # Directory to save results

# =============================================================================
# APIFY ACTORS (from https://console.apify.com/store)
# These are the actors we'll use to search across multiple job platforms
# =============================================================================
ACTORS = {
    "multi_platform": "nextapi/job-search-engines",     # LinkedIn + Indeed + Glassdoor
    "linkedin_jobs": "curious_coder/linkedin-jobs-search-scraper",  # LinkedIn focused
    "glassdoor_jobs": "bebity/glassdoor-jobs-scraper",   # Glassdoor focused
    "indeed_jobs": "nextapi/indeed-jobs",                # Indeed focused
}

# Which actor to use by default ("multi_platform" recommended)
DEFAULT_ACTOR = "multi_platform"
