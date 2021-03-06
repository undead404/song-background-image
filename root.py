#!/env/bin python3
import json
from decouple import config
import html
import os
import random
import subprocess
import lxml.cssselect
import lxml.html
import requests
import urllib
API_KEY = config("API_KEY")
API_SECRET = config("API_SECRET")
LASTFM_USERNAME = config("LASTFM_USERNAME")
BLACKLISTED_DOMAINS = []


def encodeURIComponent(input_str, quotate=urllib.parse.quote):
    """
    Python equivalent of javascript's encodeURIComponent
    """
    return quotate(input_str.encode('utf-8'), safe='~()*!.\'')


def fetch_search_page(url):
    """
    Fetches Bing page by url
    """
    return lxml.html.fromstring(requests.get(url, headers={
        'User-Agent': get_ua()}).content)


def get_current_song(lastfm_username):
    response = requests.get(
        "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks"
        "&user={lastfm_username}&api_key={api_key}&format=json".format(
            api_key=API_KEY, lastfm_username=lastfm_username))
    data = json.loads(response.text)
    return data["recenttracks"]["track"][0][
        "artist"]["#text"], data["recenttracks"]["track"][0]["name"], data[
            "recenttracks"]["track"][0]["album"]['#text']


def get_img_url_by_song(song):
    try:
        query_by_song = "{artist_name} {track_title}".format(
            artist_name=song[0], track_title=song[1])
        search_url = (
            "https://www.bing.com/images/search?q={query}&qft=+filterui:imagesize-custom_1080_1080&form=IRFLTR&first=1").format(
            query=encodeURIComponent(query_by_song))
        search_page = fetch_search_page(search_url)
        img_urls = get_img_urls_from_page(search_page)
        img_url = next(img_urls)
        while is_blacklisted(img_url) or not is_available(img_url):
            img_url = next(img_urls)
        return img_url
    except StopIteration:
        try:
            query_by_album = "{artist_name} {album_title}".format(
                artist_name=song[0], album_title=song[2])
            search_url = (
                "https://www.bing.com/images/search?q={query}&qft=+filterui:imagesize-custom_1080_1080&form=IRFLTR&first=1").format(
                query=encodeURIComponent(query_by_album))
            # print(search_url)
            img_urls = get_img_urls_from_page(search_page)
            img_url = next(img_urls)
            while is_blacklisted(img_url) or not is_available(img_url):
                img_url = next(img_urls)
            return img_url
        except StopIteration:
            try:
                query_by_artist = "{artist_name}".format(
                    artist_name=song[0])
                search_url = (
                    "https://www.bing.com/images/search?q={query}&qft=+filterui:imagesize-custom_1080_1080&form=IRFLTR&first=1").format(
                    query=encodeURIComponent(query_by_artist))
                # print(search_url)
                img_urls = get_img_urls_from_page(search_page)
                img_url = next(img_urls)
                while is_blacklisted(img_url) or not is_available(img_url):
                    img_url = next(img_urls)
                return img_url
            except StopIteration:
                return None


def get_img_url_from_meta(meta):
    """
    Returns image's url from a certain meta JSON
    """
    img_url = json.loads(html.unescape(meta))['murl']
    return img_url


def get_img_urls_from_page(page,
                           META_SELECTOR=lxml.cssselect.CSSSelector('.iusc'
                                                                    )):
    """
    Returns images' urls from a page
    """
    for meta_elem in META_SELECTOR(page):
        meta = meta_elem.attrib['m']
        yield get_img_url_from_meta(meta)


def get_last_log_record():
    try:
        with open("/home/undead404/projects/song-background-image/log.txt",
                  ) as logfile:
            return logfile.readlines()[-1]
    except IndexError:
        return ""


def get_ua(ua_list=[(
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, '
        'like Gecko) Chrome/34.0.1847.131 Safari/537.36'), (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'), (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14'
        ' (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14'), (
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20100101 '
        'Firefox/29.0'), (
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, '
        'like Gecko) Chrome/34.0.1847.137 Safari/537.36'), (
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 '
        'Firefox/28.0')
]):
    """
    Provides pseudo-random User-Agent from a saved list of ones
    """
    return random.choice(ua_list)


def is_available(url):
    try:
        return requests.head(url, headers={
            "User-Agent": get_ua()
        }).status_code == 200
    except Exception:
        return False


def is_blacklisted(url):
    for blacklisted_domain in BLACKLISTED_DOMAINS:
        if blacklisted_domain in url:
            return True
    return False


def set_background_image(img_url):
    shell = subprocess.Popen(
        ["pgrep", "gnome-session"], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    out, err = shell.communicate()
    pid = int(out)
    shell = subprocess.Popen(
        "/bin/bash", stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    COMMANDS = [
        "export DBUS_SESSION_BUS_ADDRESS=$(grep -z DBUS_SESSION_BUS_ADDRESS "
        "/proc/{pid}/environ|cut -d= -f2-)".format(
            pid=pid),
        "gsettings set org.gnome.desktop.background picture-uri "
        "'{img_url}'".format(
            img_url=img_url),
        "gsettings set org.gnome.desktop.background picture-options scaled"
    ]
    shell.communicate("; ".join(COMMANDS).encode())


if __name__ == "__main__":
    try:
        song = get_current_song(lastfm_username=LASTFM_USERNAME)
        song_string = "{artist_name} - {track_title}".format(
            artist_name=song[0], track_title=song[1])
        if song_string not in get_last_log_record():
            img_url = get_img_url_by_song(song)
            if img_url is not None:
                set_background_image(img_url)
                print(song[0], "-", song[1], img_url)
    except requests.exceptions.RequestException as error:
        print('error', error)
