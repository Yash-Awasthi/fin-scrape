import hashlib
import re
from typing import List, Dict


def compute_dedupe_hash(title: str, source_name: str) -> str:
    title_norm = re.sub(r"[^\w\s]", "", title.strip().lower())
    title_norm = re.sub(r"\s+", " ", title_norm)
    content = f"{title_norm}|{source_name.strip().lower()}"
    return hashlib.sha256(content.encode()).hexdigest()


def extract_region_tags(text: str) -> List[str]:
    region_keywords = {
        "Middle East": [
            "iran", "iraq", "israel", "palestine", "saudi", "yemen",
            "syria", "lebanon", "qatar", "uae", "jordan", "egypt",
            "gulf", "persian", "hezbollah", "hamas", "irgc",
        ],
        "East Asia": [
            "china", "taiwan", "japan", "korea", "beijing", "seoul",
            "tokyo", "pla ", "pla navy", "strait", "south china sea",
            "east china sea", "xinjiang", "hong kong",
        ],
        "Europe": [
            "russia", "ukraine", "nato", " eu ", "european", "france",
            "germany", "uk ", "united kingdom", "britain", "poland",
            "moldova", "baltics", "finland", "sweden", "crimea",
        ],
        "South Asia": [
            "india", "pakistan", "afghanistan", "bangladesh",
            "kashmir", "himalaya", "sri lanka", "nepal",
        ],
        "Americas": [
            "united states", "usa", "america", "canada", "mexico",
            "brazil", "colombia", "venezuela", "latin america",
            "pentagon", "white house", "congress",
        ],
        "Africa": [
            "africa", "nigeria", "ethiopia", "kenya", "congo",
            "sudan", "somalia", "mali", "sahel", "sahara",
            "south africa", "mozambique",
        ],
        "Southeast Asia": [
            "asean", "vietnam", "philippines", "myanmar", "thailand",
            "indonesia", "malaysia", "cambodia", "singapore",
            "south china sea",
        ],
        "Central Asia": [
            "kazakhstan", "uzbekistan", "kyrgyzstan", "tajikistan",
            "turkmenistan", "central asia", "caucasus", "azerbaijan",
        ],
    }
    text_lower = text.lower()
    tags = []
    for region, keywords in region_keywords.items():
        if any(f" {kw}" in f" {text_lower}" or text_lower.startswith(kw) for kw in keywords):
            tags.append(region)
    return tags or ["Global"]


def _extract_names(text: str, known_names: List[str]) -> List[str]:
    """Extract known person/organization names from text (case-insensitive)."""
    text_lower = text.lower()
    found = []
    for name in known_names:
        if name.lower() in text_lower:
            found.append(name)
    return found


def _extract_location_phrases(text: str) -> List[str]:
    """Extract location-like phrases (capitalized words that are place names)."""
    # Match sequences of capitalized words (potential place names)
    candidates = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    # Filter out common non-location capitalized words
    skip = {"The", "A", "An", "This", "That", "These", "Those", "It", "He", "She",
            "They", "We", "You", "Our", "Their", "His", "Her", "Its", "My", "Your",
            "However", "Therefore", "Furthermore", "Moreover", "Nevertheless",
            "Additionally", "Meanwhile", "Although", "Because", "Since", "While",
            "After", "Before", "During", "Through", "Between", "Among", "Within",
            "Without", "About", "Above", "Below", "Under", "Over", "Again", "Then",
            "Now", "Here", "There", "Where", "When", "Why", "How", "What", "Which",
            "Who", "Whom", "Whose", "Both", "Each", "Every", "Some", "Any", "All",
            "No", "Not", "Only", "Just", "Still", "Already", "Also", "Very", "Too",
            "Much", "Many", "More", "Most", "Few", "Less", "Least", "Enough", "First",
            "Second", "Third", "Last", "Next", "Previous", "Final", "Initial",
            "New", "Old", "Good", "Great", "Large", "Small", "High", "Low", "Long",
            "Short", "Full", "Empty", "Open", "Closed", "Early", "Late", "Recent",
            "Former", "Latter", "Past", "Future", "Present", "Annual", "Monthly",
            "Daily", "Weekly", "Public", "Private", "Major", "Minor", "Senior",
            "Junior", "Former", "Latest", "Updated", "Related", "Additional", "Making",
            "According", "Following", "Including", "Regarding", "During",
            "November", "December", "January", "February", "March", "April", "May",
            "June", "July", "August", "September", "October", "Monday", "Tuesday",
            "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Today",
            "Yesterday", "Tomorrow", "Week", "Month", "Year"}
    return [c for c in candidates if c not in skip][:5]


def simple_entity_extract(text: str) -> Dict:
    countries = [
        "USA", "United States", "China", "Russia", "Iran", "Israel",
        "Ukraine", "Taiwan", "North Korea", "South Korea", "Saudi Arabia",
        "Turkey", "India", "Pakistan", "France", "Germany", "UK",
        "Japan", "Brazil", "Egypt", "Qatar", "UAE", "Iraq", "Syria",
        "Lebanon", "Yemen", "Afghanistan", "Libya", "Sudan", "Ethiopia",
        "Nigeria", "South Africa", "Venezuela", "Cuba", "Myanmar",
        "Vietnam", "Philippines", "Indonesia", "Malaysia", "Thailand",
    ]
    organizations = [
        "NATO", "UN", "IAEA", "EU", "WTO", "IMF", "World Bank",
        "OPEC", "SCO", "ASEAN", "AU", "Arab League", "IRGC", "PLA",
        "Pentagon", "CIA", "MI6", "FSB", "CSTO", "G7", "G20",
    ]
    known_persons = [
        "Biden", "Trump", "Xi", "Putin", "Zelensky", "Netanyahu",
        "Khamenei", "Kim Jong Un", "Modi", "Jinping", "Lavrov",
        "Blinken", "Austin", "Sullivan", "Macron", "Scholz",
        "Sunak", "Kishida", "Erdogan", "MBS", "MbS",
    ]
    text_lower = text.lower()
    found_countries = [c for c in countries if c.lower() in text_lower]
    found_orgs = [o for o in organizations if o.lower() in text_lower]
    found_persons = _extract_names(text, known_persons)
    found_locations = _extract_location_phrases(text)
    return {
        "countries": found_countries[:10],
        "persons": found_persons[:10],
        "organizations": found_orgs[:8],
        "locations": found_locations[:5],
    }
