import { API_KEY } from '@env';
import chalk from 'chalk';
// import compact from 'lodash/compact';
import filter from 'lodash/filter';
import fromPairs from 'lodash/fromPairs';
import get from 'lodash/get';
import includes from 'lodash/includes';
import isEmpty from 'lodash/isEmpty';
import keys from 'lodash/keys';
import map from 'lodash/map';
// import mapValues from 'lodash/mapValues';
// import sum from 'lodash/sum';
// import values from 'lodash/values';
import Mustache from 'mustache';
import { data as ARTISTS_TAGS } from '../../artists.json';
import { data as SONGS_TAGS } from '../../songs.json';
import TAGS from '../../tags.json';
import {
  ALBUM_TOP_TAGS,
  ARTIST_TOP_TAGS,
  TRACK_GET_INFO,
  TRACK_TOP_TAGS,
} from './url-patterns.json';
import requestData from './utils/request-data';
import normalizeTagName from './utils/normalize-tag-name';

const { CACHE_ONLY } = process.env;

const ALLOWED_TAGS = keys(TAGS);

export default class Track {
  album = undefined;

  artist = undefined;

  name = undefined;

  tags = undefined;

  constructor(artist, name) {
    this.artist = artist;
    this.name = name;
    this.tags = get(SONGS_TAGS, `${artist}.${name}`);
  }

  async acquireAlbumTags() {
    console.debug(
      `${chalk.inverse(
        `${this.artist} - ${this.name}`,
      )}: ${chalk.inverse.yellow('acquireAlbumTags()')}`,
    );
    const albumTopTagsUrl = Mustache.render(ALBUM_TOP_TAGS, {
      album: encodeURIComponent(this.album),
      api_key: API_KEY,
      artist: encodeURIComponent(this.artist),
    });
    const albumData = await requestData(albumTopTagsUrl, 'toptags');
    const albumTags = filter(
      get(albumData, 'tag'),
      (tag) => TAGS[normalizeTagName(tag.name)],
    );
    if (!isEmpty(albumTags)) {
      this.tags = fromPairs(
        map(albumTags, (tag) => [TAGS[normalizeTagName(tag.name)], tag.count]),
      );
    }
  }

  async acquireArtistTags() {
    console.debug(
      `${chalk.inverse(
        `${this.artist} - ${this.name}`,
      )}: ${chalk.inverse.yellow('acquireArtistTags()')}`,
    );
    const artistTopTagsUrl = Mustache.render(ARTIST_TOP_TAGS, {
      api_key: API_KEY,
      artist: encodeURIComponent(this.artist),
    });
    const artistData = await requestData(artistTopTagsUrl, 'toptags');
    const artistTags = filter(get(artistData, 'tag'), (tag) =>
      includes(ALLOWED_TAGS, normalizeTagName(tag.name)),
    );
    if (!isEmpty(artistTags)) {
      this.tags = fromPairs(
        map(artistTags, (tag) => [TAGS[normalizeTagName(tag.name)], tag.count]),
      );
    }
  }

  async acquireTags() {
    console.debug(
      `${chalk.inverse(
        `${this.artist} - ${this.name}`,
      )}: ${chalk.inverse.yellow(`acquireTags()`)}`,
    );
    if (!CACHE_ONLY && !this.tags) {
      await this.acquireTrackTags();
    }
    if (!CACHE_ONLY && isEmpty(this.tags) && this.album) {
      await this.acquireAlbumTags();
    }
    if (isEmpty(this.tags)) {
      this.initArtistTags();
    }
    if (!CACHE_ONLY && !this.tags) {
      await this.acquireArtistTags();
    }
    if (!this.tags) {
      this.tags = {};
    }
    return this.tags;
  }

  async acquireTrackTags() {
    console.debug(
      `${chalk.inverse(
        `${this.artist} - ${this.name}`,
      )}: ${chalk.inverse.yellow('acquireTrackTags()')}`,
    );
    const trackInfoUrl = Mustache.render(TRACK_GET_INFO, {
      api_key: API_KEY,
      artist: encodeURIComponent(this.artist),
      track: encodeURIComponent(this.name),
    });
    const trackData = await requestData(trackInfoUrl, 'track');
    if (!trackData) {
      return {};
    }
    this.album = get(trackData, 'album.name', this.album);
    const trackTopTagsUrl = Mustache.render(TRACK_TOP_TAGS, {
      api_key: API_KEY,
      artist: encodeURIComponent(this.artist),
      track: encodeURIComponent(this.name),
    });
    const trackTopTagsData = await requestData(trackTopTagsUrl, 'toptags');
    const trackTags = get(trackTopTagsData, 'tag');
    if (trackTags) {
      this.tags = fromPairs(
        filter(
          map(trackTags, (tag) => [
            TAGS[normalizeTagName(tag.name)],
            tag.count,
          ]),
          ([tagName]) => includes(ALLOWED_TAGS, tagName),
        ),
      );
    }
  }

  initArtistTags() {
    console.debug(
      `${chalk.inverse(`${this.artist} - ${this.name}`)}: ${chalk.inverse.green(
        `initArtistTags()`,
      )}`,
    );
    this.tags = get(ARTISTS_TAGS, this.artist);
  }
}
