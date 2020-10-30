// import { LASTFM_USERNAME } from '@env';
import forEach from 'lodash/forEach';
// import keys from 'lodash/keys';
import User from './user';

// const LAUNCH_TIME = Math.trunc(Date.now() / 1000);
async function main() {
  const user = new User('UNDEADUM');
  const taste = await user.acquireTaste();
  forEach(taste, (tastePair) => {
    console.info(tastePair);
    const [tagName] = tastePair;
    console.info(user.getTopArtistsByTagName(tagName));
  });
  console.info(user.getTopArtists(100));
  // console.info(await user.acquireTasteRecent(LAUNCH_TIME));
}
main();
