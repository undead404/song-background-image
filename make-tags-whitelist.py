import json
import re
import requests
URL = ("https://raw.githubusercontent.com/undead404/exmusic/master/"
       "cult_artists.json")
cult_artists = requests.get(URL).json()
whitelisted_tags = set()
for cult_artist in cult_artists:
    for tag in cult_artists[cult_artist]:
        whitelisted_tags.add(tag)
whitelisted_tags = list(whitelisted_tags)
whitelisted_tags.sort()

TAG_PATTERN = re.compile('[^a-zA-Z0-9]+')


def normalize_tag(tag):
    return TAG_PATTERN.sub(' ', tag.lower()).strip()


tags = {normalize_tag(tag): tag.title().strip() for tag in whitelisted_tags}
with open('tags.json', 'w') as tags_file:
    json.dump(tags, tags_file)
