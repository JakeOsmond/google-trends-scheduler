from pytrends.request import TrendReq
import pandas as pd
import os
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

# --------- Set up pytrends ---------
pytrends = TrendReq(hl='en-UK', tz=0)

# --------- Fetch Data ---------
final_df = None
batch_size = 5

for i in range(0, len(all_search_terms), batch_size):
    batch = all_search_terms[i:i + batch_size]
    pytrends.build_payload(batch, timeframe=timeframe, geo=geo)
    df = pytrends.interest_over_time().reset_index()

    # Exclude partial rows
    # if 'isPartial' in df.columns:
    #     df = df[df['isPartial'] == False]
    #     df = df.drop(columns=['isPartial'])

    # Merge batch into final_df
    if final_df is None:
        final_df = df
    else:
        final_df = pd.merge(final_df, df, on='date', how='outer')

# --------- Save Output ---------
final_df = final_df.sort_values('date')
os.makedirs(output_folder, exist_ok=True)
final_df.to_csv(output_path, index=False)

print(f"✅ File saved to: {output_path} (up to {end_date}, partial data excluded)")
