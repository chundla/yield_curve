import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from io import StringIO
import asyncio
import httpx

async def fetch(url, retries=5):
	try:
		async with httpx.AsyncClient() as client:
			response = await client.get(url, timeout=20.0)  # Set a suitable timeout
			return response.text
	except httpx.ReadTimeout:
		if retries > 0:
			print(f"Timeout for {url}. Retrying... ({retries} retries left)")
			return await fetch(url, retries - 1)
		else:
			print(f"Failed to fetch {url} after several retries.")
		return None

async def main():
	current_year = datetime.now().year
	current_month = '{:02d}'.format(datetime.now().month)
	years = [f'{current_year}{current_month}', 200608, 201908, 200008]
	urls = [f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/all/{year}?field_tdr_date_value_month={year}&type=daily_treasury_yield_curve&page&_format=csv" for year in years]
	tasks = [fetch(url) for url in urls]
	responses = await asyncio.gather(*tasks)
	data_df = pd.DataFrame()
	for response in responses:
		if response:
	    	# Read the CSV data from the response text
			year_df = pd.read_csv(StringIO(response), parse_dates=['Date'])

		if not year_df.empty:
			#random_dates = year_df['Date'].sample(n=1)
			#filtered_df = year_df[year_df['Date'].isin(random_dates)]
			year_df.sort_values('Date', inplace=True)
			last_day = year_df['Date'].tail(1).iloc[0]
			filtered_df = year_df[year_df['Date'] == last_day]
			data_df = pd.concat([data_df, filtered_df])
		else:
			print(f"Failed to download data for period")
	if not data_df.empty:
		# Sort the DataFrame by date to ensure correct plotting
		data_df.sort_values('Date', inplace=True)

		dates_selected = data_df['Date'].dt.date.unique()

		# Maturities for the x-axis
		maturities = ['1 Mo', '3 Mo', '6 Mo', '1 Yr', '2 Yr', '3 Yr', '5 Yr', '7 Yr', '10 Yr', '20 Yr', '30 Yr']

		# Plotting
		plt.figure(figsize=(14, 7))

		for date in dates_selected:
			data_on_date = data_df[data_df['Date'] == pd.Timestamp(date)]
			if not data_on_date.empty:
				plt.plot(maturities, data_on_date.iloc[0][maturities], marker='o', label=date.strftime('%m/%d/%Y'))

		plt.title('U.S. Treasury Yield Curve')
		plt.xlabel('Maturity')
		plt.ylabel('Yield (%)')
		plt.legend(title='Date', bbox_to_anchor=(1.05, 1), loc='upper left')
		y_min, y_max = plt.ylim()
		custom_ticks = np.arange(np.floor(y_min), np.ceil(y_max) + 0.5, 0.5)
		plt.gca().set_yticks(custom_ticks)
		plt.grid(True)
		plt.tight_layout()
		plt.show()
	else:
		print("No data")
asyncio.run(main())


