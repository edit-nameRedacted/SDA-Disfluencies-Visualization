#!/usr/bin/env python3
"""Build the data file behind the topic-umbrella bar charts.

Reads conversations.csv from the folder written by extract_swda.py and writes one
JSON file: one record per parsed conversation with its topic, its umbrella
category, and its word count split by sentence type.

    python make_topic_bars.py swda_d3 topic_bars.json

The umbrella categories are an editorial grouping, not part of the corpus.
To regroup, edit UMBRELLAS below: each umbrella lists the corpus topic labels
that belong to it, paired with the name to display.
"""
import csv, json, os, sys

TYPES = ["complete_fluent", "complete_disfluent", "unfinished", "fragment", "response_token"]

UMBRELLAS = {
    "Entertainment & media": {
        "BOOKS AND LITERATURE": "Books and literature", "MAGAZINES": "Magazines",
        "MOVIES": "Movies", "MUSIC": "Music", "NEWS MEDIA": "News media",
        "TV PROGRAMS": "TV programs"},
    "Sports & outdoors": {
        "BASEBALL": "Baseball", "BASKETBALL": "Basketball",
        "BOATING AND SAILING": "Boating and sailing", "CAMPING": "Camping",
        "EXERCISE AND FITNESS": "Exercise and fitness", "FISHING": "Fishing",
        "FOOTBALL": "Football", "GOLF": "Golf"},
    "Home & hobbies": {
        "AUTO REPAIRS": "Auto repairs", "GARDENING": "Gardening",
        "HOBBIES AND CRAFTS": "Hobbies and crafts", "HOME REPAIRS": "Home repairs",
        "HOUSES": "Houses", "PAINTING": "Painting", "PETS": "Pets",
        "RECIPES/FOOD/COOKING": "Recipes, food and cooking", "WOODWORKING": "Woodworking"},
    "Family": {
        "CARE OF THE ELDERLY": "Care of the elderly", "CHILD CARE": "Child care",
        "FAMILY LIFE": "Family life", "FAMILY REUNIONS": "Family reunions"},
    "Money & work": {
        "BUYING A CAR": "Buying a car", "CONSUMER GOODS": "Consumer goods",
        "CREDIT CARD USE": "Credit card use", "FAMILY FINANCE": "Family finance",
        "JOB BENEFITS": "Job benefits"},
    "Politics & world affairs": {
        "ELECTIONS AND VOTING": "Elections and voting",
        "ETHICS IN GOVERNMENT": "Ethics in government", "FEDERAL BUDGET": "Federal budget",
        "IMMIGRATION": "Immigration", "LATIN AMERICA": "Latin America",
        "MIDDLE EAST": "Middle East", "POLITICS": "Politics",
        "PUERTO RICAN STTEHD": "Puerto Rican statehood", "SOVIET UNION": "Soviet Union",
        "SVGS & LOAN BAILOUT": "Savings and loan bailout", "TAXES": "Taxes",
        "UNIVERSAL HEALTH INS": "Universal health insurance",
        "UNIVERSAL PBLIC SERV": "Universal public service", "VIETNAM WAR": "Vietnam War"},
    "Law & justice": {
        "CAPITAL PUNISHMENT": "Capital punishment", "CRIME": "Crime",
        "DRUG TESTING": "Drug testing", "GUN CONTROL": "Gun control",
        "RIGHT TO PRIVACY": "Right to privacy", "TRIAL BY JURY": "Trial by jury"},
    "Education & society": {
        "AIDS": "AIDS", "CHOOSING A COLLEGE": "Choosing a college",
        "PUBLIC EDUCATION": "Public education", "SOCIAL CHANGE": "Social change",
        "WOMEN'S ROLES": "Women's roles"},
    "Science & environment": {
        "AIR POLLUTION": "Air pollution", "COMPUTERS": "Computers",
        "METRIC SYSTEM": "Metric system", "RECYCLING": "Recycling",
        "SPACE FLIGHT AND EXPLORATION": "Space flight and exploration"},
    "Small talk": {
        "CLOTHING AND DRESS": "Clothing and dress", "RESTAURANTS": "Restaurants",
        "VACATION SPOTS": "Vacation spots", "WEATHER CLIMATE": "Weather and climate"},
}
LOOKUP = {raw: (shown, umbrella) for umbrella, topics in UMBRELLAS.items() for raw, shown in topics.items()}


def main(src, dest):
    out, unknown = [], set()
    for r in csv.DictReader(open(os.path.join(src, "conversations.csv"), newline="", encoding="utf-8")):
        if r["has_parse"] != "1":
            continue                  # sentence types need the Treebank parse
        if r["topic"] not in LOOKUP:
            unknown.add(r["topic"])
        shown, umbrella = LOOKUP.get(r["topic"], (r["topic"].capitalize(), "Other"))
        out.append({"id": int(r["conversation_no"]), "topic": shown, "umbrella": umbrella,
                    "year": r["year"], "w": [int(r["stw_" + t]) for t in TYPES]})
    if unknown:
        print("Topics with no umbrella (filed under Other):", sorted(unknown))
    json.dump({"types": TYPES, "conversations": out}, open(dest, "w"), separators=(",", ":"))
    print("Wrote %s: %d conversations" % (dest, len(out)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
