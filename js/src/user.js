import { API_KEY } from '@env';
import chalk from 'chalk';
import filter from 'lodash/filter';
import flatMap from 'lodash/flatMap';
import forEach from 'lodash/forEach';
import fromPairs from 'lodash/fromPairs';
import isEmpty from 'lodash/isEmpty';
import isNil from 'lodash/isNil';
import keys from 'lodash/keys';
import map from 'lodash/map';
import range from 'lodash/range';
import size from 'lodash/size';
import sortBy from 'lodash/sortBy';
import sum from 'lodash/sum';
import take from 'lodash/take';
import toPairs from 'lodash/toPairs';
import uniq from 'lodash/uniq';
import values from 'lodash/values';
import Mustache from 'mustache';
import Track from './track';
import { USER_GET_LOVED_TRACKS } from './url-patterns.json';
import requestData from './utils/request-data';
import sequentialAsyncMap from './utils/sequential-async-map';
import getStandardDeviation from './utils/get-standard-deviation';

export default class User {
  launchTime = undefined;

  lovedTracksPagesNumber = undefined;

  name = undefined;

  tracks = {};

  constructor(name) {
    this.name = name;
  }

  async acquireLovedTracksPagesNumber() {
    console.debug(
      `${chalk.inverse(this.name)}: ${chalk.inverse.yellow(
        `acquireLovedTracksPagesNumber()`,
      )}`,
    );
    const userLovedTracksData = await requestData(
      Mustache.render(USER_GET_LOVED_TRACKS, {
        api_key: API_KEY,
        user: this.name,
        page_num: 1,
      }),
      'lovedtracks',
    );
    if (!userLovedTracksData) {
      throw new Error("User loved tracks' fetch failure");
    }
    this.lovedTracksPagesNumber = Number.parseInt(
      userLovedTracksData['@attr'].totalPages,
      10,
    );
  }

  acquirePageTracks = async (pageNumber) => {
    console.debug(
      `${chalk.inverse(this.name)}: ${chalk.inverse.yellow(
        `acquirePageTracks(${pageNumber})`,
      )}`,
    );
    const lovedTracksData = await requestData(
      Mustache.render(USER_GET_LOVED_TRACKS, {
        api_key: API_KEY,
        user: this.name,
        page_num: pageNumber,
      }),
      'lovedtracks',
    );
    if (!lovedTracksData) {
      return {};
    }
    forEach(lovedTracksData.track, (trackData) => {
      const trackUts = Number.parseInt(trackData.date.uts, 10);
      this.tracks[trackUts] = new Track(trackData.artist.name, trackData.name);
    });
  };

  async acquireTaste() {
    console.debug(
      `${chalk.inverse(this.name)}: ${chalk.inverse.yellow(`acquireTaste()`)}`,
    );
    await this.acquireLovedTracksPagesNumber();
    await sequentialAsyncMap(
      range(1, this.lovedTracksPagesNumber + 1),
      //   [1],
      this.acquirePageTracks,
    );
    await this.acquireTracksTastes();
    const tagNames = uniq(flatMap(this.tracks, (track) => keys(track.tags)));
    console.info(tagNames);
    const tracksPairs = toPairs(this.tracks);
    const tagsDeviations = fromPairs(
      map(tagNames, (tagName) => {
        const relatedTracksPairs = filter(
          tracksPairs,
          ([, track]) => track.tags[tagName],
        );
        const utss = map(relatedTracksPairs, ([trackUts]) =>
          Number.parseInt(trackUts, 10),
        );
        const standardDeviation = getStandardDeviation(utss);
        return [tagName, standardDeviation];
      }),
    );
    const tagsWeights = fromPairs(
      map(tagNames, (tagName) => [
        tagName,
        sum(map(this.tracks, (track) => track.tags[tagName])),
      ]),
    );
    return take(
      sortBy(
        map(tagNames, (tagName) => [
          tagName,
          tagsDeviations[tagName] * tagsWeights[tagName],
        ]),
        ([, tagWeight]) => -tagWeight,
      ),
      10,
    );
  }

  async acquireTasteRecent(launchTime) {
    console.debug(
      `${chalk.inverse(this.name)}: ${chalk.inverse.yellow(
        `acquireTasteRecent(${launchTime})`,
      )}`,
    );
    this.launchTime = launchTime;
    if (isNil(this.lovedTracksPagesNumber)) {
      await this.acquireLovedTracksPagesNumber();
    }
    if (isEmpty(this.tracks)) {
      await sequentialAsyncMap(
        range(1, this.lovedTracksPagesNumber + 1),
        this.acquirePageTracks,
      );
      await this.acquireTracksTastes();
    }
    const tagNames = uniq(flatMap(this.tracks, (track) => keys(track.tags)));
    const tracksPairs = toPairs(this.tracks);
    const tagsWeights = fromPairs(
      map(tagNames, (tagName) => {
        const relatedTracksPairs = filter(
          tracksPairs,
          ([, track]) => track.tags[tagName],
        );
        return [
          tagName,
          sum(
            map(
              relatedTracksPairs,
              ([trackUts, track]) =>
                (track.tags[tagName] /
                  (this.launchTime - Number.parseInt(trackUts, 10))) *
                sum(values(track.tags)),
            ),
          ),
        ];
      }),
    );
    return take(
      sortBy(toPairs(tagsWeights), ([, tagWeight]) => -tagWeight),
      10,
    );
  }

  async acquireTracksTastes() {
    console.debug(
      `${chalk.inverse(this.name)}: ${chalk.inverse.yellow(`getTopArtists()`)}`,
    );
    return sequentialAsyncMap(this.tracks, (track) => track.acquireTags());
  }

  getTopArtists(limit = 10) {
    console.debug(
      `${chalk.inverse(this.name)}: ${chalk.inverse.green(`getTopArtists()`)}`,
    );
    const tracksPairs = toPairs(this.tracks);
    const artistNames = uniq(map(tracksPairs, ([, track]) => track.artist));

    return take(
      sortBy(
        map(artistNames, (artistName) => {
          const artistTracksPairs = filter(
            tracksPairs,
            ([, track]) => track.artist === artistName,
          );
          const weight =
            getStandardDeviation(
              map(artistTracksPairs, ([trackUts]) =>
                Number.parseInt(trackUts, 10),
              ),
            ) * size(artistTracksPairs);
          return [artistName, weight];
        }),
        ([, artistWeight]) => -artistWeight,
      ),
      limit,
    );
  }

  getTopArtistsByTagName(tagName, limit = 10) {
    console.debug(
      `${chalk.inverse(this.name)}: ${chalk.inverse.green(
        `getTopArtistsByTagName(${tagName}, ${limit})`,
      )}`,
    );
    const tagTracksPairs = filter(
      toPairs(this.tracks),
      ([, track]) => track.tags[tagName],
    );
    const artistNames = uniq(map(tagTracksPairs, ([, track]) => track.artist));

    return take(
      sortBy(
        map(artistNames, (artistName) => {
          const artistTracksPairs = filter(
            tagTracksPairs,
            ([, track]) => track.artist === artistName,
          );
          const weight =
            getStandardDeviation(
              map(artistTracksPairs, ([trackUts]) =>
                Number.parseInt(trackUts, 10),
              ),
            ) * sum(map(artistTracksPairs, ([, track]) => track.tags[tagName]));
          return [artistName, weight];
        }),
        ([, artistWeight]) => -artistWeight,
      ),
      limit,
    );
  }
}
