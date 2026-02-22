#!/usr/bin/env python3
"""
Oil & Gas Job Search Tool
Uses Apify actors from https://console.apify.com/store to search for
oil and gas jobs across LinkedIn, Indeed, Glassdoor, and more.

Searches for Production Operator, Control Room Operator, Production Supervisor,
Safety Lead, Safety Advisor and other high-paying roles in Newfoundland Canada
and top-paying oil & gas hubs worldwide.

Usage:
    python job_search.py                     # Run full search (all locations)
    python job_search.py --location "NL"     # Search Newfoundland only
    python job_search.py --worldwide         # Search international hubs only
    python job_search.py --quick             # Quick search (core roles only)
    python job_search.py --dry-run           # Preview what would be searched
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from apify_client import ApifyClient
except ImportError:
    print("=" * 60)
    print("ERROR: apify-client not installed.")
    print("Run: pip install apify-client")
    print("=" * 60)
    sys.exit(1)

from job_search_config import (
    APIFY_TOKEN,
    JOB_TITLES,
    LOCATIONS,
    MAX_RESULTS_PER_SEARCH,
    POSTED_SINCE,
    OUTPUT_FORMAT,
    OUTPUT_DIR,
    ACTORS,
    DEFAULT_ACTOR,
)


# Core roles (used for --quick mode)
CORE_TITLES = [
    "Production Operator Oil Gas",
    "Control Room Operator Oil Gas",
    "Production Supervisor Oil Gas",
    "Safety Lead Oil Gas",
    "Safety Advisor Oil Gas",
    "HSE Advisor Oil Gas",
]

# Newfoundland-only locations (used for --location NL)
NL_LOCATION_KEYS = ["Newfoundland, Canada", "St. John's, NL"]

# Canadian locations
CANADA_LOCATION_KEYS = [
    "Newfoundland, Canada",
    "St. John's, NL",
    "Alberta, Canada",
    "Fort McMurray, Canada",
]


def create_client(token):
    """Initialize the Apify API client."""
    if token == "YOUR_APIFY_TOKEN_HERE" or not token:
        print("=" * 60)
        print("ERROR: Please set your Apify API token!")
        print()
        print("1. Go to https://console.apify.com/account/integrations")
        print("2. Copy your API token")
        print("3. Paste it in job_search_config.py as APIFY_TOKEN")
        print("   OR set environment variable: export APIFY_TOKEN=your_token")
        print("=" * 60)
        sys.exit(1)
    return ApifyClient(token)


def search_jobs_multi_platform(client, search_terms, country, location, max_results, posted_since):
    """
    Search for jobs using the multi-platform actor (nextapi/job-search-engines).
    Searches LinkedIn, Indeed, and Glassdoor simultaneously.
    """
    actor_id = ACTORS["multi_platform"]
    run_input = {
        "search_terms": search_terms,
        "country": country,
        "location": location,
        "max_results": max_results,
        "posted_since": posted_since,
    }

    print(f"  Running actor: {actor_id}")
    print(f"  Search terms: {search_terms}")
    print(f"  Location: {location}, {country}")
    print(f"  Max results per platform: {max_results}")

    try:
        run = client.actor(actor_id).call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        print(f"  -> Found {len(dataset_items)} jobs")
        return dataset_items
    except Exception as e:
        print(f"  -> ERROR: {e}")
        return []


def search_jobs_linkedin(client, search_term, location, max_results):
    """
    Search for jobs using the LinkedIn-specific actor.
    """
    actor_id = ACTORS["linkedin_jobs"]
    run_input = {
        "searchQuery": search_term,
        "location": location,
        "maxResults": max_results,
    }

    print(f"  Running LinkedIn actor: {actor_id}")
    print(f"  Query: {search_term} in {location}")

    try:
        run = client.actor(actor_id).call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        print(f"  -> Found {len(dataset_items)} LinkedIn jobs")
        return dataset_items
    except Exception as e:
        print(f"  -> ERROR with LinkedIn actor: {e}")
        return []


def search_jobs_indeed(client, search_term, country, location, max_results):
    """
    Search for jobs using the Indeed-specific actor.
    """
    actor_id = ACTORS["indeed_jobs"]
    run_input = {
        "search_terms": [search_term],
        "country": country,
        "location": location,
        "max_results": max_results,
    }

    print(f"  Running Indeed actor: {actor_id}")
    print(f"  Query: {search_term} in {location}, {country}")

    try:
        run = client.actor(actor_id).call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        print(f"  -> Found {len(dataset_items)} Indeed jobs")
        return dataset_items
    except Exception as e:
        print(f"  -> ERROR with Indeed actor: {e}")
        return []


def normalize_job(job):
    """Normalize job data from different actors into a consistent format."""
    return {
        "title": job.get("title") or job.get("job_title") or job.get("name", "N/A"),
        "company": job.get("company_name") or job.get("company") or job.get("companyName", "N/A"),
        "location": job.get("location") or job.get("job_location") or job.get("place", "N/A"),
        "country": job.get("country", "N/A"),
        "salary_min": job.get("salary_minimum") or job.get("salary_min") or job.get("salaryMin", ""),
        "salary_max": job.get("salary_maximum") or job.get("salary_max") or job.get("salaryMax", ""),
        "salary_currency": job.get("salary_currency") or job.get("currency", ""),
        "salary_period": job.get("salary_period") or job.get("salaryPeriod", ""),
        "employment_type": job.get("employment_type") or job.get("type") or job.get("employmentType", "N/A"),
        "seniority_level": job.get("seniority_level") or job.get("seniorityLevel", "N/A"),
        "is_remote": job.get("is_remote") or job.get("isRemote", False),
        "description": (job.get("description") or job.get("job_description") or "")[:500],
        "url": job.get("url") or job.get("job_url") or job.get("link", "N/A"),
        "source": job.get("source") or job.get("platform") or job.get("site", "N/A"),
        "posted_date": job.get("posted_date") or job.get("date") or job.get("postedDate", "N/A"),
    }


def deduplicate_jobs(jobs):
    """Remove duplicate job listings based on title + company + location."""
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = (
            job.get("title", "").lower().strip(),
            job.get("company", "").lower().strip(),
            job.get("location", "").lower().strip(),
        )
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    return unique_jobs


def save_results_csv(jobs, filepath):
    """Save job results to CSV file."""
    if not jobs:
        print("No jobs to save to CSV.")
        return

    fieldnames = [
        "title", "company", "location", "country",
        "salary_min", "salary_max", "salary_currency", "salary_period",
        "employment_type", "seniority_level", "is_remote",
        "description", "url", "source", "posted_date",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for job in jobs:
            writer.writerow(job)

    print(f"Saved {len(jobs)} jobs to {filepath}")


def save_results_json(jobs, filepath):
    """Save job results to JSON file."""
    if not jobs:
        print("No jobs to save to JSON.")
        return

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False, default=str)

    print(f"Saved {len(jobs)} jobs to {filepath}")


def print_summary(jobs):
    """Print a summary of the job search results."""
    if not jobs:
        print("\nNo jobs found.")
        return

    print("\n" + "=" * 80)
    print(f"  JOB SEARCH RESULTS SUMMARY - {len(jobs)} jobs found")
    print("=" * 80)

    # Group by location
    by_location = {}
    for job in jobs:
        loc = job.get("location", "Unknown")
        by_location.setdefault(loc, []).append(job)

    print(f"\n{'Location':<40} {'Jobs':>6}")
    print("-" * 48)
    for loc in sorted(by_location.keys(), key=lambda x: len(by_location[x]), reverse=True)[:20]:
        print(f"  {loc:<38} {len(by_location[loc]):>6}")

    # Group by source/platform
    by_source = {}
    for job in jobs:
        src = job.get("source", "Unknown")
        by_source.setdefault(src, []).append(job)

    print(f"\n{'Platform':<30} {'Jobs':>6}")
    print("-" * 38)
    for src in sorted(by_source.keys(), key=lambda x: len(by_source[x]), reverse=True):
        print(f"  {src:<28} {len(by_source[src]):>6}")

    # Jobs with salary info
    with_salary = [j for j in jobs if j.get("salary_min") or j.get("salary_max")]
    print(f"\nJobs with salary info: {len(with_salary)} / {len(jobs)}")

    # Show top-paying jobs if salary data available
    if with_salary:
        print("\n--- TOP PAYING JOBS (by minimum salary) ---")
        salary_jobs = []
        for j in with_salary:
            try:
                sal = float(str(j.get("salary_min", 0)).replace(",", "").replace("$", ""))
                salary_jobs.append((sal, j))
            except (ValueError, TypeError):
                continue

        salary_jobs.sort(key=lambda x: x[0], reverse=True)
        for sal, j in salary_jobs[:15]:
            currency = j.get("salary_currency", "")
            period = j.get("salary_period", "")
            print(f"  {currency}{sal:>10,.0f}/{period:<6}  {j['title'][:35]:<36} @ {j['company'][:25]:<26} ({j['location']})")

    # Print first 20 job listings
    print("\n--- SAMPLE JOB LISTINGS ---")
    for i, job in enumerate(jobs[:20], 1):
        salary_str = ""
        if job.get("salary_min") or job.get("salary_max"):
            cur = job.get("salary_currency", "$")
            lo = job.get("salary_min", "?")
            hi = job.get("salary_max", "?")
            per = job.get("salary_period", "")
            salary_str = f" | {cur}{lo}-{cur}{hi}/{per}"

        print(f"\n  [{i}] {job['title']}")
        print(f"      Company:  {job['company']}")
        print(f"      Location: {job['location']}")
        print(f"      Source:   {job['source']}{salary_str}")
        if job.get("url") and job["url"] != "N/A":
            print(f"      Apply:    {job['url']}")


def run_search(client, titles, locations_dict, max_results, posted_since, actor_type="multi_platform"):
    """Run the job search across all specified titles and locations."""
    all_jobs = []

    total_searches = len(locations_dict)
    for idx, (loc_name, loc_config) in enumerate(locations_dict.items(), 1):
        print(f"\n{'='*60}")
        print(f"  SEARCHING: {loc_name} ({idx}/{total_searches})")
        print(f"{'='*60}")

        country = loc_config["country"]
        location = loc_config["location"]

        if actor_type == "multi_platform":
            # Multi-platform actor accepts a list of search terms
            # Batch titles to avoid overly long queries
            batch_size = 5
            for i in range(0, len(titles), batch_size):
                batch = titles[i : i + batch_size]
                jobs = search_jobs_multi_platform(
                    client, batch, country, location, max_results, posted_since
                )
                normalized = [normalize_job(j) for j in jobs]
                all_jobs.extend(normalized)

        elif actor_type == "linkedin":
            for title in titles:
                jobs = search_jobs_linkedin(
                    client, title, f"{location}, {country}", max_results
                )
                normalized = [normalize_job(j) for j in jobs]
                all_jobs.extend(normalized)

        elif actor_type == "indeed":
            for title in titles:
                jobs = search_jobs_indeed(
                    client, title, country, location, max_results
                )
                normalized = [normalize_job(j) for j in jobs]
                all_jobs.extend(normalized)

    return all_jobs


def main():
    parser = argparse.ArgumentParser(
        description="Oil & Gas Job Search using Apify (LinkedIn, Indeed, Glassdoor)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python job_search.py                          Full search all locations
  python job_search.py --location NL            Newfoundland only
  python job_search.py --location canada        All Canadian locations
  python job_search.py --worldwide              International hubs only
  python job_search.py --quick                  Quick search (core roles only)
  python job_search.py --quick --location NL    Quick search, NL only
  python job_search.py --actor linkedin         Use LinkedIn-specific actor
  python job_search.py --dry-run                Preview without running
  python job_search.py --titles "Drilling Engineer" "Rig Manager"
        """,
    )
    parser.add_argument(
        "--location",
        choices=["NL", "canada", "worldwide", "all"],
        default="all",
        help="Which locations to search (default: all)",
    )
    parser.add_argument(
        "--worldwide",
        action="store_true",
        help="Search only international high-paying hubs",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick search with core roles only (fewer API calls)",
    )
    parser.add_argument(
        "--actor",
        choices=["multi_platform", "linkedin", "indeed"],
        default=DEFAULT_ACTOR,
        help="Which Apify actor to use (default: multi_platform)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=MAX_RESULTS_PER_SEARCH,
        help=f"Max results per search (default: {MAX_RESULTS_PER_SEARCH})",
    )
    parser.add_argument(
        "--posted-since",
        default=POSTED_SINCE,
        help=f'How recent (default: "{POSTED_SINCE}")',
    )
    parser.add_argument(
        "--titles",
        nargs="+",
        help="Custom job titles to search (overrides config)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview searches without running them",
    )
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})",
    )

    args = parser.parse_args()

    # Determine which titles to search
    if args.titles:
        titles = args.titles
    elif args.quick:
        titles = CORE_TITLES
    else:
        titles = JOB_TITLES

    # Determine which locations to search
    if args.worldwide:
        selected_locations = {
            k: v for k, v in LOCATIONS.items() if k not in CANADA_LOCATION_KEYS
        }
    elif args.location == "NL":
        selected_locations = {
            k: v for k, v in LOCATIONS.items() if k in NL_LOCATION_KEYS
        }
    elif args.location == "canada":
        selected_locations = {
            k: v for k, v in LOCATIONS.items() if k in CANADA_LOCATION_KEYS
        }
    elif args.location == "worldwide":
        selected_locations = {
            k: v for k, v in LOCATIONS.items() if k not in CANADA_LOCATION_KEYS
        }
    else:
        selected_locations = LOCATIONS

    # Print search plan
    print("\n" + "#" * 60)
    print("  OIL & GAS JOB SEARCH")
    print("  Powered by Apify (https://console.apify.com/store)")
    print("#" * 60)
    print(f"\n  Actor:       {ACTORS[args.actor]}")
    print(f"  Job titles:  {len(titles)} search terms")
    print(f"  Locations:   {len(selected_locations)} locations")
    print(f"  Max results: {args.max_results} per platform per search")
    print(f"  Posted since: {args.posted_since}")
    print(f"\n  Titles:")
    for t in titles:
        print(f"    - {t}")
    print(f"\n  Locations:")
    for loc in selected_locations:
        print(f"    - {loc}")

    if args.dry_run:
        print("\n  [DRY RUN] No searches will be executed.")
        print(f"  This search would make ~{len(selected_locations)} actor runs.")
        return

    # Get token from env or config
    token = os.environ.get("APIFY_TOKEN", APIFY_TOKEN)
    client = create_client(token)

    # Run searches
    print("\n  Starting searches...\n")
    all_jobs = run_search(
        client, titles, selected_locations,
        args.max_results, args.posted_since, args.actor
    )

    # Deduplicate
    print(f"\nTotal raw results: {len(all_jobs)}")
    all_jobs = deduplicate_jobs(all_jobs)
    print(f"After deduplication: {len(all_jobs)}")

    # Print summary
    print_summary(all_jobs)

    # Save results
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_format = OUTPUT_FORMAT
    if output_format in ("csv", "both"):
        csv_path = output_dir / f"oil_gas_jobs_{timestamp}.csv"
        save_results_csv(all_jobs, csv_path)

    if output_format in ("json", "both"):
        json_path = output_dir / f"oil_gas_jobs_{timestamp}.json"
        save_results_json(all_jobs, json_path)

    print("\n" + "=" * 60)
    print("  SEARCH COMPLETE!")
    print(f"  Total unique jobs found: {len(all_jobs)}")
    print(f"  Results saved to: {output_dir}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
