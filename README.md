# song-background-image
Changes desktop background image according to the last song scrobbled by a last.fm user.

![My screenshot](https://raw.githubusercontent.com/undead404/song-background-image/master/screenshot.png)

## Usage
### 0. Clone this repository && change current directory to the script's folder
`git clone https://github.com/undead404/song-background-image.git` && cd song-background-image

### 1. Create in the script's folder an `.env` file with content as followed:
`API_KEY={your api key}` (request it [here](https://www.last.fm/api/account/create))
`API_SECRET={your api secret}` (corresponding to your API_KEY)
`LASTFM_USERNAME={your last.fm username}`

### 2. Install requirements

\# `pip3 install -r requirements.txt`

### 3. Set up cron to launch the script

$ `crontab -e`

I set the script to change my background image every minute:

`* * * * * /usr/bin/python3/ /home/undead404/projects/song-background-image/root.py >> /home/undead404/projects/song-background-image/log.txt`