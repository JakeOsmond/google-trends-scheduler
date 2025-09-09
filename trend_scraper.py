from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError
import requests, time, random, sys
import pandas as pd
import os
from datetime import datetime, timedelta, timezone

# -------- Settings --------
terms = ["Travel Insurance"]
geo = "GB"
years = 3
output = "docs/travel_insurance_trend.csv"

# -------- Dates (UTC) --------
today = datetime.now(timezone.utc)
end_date = today.strftime("%Y-%m-%d")
start_date = (today - timedelta(days=365*years)).strftime("%Y-%m-%d")
timeframe = f"{start_date} {end_date}"

# -------- Pytrends (no internal retries, browsery headers) --------
ua = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://trends.google.com/trends/explore"
}
pytrends = TrendReq(hl="en-GB", tz=0, retries=0, backoff_factor=0, timeout=(10, 45), requests_args={"headers": ua})

def log(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)

def fetch_full_range(max_attempts=6, cap_sleep=30, total_runtime_cap=240):
    """Bounded attempts and bounded sleeps so we never run forever."""
    start_wall = time.perf_counter()
    attempt = 1
    while True:
        try:
            if time.perf_counter() - start_wall > total_runtime_cap:
                raise TimeoutError(f"Overall fetch timed out after {total_runtime_cap}s")
            jitter = random.uniform(1.0, 3.0)
            log(f"Attempt {attempt}: sleeping {jitter:.1f}s preflight")
            time.sleep(jitter)

            log(f"build_payload start timeframe={timeframe}")
            pytrends.build_payload(terms, timeframe=timeframe, geo=geo)

            log("interest_over_time start")
            t0 = time.perf_counter()
            df = pytrends.interest_over_time().reset_index()
            log(f"interest_over_time ok in {time.perf_counter()-t0:.2f}s")
            return df
        except (TooManyRequestsError, requests.exceptions.RetryError) as e:
            if attempt >= max_attempts:
                log(f"Giving up after {attempt} attempts: {type(e).__name__}")
                raise
            sleep_s = min(cap_sleep, (2 ** attempt) + random.uniform(0, 4))
            log(f"429 or retryable error on attempt {attempt}. Sleeping {sleep_s:.1f}s")
            time.sleep(sleep_s)
            attempt += 1

# Quick connectivity smoke test (tiny window). If this hangs, it’s rate limiting or network.
try:
    log("Smoke test: 7d window")
    pytrends.build_payload(terms, timeframe="now 7-d", geo=geo)
    _ = pytrends.interest_over_time()
    log("Smoke test succeeded")
except Exception as e:
    log(f"Smoke test failed fast: {e.__class__.__name__}: {e}")
    # Optional: exit early to avoid long job times if even 7d is blocked
    # sys.exit(1)

# Fetch full range
df = fetch_full_range()

# Optional: drop trailing partial week for stability
# if "isPartial" in df.columns:
#     df = df[df["isPartial"] == False].drop(columns=["isPartial"])

df = df.sort_values("date")
os.makedirs(os.path.dirname(output), exist_ok=True)
tmp = output + ".tmp"
df.to_csv(tmp, index=False)
os.replace(tmp, output)
log(f"Saved {output} rows={len(df)} range={df['date'].min()}..{df['date'].max()}")
