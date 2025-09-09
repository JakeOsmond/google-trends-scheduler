from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError
import requests
import pandas as pd
import os, time, random
from datetime import datetime, timedelta, timezone

# --------- Settings ---------
all_search_terms = ["Travel Insurance"]
geo = "GB"
years = 3
output_folder = "docs"
output_filename = "travel_insurance_trend.csv"
output_path = os.path.join(output_folder, output_filename)

# --------- Date Range (UTC) ---------
today = datetime.now(timezone.utc)
end_date = today.strftime("%Y-%m-%d")
start_date = (today - timedelta(days=365 * years)).strftime("%Y-%m-%d")
timeframe = f"{start_date} {end_date}"

# --------- Pytrends with browser-like headers ---------
ua = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124 Safari/537.36"
    )
}
# Keep internal retries minimal; we control backoff ourselves
pytrends = TrendReq(
    hl="en-GB",
    tz=0,
    retries=0,
    backoff_factor=0,           # disable internal backoff
    timeout=(10, 45),
    requests_args={"headers": ua},
)

def fetch_full_range(py, terms, timeframe, geo, max_attempts=10):
    """
    Single full-range call with exponential backoff and jitter.
    Backs off up to ~10 minutes on later attempts.
    """
    attempt = 1
    while True:
        try:
            # small random pause before hitting Google
            time.sleep(random.uniform(2.0, 6.0))
            py.build_payload(terms, timeframe=timeframe, geo=geo)
            df = py.interest_over_time().reset_index()
            return df
        except (TooManyRequestsError, requests.exceptions.RetryError) as e:
            if attempt >= max_attempts:
                raise
            sleep_s = min(600, (2 ** attempt) + random.uniform(0, 5))  # cap ~10 min
            print(f"[429] Throttled. Attempt {attempt}/{max_attempts-1}. Sleeping {sleep_s:.1f}s")
            time.sleep(sleep_s)
            attempt += 1

# --------- Fetch Data (single shot) ---------
df = fetch_full_range(pytrends, all_search_terms, timeframe, geo)

# Optionally drop the trailing partial row to avoid weekly instability
# if "isPartial" in df.columns:
#     df = df[df["isPartial"] == False].drop(columns=["isPartial"])

# --------- Save Output ---------
df = df.sort_values("date")
os.makedirs(output_folder, exist_ok=True)
tmp_path = output_path + ".tmp"
df.to_csv(tmp_path, index=False)
os.replace(tmp_path, output_path)

print(f"File saved to: {output_path} (full range {start_date} to {end_date})")
