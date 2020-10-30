import reduce from 'lodash/reduce';

export default async function sequentialAsyncMap(collection, f) {
  const results = [];
  await reduce(
    collection,
    async (accumulator, item) => {
      await accumulator;
      results.push(await f(item));
    },
    Promise.resolve(),
  );
  return results;
}
