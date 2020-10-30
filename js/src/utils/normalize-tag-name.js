import replace from 'lodash/replace';
import toLower from 'lodash/toLower';
import trim from 'lodash/trim';

const RE_TAG_GARBAGE = /[^\d a-z-]+/gi;
export default function normalizeTagName(tagName) {
  return toLower(trim(replace(tagName, RE_TAG_GARBAGE, ' ')));
}
