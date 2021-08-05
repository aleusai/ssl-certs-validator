import requests
from multiprocessing import Pool
import os
import random

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

payloads = [ { "url": "https://facebook.com", "toPrometheus": "False"}, 
    { "url": "https://facebook.com", "toPrometheus": "False"}, 
    { "url": "https://google.com", "toPrometheus": "False"}, 
    { "url": "https://amazon.com", "toPrometheus": "False"}, 
    { "url": "https://instagram.com", "toPrometheus": "False"}, 
    { "url": "https://yahoo.com", "toPrometheus": "False"}, 
    { "url": "https://microsoft.com", "toPrometheus": "False"}, 
    { "url": "https://hotmail.com", "toPrometheus": "False"},
    { "url": "https://gmail.com", "toPrometheus": "False"}
    ] 
headers = {"Accept": "application/json", "Content-type": "application/json"}




def fetch(i):
    index = random.randint(0, 8)
    payload = payloads[index]
    print('payload=', payload)
    return requests.post("http://127.0.0.1:5000/api/local", json=payload, 
    auth=(USERNAME, PASSWORD) ).elapsed.microseconds

if __name__ == "__main__":
    with Pool(10) as p:
        res_times = p.map(fetch, list(range(100)))

    avg_time = sum(res_times) / len(res_times) if len(res_times) else 0

    print(
        f"On average each request took {round(avg_time/1000)} milliseconds.\n\n")
