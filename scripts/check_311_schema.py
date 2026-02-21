import requests
r = requests.get(
    "https://data.cityofnewyork.us/resource/erm2-nwe9.json",
    params={"$limit": 2, "$where": "complaint_type like '%Noise%'"},
    timeout=15,
)
print("Status:", r.status_code)
if r.ok:
    d = r.json()
    print("Rows:", len(d))
    if d:
        print("Columns:", list(d[0].keys()))
        for k in ["latitude", "longitude", "complaint_type", "Latitude", "Longitude", "incident_latitude", "incident_longitude"]:
            if k in d[0]:
                print(" ", k, ":", repr(d[0].get(k))[:70])
