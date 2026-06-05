import csv

with open("portfolio_sample.csv", "r") as file:
    reader = csv.DictReader(file)
    rows = list(reader)

print("Portfolio Data Loaded Successfully:")
for row in rows:
    print(row)
