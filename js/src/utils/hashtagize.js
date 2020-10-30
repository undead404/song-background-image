import snakeCase from 'lodash/snakeCase';

export default function hashtagize(tagName) {
  return `#${snakeCase(tagName)}`;
}
