import isEmpty from 'lodash/isEmpty';
import isNaN from 'lodash/isNaN';
import map from 'lodash/map';
import mean from 'lodash/mean';
import size from 'lodash/size';
import sum from 'lodash/sum';

export default function getStandardDeviation(collection) {
  if (isEmpty(collection) || size(collection) === 1) {
    return 0;
  }
  const result = Math.sqrt(
    sum(map(collection, (item) => (item - mean(collection)) ** 2)) /
      size(collection),
  );
  if (isNaN(result)) {
    console.debug(collection);
    throw new TypeError('Standard deviation is NaN');
  }
  return result;
}
