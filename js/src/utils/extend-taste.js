import forEach from 'lodash/forEach';
import get from 'lodash/get';

export default function extendTaste(taste, tastePortion, multiplyBy = 1) {
  // console.debug("extend_taste(...)")
  const newTaste = { ...taste };
  forEach(tastePortion, (tagValue, tagName) => {
    newTaste[tagName] = get(newTaste, tagName, 0) + tagValue * multiplyBy;
  });
  return newTaste;
}
