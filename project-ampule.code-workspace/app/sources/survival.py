import requests
from bs4 import BeautifulSoup

SURVIVAL_WEB_SOURCES = [
	("readygov:kit", "https://www.ready.gov/kit"),
	("readygov:water", "https://www.ready.gov/water"),
	("readygov:shelter", "https://www.ready.gov/shelter"),
	("readygov:first-aid", "https://www.ready.gov/first-aid"),
]

def fetch_survival_page(url):
	headers = {"User-Agent": "ProjectAmpule/1.0"}
	response = requests.get(url, headers=headers, timeout=10)
	if response.status_code != 200:
		return None

	soup = BeautifulSoup(response.text, "html.parser")
	paragraphs = [paragraph.get_text(" ", strip=True) for paragraph in soup.find_all("p")]
	text = "\n".join(paragraph for paragraph in paragraphs if paragraph)
	return text or None

def iter_survival_documents():
	for source_name, url in SURVIVAL_WEB_SOURCES:
		try:
			text = fetch_survival_page(url)
		except Exception as exc:
			print(f"Error fetching survival source {url}: {exc}")
			continue

		if text:
			yield source_name, text
