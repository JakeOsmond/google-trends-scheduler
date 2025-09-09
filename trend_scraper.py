from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError
import pandas as pd
import os
import time
import random
from datetime import datetime, timedelta

# --------- Settings ---------
all_search_terms = ["Travel Insurance"]
geo = 'GB'
years = 3
output_folder = "docs"
output_filename = "travel_insurance_trend.csv"
output_path = os.path.join(output_folder, output_filename)

# --------- Date Range (ending on today) ---------
today = datetime.today()
end_date = today.strftime('%Y-%m-%d')
start_date = (today - timedelta(days=365 * years)).strftime('%Y-%m-%d')
timeframe = f'{start_date} {end_date}'

# --------- Set up pytrends with retries ---------
# hl en-GB for UK, tz 0 for UTC, retries and backoff_factor enable internal retry logic
pytrends = TrendReq(hl='en-GB', tz=0, retries=5, backoff_factor=0.5, timeout=(10, 30))

def fetch_interest_with_retry(py, terms, timeframe, geo, max_attempts=7):
    """
    Extra retry wrapper to survive stubborn 429s on CI.
    Exponential backoff with jitter, caps at ~1 minute sleeps.
    """
    attempt = 1
    while True:
        try:
            py.build_payload(terms, timeframe=timeframe, geo=geo)
            df = py.interest_over_time().reset_index()
            return df
        except TooManyRequestsError as e:
            if attempt >= max_attempts:
                raise
            sleep_s = min(60, (2 ** attempt) + random.uniform(0, 3))
            print(f"429 received. Attempt {attempt}/{max_attempts - 1}. Sleeping {sleep_s:.1f}s...")
            time.sleep(sleep_s)
            attempt += 1

# --------- Fetch Data ---------
final_df = None
batch_size = 5

for i in range(0, len(all_search_terms), batch_size):
    batch = all_search_terms[i:i + batch_size]
    df = fetch_interest_with_retry(pytrends, batch, timeframe, geo)

    # Optional: drop partial rows if you do not want trailing partial weeks
    # if 'isPartial' in df.columns:
    #     df = df[df['isPartial'] == False].drop(columns=['isPartial'])

    if final_df is None:
        final_df = df
    else:
        final_df = pd.merge(final_df, df, on='date', how='outer')

# --------- Save Output ---------
final_df = final_df.sort_values('date')
os.makedirs(output_folder, exist_ok=True)
final_df.to_csv(output_path, index=False)
print(f"File saved to: {output_path} (up to {end_date})")
