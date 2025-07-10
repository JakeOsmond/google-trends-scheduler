# trend_scraper.py
from pytrends.request import TrendReq
import pandas as pd
import os
from datetime import datetime, timedelta

# Search term(s)
all_search_terms = ["Travel Insurance"]
geo = 'GB'

# Date range: last 3 years
end_date = datetime.today().strftime('%Y-%m-%d')
start_date = (datetime.today() - timedelta(days=365 * 3)).strftime('%Y-%m-%d')
timeframe = f'{start_date} {end_date}'

# Set up pytrends
pytrends = TrendReq(hl='en-UK', tz=0)

# Collect data
final_df = None
pytrends.build_payload(all_search_terms, timeframe=timeframe, geo=geo)
df = pytrends.interest_over_time().reset_index()

# Drop partial column
if 'isPartial' in df.columns:
    df = df.drop(columns=['isPartial'])

final_df = df.sort_values('date')

# Save to /output directory
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)
file_path = os.path.join(output_dir, "travel_insurance_trend.csv")
final_df.to_csv(file_path, index=False)

print(f"✅ File saved to: {file_path}")
