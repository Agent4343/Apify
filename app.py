"""
Oil & Gas Job Search - Web Application
Hosted on Railway, powered by Apify actors from https://console.apify.com/store
"""

import csv
import io
import json
import os
import threading
import uuid
from datetime import datetime

from flask import Flask, render_template, request, jsonify, Response

from apify_client import ApifyClient

from job_search_config import (
    JOB_TITLES,
    LOCATIONS,
    ACTORS,
    DEFAULT_ACTOR,
)

app = Flask(__name__)

# In-memory store for search results (per session)
search_results = {}
search_status = {}

# ---------------------------------------------------------------------------
# Apify helpers (reused from job_search.py)
# ---------------------------------------------------------------------------

CORE_TITLES = [
    "Production Operator Oil Gas",
    "Control Room Operator Oil Gas",
    "Production Supervisor Oil Gas",
    "Safety Lead Oil Gas",
    "Safety Advisor Oil Gas",
    "HSE Advisor Oil Gas",
]

NL_LOCATION_KEYS = ["Newfoundland, Canada", "St. John's, NL"]
CANADA_LOCATION_KEYS = [
    "Newfoundland, Canada", "St. John's, NL",
    "Alberta, Canada", "Fort McMurray, Canada",
]


def get_apify_client():
    token = os.environ.get("APIFY_TOKEN", "")
    if not token:
        return None
    return ApifyClient(token)


def normalize_job(job):
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
    seen = set()
    unique = []
    for job in jobs:
        key = (
            str(job.get("title", "")).lower().strip(),
            str(job.get("company", "")).lower().strip(),
            str(job.get("location", "")).lower().strip(),
        )
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


def run_search_task(search_id, titles, locations_dict, max_results, posted_since, actor_type):
    """Background worker that runs the Apify search."""
    client = get_apify_client()
    if not client:
        search_status[search_id] = {
            "state": "error",
            "message": "APIFY_TOKEN environment variable not set.",
        }
        return

    actor_id = ACTORS.get(actor_type, ACTORS[DEFAULT_ACTOR])
    all_jobs = []
    total_locations = len(locations_dict)

    for idx, (loc_name, loc_config) in enumerate(locations_dict.items(), 1):
        search_status[search_id]["progress"] = f"Searching {loc_name} ({idx}/{total_locations})..."
        search_status[search_id]["percent"] = int((idx - 1) / total_locations * 100)

        country = loc_config["country"]
        location = loc_config["location"]

        if actor_type in ("multi_platform", DEFAULT_ACTOR):
            batch_size = 5
            for i in range(0, len(titles), batch_size):
                batch = titles[i:i + batch_size]
                try:
                    run = client.actor(actor_id).call(run_input={
                        "search_terms": batch,
                        "country": country,
                        "location": location,
                        "max_results": max_results,
                        "posted_since": posted_since,
                    })
                    items = client.dataset(run["defaultDatasetId"]).list_items().items
                    all_jobs.extend([normalize_job(j) for j in items])
                except Exception as e:
                    search_status[search_id].setdefault("warnings", []).append(
                        f"{loc_name}: {str(e)[:120]}"
                    )

        elif actor_type == "linkedin":
            for title in titles:
                try:
                    run = client.actor(ACTORS["linkedin_jobs"]).call(run_input={
                        "searchQuery": title,
                        "location": f"{location}, {country}",
                        "maxResults": max_results,
                    })
                    items = client.dataset(run["defaultDatasetId"]).list_items().items
                    all_jobs.extend([normalize_job(j) for j in items])
                except Exception as e:
                    search_status[search_id].setdefault("warnings", []).append(
                        f"LinkedIn {loc_name}: {str(e)[:120]}"
                    )

        elif actor_type == "indeed":
            for title in titles:
                try:
                    run = client.actor(ACTORS["indeed_jobs"]).call(run_input={
                        "search_terms": [title],
                        "country": country,
                        "location": location,
                        "max_results": max_results,
                    })
                    items = client.dataset(run["defaultDatasetId"]).list_items().items
                    all_jobs.extend([normalize_job(j) for j in items])
                except Exception as e:
                    search_status[search_id].setdefault("warnings", []).append(
                        f"Indeed {loc_name}: {str(e)[:120]}"
                    )

    all_jobs = deduplicate_jobs(all_jobs)
    search_results[search_id] = all_jobs
    search_status[search_id]["state"] = "complete"
    search_status[search_id]["progress"] = f"Done! Found {len(all_jobs)} unique jobs."
    search_status[search_id]["percent"] = 100
    search_status[search_id]["count"] = len(all_jobs)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    has_token = bool(os.environ.get("APIFY_TOKEN"))
    return render_template(
        "index.html",
        job_titles=JOB_TITLES,
        locations=LOCATIONS,
        core_titles=CORE_TITLES,
        nl_keys=NL_LOCATION_KEYS,
        canada_keys=CANADA_LOCATION_KEYS,
        has_token=has_token,
    )


@app.route("/search", methods=["POST"])
def start_search():
    data = request.get_json()
    titles = data.get("titles", CORE_TITLES)
    location_keys = data.get("locations", list(LOCATIONS.keys()))
    max_results = int(data.get("max_results", 50))
    posted_since = data.get("posted_since", "1 months")
    actor_type = data.get("actor", DEFAULT_ACTOR)

    selected_locations = {k: v for k, v in LOCATIONS.items() if k in location_keys}
    if not selected_locations:
        selected_locations = LOCATIONS

    search_id = str(uuid.uuid4())[:8]
    search_status[search_id] = {
        "state": "running",
        "progress": "Starting search...",
        "percent": 0,
        "warnings": [],
    }

    thread = threading.Thread(
        target=run_search_task,
        args=(search_id, titles, selected_locations, max_results, posted_since, actor_type),
        daemon=True,
    )
    thread.start()

    return jsonify({"search_id": search_id})


@app.route("/status/<search_id>")
def get_status(search_id):
    status = search_status.get(search_id)
    if not status:
        return jsonify({"state": "not_found"}), 404
    return jsonify(status)


@app.route("/results/<search_id>")
def get_results(search_id):
    jobs = search_results.get(search_id, [])

    sort_by = request.args.get("sort", "")
    if sort_by == "salary":
        def salary_key(j):
            try:
                return float(str(j.get("salary_min", 0)).replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                return 0
        jobs = sorted(jobs, key=salary_key, reverse=True)
    elif sort_by == "company":
        jobs = sorted(jobs, key=lambda j: str(j.get("company", "")).lower())
    elif sort_by == "location":
        jobs = sorted(jobs, key=lambda j: str(j.get("location", "")).lower())

    filter_source = request.args.get("source", "")
    if filter_source:
        jobs = [j for j in jobs if filter_source.lower() in str(j.get("source", "")).lower()]

    filter_location = request.args.get("filter_location", "")
    if filter_location:
        jobs = [j for j in jobs if filter_location.lower() in str(j.get("location", "")).lower()]

    return jsonify({"jobs": jobs, "total": len(jobs)})


@app.route("/download/<search_id>/<fmt>")
def download_results(search_id, fmt):
    jobs = search_results.get(search_id, [])
    if not jobs:
        return "No results", 404

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "json":
        return Response(
            json.dumps(jobs, indent=2, ensure_ascii=False, default=str),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment; filename=oil_gas_jobs_{timestamp}.json"},
        )
    elif fmt == "csv":
        output = io.StringIO()
        fieldnames = [
            "title", "company", "location", "country",
            "salary_min", "salary_max", "salary_currency", "salary_period",
            "employment_type", "seniority_level", "is_remote",
            "url", "source", "posted_date", "description",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for job in jobs:
            writer.writerow(job)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=oil_gas_jobs_{timestamp}.csv"},
        )
    return "Invalid format", 400


@app.route("/health")
def health():
    return jsonify({"status": "ok", "has_token": bool(os.environ.get("APIFY_TOKEN"))})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
