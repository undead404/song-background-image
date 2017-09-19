#!/usr/bin/env python3
from decouple import config
import json
import lxml.cssselect
import lxml.html
import random
import requests
import subprocess
import urllib
API_KEY = config("API_KEY")
API_SECRET = config("API_SECRET")
LASTFM_USERNAME = config("LASTFM_USERNAME")


def encodeURIComponent(input_str, quotate=urllib.parse.quote):
    """
    Python equivalent of javascript's encodeURIComponent
    """
    return quotate(input_str.encode('utf-8'), safe='~()*!.\'')


def fetch_search_page(url):
    """
    Fetches Google ajax page by url
    """
    return lxml.html.fromstring(json.loads(requests.get(url,
                                                        headers={'User-Agent': get_ua()}).content.decode('utf-8'
                                                                                                         ))[1][1])


def get_current_song(lastfm_username):
    response = requests.get("http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={lastfm_username}&api_key={api_key}&format=json".format(
        api_key=API_KEY, lastfm_username=lastfm_username))
    data = json.loads(response.text)
    return data["recenttracks"]["track"][0]["artist"]["#text"], data["recenttracks"]["track"][0]["name"]


def get_img_url_by_song(song):
    search_query = "\"{artist_name}\" \"{track_title}\"".format(
        artist_name=song[0], track_title=song[1])
    search_url = "https://www.google.com.ua/search?async=_id:rg_s,_pms:qs&q={query}&start=0&asearch=ichunk&tbm=isch&tbs=isz:l".format(
        query=encodeURIComponent(search_query))
    search_page = fetch_search_page(search_url)
    return next(get_img_urls_from_page(search_page))


def get_img_url_from_meta(meta):
    """
    Returns image's url from a certain meta JSON
    """
    return json.loads(meta)['ou']


def get_img_urls_from_page(page,
                           META_SELECTOR=lxml.cssselect.CSSSelector('.rg_meta'
                                                                    )):
    """
    Returns images' urls from a page
    """
    return (get_img_url_from_meta(meta_elem.text_content())
            for meta_elem in META_SELECTOR(page))


def get_ua(ua_list=[
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20100101 Firefox/29.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
]):
    """
    Provides pseudo-random User-Agent from a saved list of ones
    """
    return random.choice(ua_list)


def set_background_image(img_url):
    subprocess.call(
        ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", img_url])


if __name__ == "__main__":
    song = get_current_song(lastfm_username=LASTFM_USERNAME)
    img_url = get_img_url_by_song(song)
    set_background_image(img_url)
