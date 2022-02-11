import pytest
import requests
if __name__ == "__main__":
	import sys
	sys.path.append('../openpolicedata')
from openpolicedata import data
from openpolicedata import datasets

class TestProduct:
	def test_source_urls(self):
		for i in range(len(datasets)):
			url = datasets.iloc[i]["URL"]
			try:
				r = requests.head(url)
			except requests.exceptions.MissingSchema:
				if url[0:4] != "http":
					https = "https://"
					url = https + url
					r = requests.head(url)
				else:
					raise
			except:
				raise

			if r.status_code != 200:
				raise ValueError(f"Status code for {url} is {r.status_code}")


	def test_source_download_limitable(self):
		for i in range(len(datasets)):
			if self.can_be_limited(datasets.iloc[i]["DataType"], datasets.iloc[i]["URL"]):
				srcName = datasets.iloc[i]["SourceName"]
				state = datasets.iloc[i]["State"]
				src = data.Source(srcName, state=state)
				# For speed, set private limit parameter so that only a single entry is requested
				src._Source__limit = 1

				table = src.load_from_url(datasets.iloc[i]["Year"], datasets.iloc[i]["TableType"])
				assert len(table.table)==1
				if "date_field" in datasets.iloc[i]["LUT"]:
					assert datasets.iloc[i]["LUT"]["date_field"] in table.table
					assert table.table[datasets.iloc[i]["LUT"]["date_field"]].dtype.name == 'datetime64[ns]'
				if "jurisdiction_field" in datasets.iloc[i]["LUT"]:
					assert datasets.iloc[i]["LUT"]["jurisdiction_field"] in table.table
				
	def test_source_url_name_unlimitable(self):
		for i in range(len(datasets)):
			if not self.can_be_limited(datasets.iloc[i]["DataType"], datasets.iloc[i]["URL"]):
				ext = "." + datasets.iloc[i]["DataType"].lower()
				assert ext in datasets.iloc[i]["URL"]
				
				
	def test_jurisdiction_filter(self):
		src = data.Source("Virginia Community Policing Act")
		jurisdiction="Fairfax County Police Department"
		# For speed, set private limit parameter so that only a single entry is requested
		src._Source__limit = 100
		table = src.load_from_url(2021, jurisdiction_filter=jurisdiction)
		
		assert len(table.table)==100
		assert table.table[table._jurisdiction_field].nunique()==1
		assert table.table.iloc[0][table._jurisdiction_field] == jurisdiction


	@pytest.mark.slow(reason="This is a slow test and should only be run before a major commit.")
	def test_source_download_not_limitable(self):
		for i in range(len(datasets)):
			if not self.can_be_limited(datasets.iloc[i]["DataType"], datasets.iloc[i]["URL"]):
				srcName = datasets.iloc[i]["SourceName"]
				state = datasets.iloc[i]["State"]
				src = data.Source(srcName, state=state)

				year = datasets.iloc[i]["Year"]
				table_type = datasets.iloc[i]["TableType"]
				try:
					table = src.load_from_url(year, table_type)
				except:
					raise ValueError(f"Error loading CSV {srcName}, year={year}, table_type={table_type}")

				assert len(table.table)>1
				if "date_field" in datasets.iloc[i]["LUT"]:
					assert datasets.iloc[i]["LUT"]["date_field"] in table.table
					assert table.table[datasets.iloc[i]["LUT"]["date_field"]].dtype.name == 'datetime64[ns]'
				if "jurisdiction_field" in datasets.iloc[i]["LUT"]:
					assert datasets.iloc[i]["LUT"]["jurisdiction_field"] in table.table


	# TODO: Future tests on date filtering, get year and jurisdictions functions, and a couple of testings that read in the whole table...
	def can_be_limited(self, table_type, url):
		if table_type == "GeoJSON" or (table_type == "CSV" and ".zip" in url):
			return False
		elif (table_type == "ArcGIS" or table_type == "Socrata" or table_type == "CSV"):
			return True
		else:
			raise ValueError("Unknown table type")

if __name__ == "__main__":
	tp = TestProduct()
	tp.test_source_download_limitable()