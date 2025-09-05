import requests

# URL of your running Flask API
url = "http://127.0.0.1:8000/query"

# Your query
data = {
    "query": "Find artisan Amit Patel"
}

# Send POST request
response = requests.post(url, json=data)

# Print response from API
print(response.json())
