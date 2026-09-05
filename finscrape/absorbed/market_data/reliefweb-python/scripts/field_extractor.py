import requests
from bs4 import BeautifulSoup

url = "https://apidoc.reliefweb.int/fields-tables"

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

result = {}

# Step 1: Loop over all tables
for table in soup.find_all("table"):
    parent_with_id = table.find_parent(id=True)
    table_id = parent_with_id["id"] if parent_with_id else "unknown"

    rows = table.find_all("tr")[1:]  # Skip header row
    all_fields = []
    for row in rows:
        td = row.find("td")
        if td:
            field_name = td.get_text(strip=True).replace("\xa0", "")
            all_fields.append(field_name)

    # Step 2: Categorize into nested and un-nested
    final_fields = list(
        set([field.split(".")[0] if "." in field else field for field in all_fields])
    )

    result[table_id] = final_fields

# Step 3: Print results
print(result)
