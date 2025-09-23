"""
Quick HTML structure analysis for SumoDB.
"""

import requests
from bs4 import BeautifulSoup

def analyze_sumodb_structure():
    # Fetch first page
    url = 'https://sumodb.sumogames.de/Query_bout.aspx?show_form=0&year=2000-2025&m=on&j=on&rowcount=5&onlyw1=on&offset=0'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    # Find all tables
    tables = soup.find_all('table')
    print(f'Found {len(tables)} tables')

    # Look for data tables
    for i, table in enumerate(tables):
        rows = table.find_all('tr')
        if len(rows) > 10:  # Likely data table
            print(f'\nTable {i}: {len(rows)} rows')
            
            # Get headers
            header_row = rows[0] if rows else None
            if header_row:
                headers = [cell.get_text(strip=True) for cell in header_row.find_all(['th', 'td'])]
                print(f'Headers: {headers}')
            
            # Get first few data rows
            for j in range(1, min(4, len(rows))):
                cells = [cell.get_text(strip=True) for cell in rows[j].find_all(['td', 'th'])]
                print(f'Row {j}: {cells}')

if __name__ == "__main__":
    analyze_sumodb_structure()