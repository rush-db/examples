#!/usr/bin/env python3
"""Generates the example memory log (made-up data, seed 11): what a personal assistant
agent wrote down about one user between 2026-07-01 and 2026-10-28. Each memory has the
sentence the agent stored plus the structured fields it extracted at write time."""
import datetime as dt
import json
import random

rng = random.Random(11)
start = dt.date(2026, 7, 1)
end = dt.date(2026, 10, 28)
days = (end - start).days + 1
mem = []


def day():
    return start + dt.timedelta(days=rng.randrange(days))


def add(date, kind, text, **fields):
    mem.append({"at": date.isoformat(), "kind": kind, "text": text, **fields})


routes = ["along the river", "around the park", "on the track", "up the hill road", "through the old town"]
for _ in range(30):
    d = day()
    km = round(rng.uniform(3, 14), 1)
    add(d, "run", f"Went for a {km} km run {rng.choice(routes)}.", distance_km=km)

groceries = ["Lidl", "Rimi", "Maxima"]
restaurants = ["Kolonāde", "Ezītis", "Pelmeni XL", "Big Bad Bagels", "Herbārijs", "Muusu"]
for _ in range(18):
    d = day()
    shop = rng.choice(groceries)
    amt = round(rng.uniform(18, 95), 2)
    add(d, "expense", f"Bought groceries at {shop} for ${amt}.", amount=amt, category="groceries", merchant=shop)
for _ in range(12):
    d = day()
    r = rng.choice(restaurants)
    amt = round(rng.uniform(14, 70), 2)
    add(d, "expense", f"Dinner at {r}, paid ${amt}.", amount=amt, category="restaurant", merchant=r)
big = [("a new bike helmet", "sports", "Decathlon", 129.0), ("flights to Lisbon", "travel", "airBaltic", 312.4),
       ("a standing desk", "home", "IKEA", 449.0), ("winter tyres", "car", "Vianor", 386.0),
       ("concert tickets", "leisure", "Bilesu Serviss", 118.0), ("a dentist bill", "health", "Smile Clinic", 160.0)]
for what, cat, merchant, amt in big:
    d = day()
    add(d, "expense", f"Paid ${amt} for {what} at {merchant}.", amount=amt, category=cat, merchant=merchant)

people = ["Dana", "Marek", "Ilze", "Tom"]
projects = ["Atlas", "Beacon", "Comet"]
for _ in range(22):
    d = day()
    who, proj = rng.choice(people), rng.choice(projects)
    add(d, "meeting", f"Met {who} about project {proj}.", person=who, project=proj)

for i in range(9):
    d = day()
    proj = rng.choice(projects)
    status = rng.choice(["open", "closed", "closed"])
    add(d, "ticket", f"Filed support ticket #{4100 + i} for project {proj}; it is {status}.", project=proj, status=status, ticket_no=4100 + i)

for d in (dt.date(2026, 7, 14), dt.date(2026, 9, 2), dt.date(2026, 10, 9)):
    add(d, "appointment", f"Dentist appointment at Smile Clinic on {d.isoformat()}.", provider="dentist")
add(dt.date(2026, 8, 20), "appointment", "Eye check at the optician on 2026-08-20.", provider="optician")

books = ["The Mythical Man-Month", "Designing Data-Intensive Applications", "Piranesi", "The Overstory", "Project Hail Mary", "A Philosophy of Software Design"]
for b in books:
    d = day()
    add(d, "book", f"Finished reading {b}.", title=b)

mem.sort(key=lambda m: (m["at"], m["text"]))
for i, m in enumerate(mem):
    m["memory_no"] = i + 1
print(json.dumps(mem, ensure_ascii=False, indent=1))
