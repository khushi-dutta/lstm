import random
import csv
from datetime import datetime, timedelta

# Geotags for Kerala's 14 districts
GEO = {
    'Thiruvananthapuram': (8.5241, 76.9366),
    'Kollam':            (8.8932, 76.6141),
    'Alappuzha':         (9.4981, 76.3388),
    'Kottayam':          (9.5916, 76.5222),
    'Ernakulam':         (10.0827, 76.2711),
    'Thrissur':          (10.5276, 76.2144),
    'Palakkad':          (10.7867, 76.6548),
    'Malappuram':        (11.2588, 76.3183),
    'Kozhikode':         (11.2588, 75.7804),
    'Wayanad':           (11.6854, 76.1320),
    'Kannur':            (11.8745, 75.3704),
    'Kasaragod':         (12.4990, 75.0577),
    'Pathanamthitta':    (9.2646, 76.7874),
    'Idukki':            (9.8501, 77.0166),
}

# Typical water-level ranges per district (m)
LEVEL_RANGES = {
    'Thiruvananthapuram': (2.5, 6),
    'Kollam':            (3,   7),
    'Alappuzha':         (2,   6.5),
    'Kottayam':          (2,   7.5),
    'Ernakulam':         (2,   8),
    'Thrissur':          (2,   8),
    'Palakkad':          (1.5, 6),
    'Malappuram':        (2.5, 8.5),
    'Kozhikode':         (2.5, 8),
    'Wayanad':           (3,   7),
    'Kannur':            (2.5, 7.5),
    'Kasaragod':         (2.3, 7),
    'Pathanamthitta':    (2,   7),
    'Idukki':            (2.5, 9),
}

# Flood-alert thresholds
# Yellow: wl<5 & pr<150; Orange: 5≤wl<7 & 150≤pr<200; Red: wl≥7 or pr≥200
def alert_flag(wl, pr):
    if wl >= 7 or pr >= 200:
        return 'Red'
    if wl >= 5 and pr >= 150:
        return 'Orange'
    return 'Yellow'

start = datetime(2014, 6, 1)
end   = datetime(2025, 8, 31)
delta = timedelta(days=1)

with open('kerala_flood_data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'date','city','latitude','longitude',
        'water_level_m','precipitation_mm','flood_alert_flag'
    ])

    curr = start
    while curr <= end:
        for city, (lat, lon) in GEO.items():
            wl = round(random.uniform(*LEVEL_RANGES[city]), 2)
            # Monsoon months more rainfall
            mean_pr = 180 if curr.month in (6,7,8) else 120
            pr = max(0, round(random.gauss(mean_pr, 40), 2))
            flag = alert_flag(wl, pr)
            writer.writerow([
                curr.strftime('%Y-%m-%d'), city, lat, lon, wl, pr, flag
            ])
        curr += delta

print("Generated kerala_flood_data.csv with daily records from 2014–2025.")
