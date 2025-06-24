# Function to extract SQL query from response
import re
def extract_sql_from_response(response):
    queries = re.findall(r"SELECT.*?;", response, re.IGNORECASE | re.DOTALL)
    if queries:
        return queries[0].strip().rstrip(';')
    else:
        raise ValueError("No valid SQL query found.")