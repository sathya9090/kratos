r"""Air quality prediction helper script

This script reads a Google Sheet into a pandas DataFrame and produces
basic summaries and visualizations. It is written to work in two modes:

1. Google Colab (interactive) -- will attempt to use `google.colab.auth`.
2. Local / CI -- uses a service account JSON file (path provided by
   the SERVICE_ACCOUNT_JSON environment variable or `service_account.json`).

Notes about common problems and fixes:
- Do NOT place pip install commands inside a .py file (that causes syntax
  errors). Use a `requirements.txt` and install via the shell.
- Colab-specific imports (`google.colab`) will fail locally; this script
  falls back to a service-account flow when not running in Colab.


Usage examples (PowerShell):

	# Install deps once
	pip install -r requirements.txt

	# If using a service account JSON locally:
	$env:SERVICE_ACCOUNT_JSON = 'C:\path\to\service_account.json'
	python "air quality prediction.py" --url "<spreadsheet_url>" --worksheet 0

	# Or provide the spreadsheet id directly:
	python "air quality prediction.py" --id "<spreadsheet_id>" --worksheet 0 --save-plots

	# Or run locally against a CSV or Excel file you added to the repo:
	python "air quality prediction.py" --csv ".\data\my_data.csv" --save-plots
	python "air quality prediction.py" --csv ".\data\my_data.xlsx" --sheet "Sheet1" --save-plots

"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

import gspread
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns


def get_gspread_client() -> gspread.Client:
	"""Return an authorized gspread client.

	Tries Colab authorization first; if that fails, tries a service account
	JSON file pointed to by the SERVICE_ACCOUNT_JSON env var or
	'./service_account.json'.
	"""
	# Try Colab flow (interactive)
	try:
		from google.colab import auth  # type: ignore

		print("Detected Colab environment: running interactive auth()")
		auth.authenticate_user()
		from google.auth import default

		creds, _ = default()
		return gspread.authorize(creds)
	except Exception:
		# Not in Colab or Colab auth failed; fall back to service account
		pass

	# Service account flow
	sa_path = os.environ.get("SERVICE_ACCOUNT_JSON", "service_account.json")
	if not os.path.exists(sa_path):
		raise FileNotFoundError(
			"Service account JSON not found. Set SERVICE_ACCOUNT_JSON env var "
			"or place 'service_account.json' next to the script."
		)

	from google.oauth2.service_account import Credentials

	scopes = [
		"https://www.googleapis.com/auth/spreadsheets",
		"https://www.googleapis.com/auth/drive",
	]
	creds = Credentials.from_service_account_file(sa_path, scopes=scopes)
	return gspread.authorize(creds)


def extract_spreadsheet_id(url: str) -> str:
	"""Extract spreadsheet id from a Google Sheets URL or return the input if it looks like an id."""
	if "/d/" in url:
		try:
			return url.split("/d/")[1].split("/edit")[0].split("/")[0]
		except Exception:
			raise ValueError("Couldn't parse spreadsheet id from URL")
	return url


def load_sheet_data(client: gspread.Client, spreadsheet_id: str, worksheet_index: int = 0) -> pd.DataFrame:
	sh = client.open_by_key(spreadsheet_id)
	worksheet = sh.get_worksheet(worksheet_index)
	if worksheet is None:
		raise IndexError(f"Worksheet index {worksheet_index} not found")
	data_list = worksheet.get_all_values()
	if not data_list or len(data_list) < 2:
		raise ValueError("Spreadsheet contains no data or no header row")
	df = pd.DataFrame(data_list[1:], columns=data_list[0])
	return df


def load_local_data(path: str, sheet: Optional[str] = None, sep: str = ",") -> pd.DataFrame:
	"""Load a local CSV or Excel file into a DataFrame.

	- If the file ends with .csv (or .txt), uses `pd.read_csv` with provided `sep`.
	- If the file ends with .xls/.xlsx, uses `pd.read_excel` and optional `sheet`.
	"""
	if not os.path.exists(path):
		raise FileNotFoundError(f"Local data file not found: {path}")

	lower = path.lower()
	if lower.endswith(".csv") or lower.endswith(".txt"):
		return pd.read_csv(path, sep=sep)
	if lower.endswith(".xls") or lower.endswith(".xlsx"):
		# If sheet is provided, pass it; otherwise let pandas load the first sheet
		if sheet:
			df = pd.read_excel(path, sheet_name=sheet)
		else:
			df = pd.read_excel(path)

		# pd.read_excel may return a dict if multiple sheets were requested;
		# ensure we return a single DataFrame
		if isinstance(df, dict):
			# pick the first sheet
			first_key = next(iter(df.keys()))
			return df[first_key]
		return df

	# Fallback: try read_csv first, then read_excel
	try:
		return pd.read_csv(path, sep=sep)
	except Exception:
		df = pd.read_excel(path, sheet_name=sheet) if sheet else pd.read_excel(path)
		if isinstance(df, dict):
			first_key = next(iter(df.keys()))
			return df[first_key]
		return df


def summarize_and_plot(df: pd.DataFrame, save_plots: bool = False, out_prefix: str = "aq_") -> None:
	print("\n✅ Data loaded successfully. Showing first 5 rows:\n")
	print(df.head())

	print("\nDataset info:")
	df.info()

	print("\nStatistical summary (numeric columns):")
	print(df.describe())

	# Convert to numeric where possible
	numeric = df.apply(pd.to_numeric, errors="coerce")

	# Guard: need at least 2 numeric columns for a correlation heatmap
	num_numeric = numeric.select_dtypes(include=["number"]).shape[1]
	if num_numeric == 0:
		print("No numeric columns found — skipping plots.")
		return

	sns.set(style="whitegrid")
	# Heatmap of up to first 5 numeric columns
	cols = numeric.select_dtypes(include=["number"]).columns[:5]
	plt.figure(figsize=(10, 6))
	sns.heatmap(numeric[cols].corr(), annot=True, cmap="coolwarm")
	plt.title("Correlation Heatmap of First 5 Numeric Columns")
	if save_plots:
		heat_path = out_prefix + "heatmap.png"
		plt.savefig(heat_path, bbox_inches="tight")
		print(f"Saved heatmap to {heat_path}")
	else:
		plt.show()
	plt.close()

	# Histogram of first numeric column
	first_col = cols[0]
	plt.figure(figsize=(10, 6))
	numeric[first_col].hist(bins=30, edgecolor="black")
	plt.title(f"Histogram of {first_col}")
	plt.xlabel("Values")
	plt.ylabel("Frequency")
	if save_plots:
		path = out_prefix + "histogram.png"
		plt.savefig(path, bbox_inches="tight")
		print(f"Saved histogram to {path}")
	else:
		plt.show()
	plt.close()

	# Boxplot for the first numeric column
	plt.figure(figsize=(10, 6))
	sns.boxplot(x=numeric[first_col])
	plt.title(f"Boxplot for {first_col}")
	if save_plots:
		path = out_prefix + "boxplot.png"
		plt.savefig(path, bbox_inches="tight")
		print(f"Saved boxplot to {path}")
	else:
		plt.show()
	plt.close()


def main(argv: Optional[list[str]] = None) -> int:
	parser = argparse.ArgumentParser(description="Load Google Sheet or local file and show basic summaries/plots")
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument("--url", help="Full Google Sheets URL")
	group.add_argument("--id", help="Spreadsheet ID (the long id in the URL)")
	group.add_argument("--csv", help="Path to a local CSV or Excel file to load")
	parser.add_argument("--worksheet", type=int, default=0, help="Worksheet index (default 0)")
	parser.add_argument("--sheet", help="Excel sheet name to load (when using --csv with an xlsx file)")
	parser.add_argument("--sep", default=",", help="CSV separator (default ',')")
	parser.add_argument("--save-plots", action="store_true", help="Save plots to files instead of showing them")
	args = parser.parse_args(argv)

	# If running against a local file, avoid creating a gspread client
	if args.csv:
		try:
			df = load_local_data(args.csv, sheet=args.sheet, sep=args.sep)
		except Exception as exc:
			print("Failed to load local data file:", exc)
			return 3
	else:
		try:
			client = get_gspread_client()
		except Exception as exc:
			print("Failed to create gspread client:", exc)
			return 2

		spreadsheet_id = extract_spreadsheet_id(args.url) if args.url else args.id

		try:
			df = load_sheet_data(client, spreadsheet_id, args.worksheet)
		except Exception as exc:
			print("Failed to load sheet data:", exc)
			return 3

	summarize_and_plot(df, save_plots=args.save_plots)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
