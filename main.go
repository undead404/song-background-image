package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"html"
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/imroc/req"
	"github.com/joho/godotenv"
	lumberjack "gopkg.in/natefinch/lumberjack.v2"
)

type valueWithMbid struct {
	Text string `json:"#text"`
}

type recentTracksData struct {
	RecentTracks struct {
		Track []struct {
			Album  valueWithMbid `json:"album"`
			Artist valueWithMbid `json:"artist"`
			Name   string
		} `json:"track"`
	} `json:"recenttracks"`
}

type songData struct {
	Album  string
	Artist string
	Name   string
}

type bingImgMeta struct {
	URL string `json:"murl"`
}

var apiKey string
var availableHeaders []string
var lastfmUsername string
var localRand *rand.Rand

var mime = map[string]string{
	"image/jpeg": "jpg",
	"image/png": "png",
	"image/svg+xml": "svg",
	"image/xcf": "xcf",
};

func fetchSearchPage(searchURL string) (*goquery.Document, error) {
	request := req.New()
	response, err := request.Get(searchURL, getHeaders())
	if err != nil {
		return nil, err
	}
	responseBody := response.Response().Body
	document, err := goquery.NewDocumentFromReader(responseBody)
	if err != nil {
		return nil, err
	}
	return document, nil
}

func getCurrentSong(lastfmUsername string) (*songData, error) {
	request := req.New()
	response, err := request.Get(
		fmt.Sprintf(
			"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=%s&api_key=%s&format=json",
			lastfmUsername,
			apiKey,
		),
	)
	if err != nil {
		return nil, err
	}
	rtd := recentTracksData{}
	err = response.ToJSON(&rtd)
	if err != nil {
		log.Panic(err)
	}
	track := rtd.RecentTracks.Track[0]
	return &songData{
		Album:  track.Album.Text,
		Artist: track.Artist.Text,
		Name:   track.Name,
	}, nil
}

func getHeaders() http.Header {
	choice := localRand.Intn(len(availableHeaders))
	headers := make(http.Header)
	headers.Set(
		"User-Agent",
		availableHeaders[choice],
	)
	return headers
}

func getImgURLBySong(song *songData) (string, string, error) {
	queryBySong := fmt.Sprintf("%s - %s", song.Artist, song.Name)
	imgUrls, err := getImgURLsByQuery(queryBySong)
	if err != nil {
		return "", "", err
	}
	for _, imgURL := range imgUrls {
		ext := getExt(imgURL)
		if ext != "" {
			return imgURL, ext, nil
		}
	}
	queryByAlbum := fmt.Sprintf("%s - %s", song.Artist, song.Album)
	imgUrls, err = getImgURLsByQuery(queryByAlbum)
	if err != nil {
		return "", "", err
	}
	for _, imgURL := range imgUrls {
		ext := getExt(imgURL)
		if ext != "" {
			return imgURL, ext, nil
		}
	}
	queryByArtist := song.Artist
	imgUrls, err = getImgURLsByQuery(queryByArtist)
	if err != nil {
		return "", "", err
	}
	for _, imgURL := range imgUrls {
		ext := getExt(imgURL)
		if ext != "" {
			return imgURL, ext, nil
		}
	}
	return "", "", errors.New("No images found")
}

func getImgURLFromMeta(meta string) (string, error) {
	metaUnescaped := html.UnescapeString(meta)
	var imgData bingImgMeta
	err := json.Unmarshal([]byte(metaUnescaped), &imgData)
	if err != nil {
		return "", err
	}
	return imgData.URL, nil
}

func getImgURLsFromSearchPage(searchPage *goquery.Document) ([]string, error) {
	elems := searchPage.Find(".iusc").Nodes
	var imgURLs []string
	var meta string
	var imgURL string
	var err error
	for _, elem := range elems {
		for _, attr := range elem.Attr {
			if attr.Key == "m" {
				meta = attr.Val
				break
			}
		}
		imgURL, err = getImgURLFromMeta(meta)
		if err != nil {
			return nil, err
		}
		if imgURL != "" {
			imgURLs = append(imgURLs, imgURL)
		}
	}
	return imgURLs, nil
}

func getImgURLsByQuery(query string) ([]string, error) {
	searchURL := fmt.Sprintf(
		"https://www.bing.com/images/search?q=%s&qft=+filterui:imagesize-custom_1080_720&form=IRFLTR&first=1",
		url.PathEscape(query),
	)
	searchPage, err := fetchSearchPage(searchURL)
	if err != nil {
		return nil, err
	}
	imgURLs, err := getImgURLsFromSearchPage(searchPage)
	if err != nil {
		return nil, err
	}
	return imgURLs, nil
}

func getLastSong(dir string) string {
	lastSong, err := ioutil.ReadFile(fmt.Sprintf("%s/last-song.txt", dir))
	if err != nil {
		log.Printf("getLastSong: %s", err.Error())
		return ""
	}
	return string(lastSong)
}

func getExt(imgURL string) string {
	request := req.New()
	response, err := request.Head(imgURL, getHeaders())
	if err != nil {
		return ""
	}
	httpResponse := response.Response()
	if httpResponse.StatusCode < 200 || httpResponse.StatusCode >= 300 {
		return ""
	}
	mimeType := httpResponse.Header.Get("Content-Type")
	ext, found := mime[mimeType]
	if !found {
		return ""
	}
	return ext
}

func main() {
	dir := filepath.Dir(os.Args[0])
	logFileName := fmt.Sprintf("%s/logs/%s.txt", dir, time.Now().Format("2006-01-02"))
	log.SetOutput(&lumberjack.Logger{
		Filename:   logFileName,
		MaxSize:    1, // megabytes
		MaxBackups: 3,
	})
	err := godotenv.Load(fmt.Sprintf("%s/.env", dir))
	if err != nil {
		log.Panic("Error loading .env file")
	}
	randSource := rand.NewSource(time.Now().Unix())
	localRand = rand.New(randSource) // initialize local pseudorandom generator
	availableHeaders = []string{
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
		"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20100101 Firefox/29.0",
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36",
		"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0",
	}
	lastfmUsername = os.Getenv("LASTFM_USERNAME")
	apiKey = os.Getenv("API_KEY")
	song, err := getCurrentSong(lastfmUsername)
	if err != nil {
		log.Panic(err)
	}
	songString := fmt.Sprintf("%s - %s", song.Artist, song.Name)
	if getLastSong(dir) != songString {
		imgURL, ext, err := getImgURLBySong(song)
		if err != nil {
			log.Panic(err)
		}
		if imgURL != "" {
			err = setBackgroundImg(imgURL, ext)
			if err != nil {
				log.Panic(err)
			}
			err = saveLastSong(dir, songString)
			if err != nil {
				log.Panic(err)
			}
			log.Printf("%s - %s %s", song.Artist, song.Name, imgURL)
		} else {
			log.Printf("%s - %s: no images found", song.Artist, song.Name)
		}
	}
}

func saveLastSong(dir, songString string) error {
	err := ioutil.WriteFile(fmt.Sprintf("%s/last-song.txt", dir), []byte(songString), 0644)
	if err != nil {
		return fmt.Errorf("saveLastSong: %s", err.Error())
	}
	return nil
}

func setBackgroundImg(imgURL, ext string) error {
	var err error
	var stderr bytes.Buffer
	commandText := strings.Join(
		[]string{
			"export DBUS_SESSION_BUS_ADDRESS=$(grep -z DBUS_SESSION_BUS_ADDRESS /proc/$(pgrep gnome-session)/environ|cut -d= -f2-)",
			fmt.Sprintf("gsettings set org.gnome.desktop.background picture-uri \"%s\"", imgURL),
			"gsettings set org.gnome.desktop.background picture-options scaled",
		},
		" && ",
	)
	if os.Getenv("DESKTOP_SESSION") == "mate" {
		fmt.Println("MATE")
		commandText = strings.Join(
			[]string{
				"export DBUS_SESSION_BUS_ADDRESS=$(grep -z DBUS_SESSION_BUS_ADDRESS /proc/$(pgrep mate-session)/environ|cut -d= -f2-)",
				fmt.Sprintf("wget --ignore-length -O /home/undead404/wallpaper.temp \"%s\"", imgURL),
				fmt.Sprintf("cp /home/undead404/wallpaper.temp /home/undead404/wallpaper.%s", ext),
				fmt.Sprintf("gsettings set org.mate.background picture-filename \"'/home/undead404/wallpaper.%s'\"", ext),
			},
			" && ",
		)
	}
	// log.Println(commandText)
	command := exec.Command("sh", "-c", commandText)
	command.Stderr = &stderr
	err = command.Run()
	if err != nil {
		return errors.New(err.Error() + ": " + stderr.String())
	}
	// stdErr := stderr.String()
	// if stdErr != "" {
	// 	return errors.New("setBackgroundImg: " + stdErr)
	// }
	return nil
}
