import reduce from 'lodash/reduce';
import extendTaste from './extend-taste';

describe('extendTaste', () => {
  it('works with empty taste portions', () => {
    expect.assertions(1);
    expect(extendTaste({}, {})).toStrictEqual({});
  });
  it("doesn't mutate original taste with empty portion", () => {
    expect.assertions(1);
    expect(extendTaste({ Hardcore: 1 }, {})).toStrictEqual({ Hardcore: 1 });
  });
  it('records first valuable portion', () => {
    expect.assertions(1);
    expect(extendTaste({}, { Hardcore: 1 })).toStrictEqual({ Hardcore: 1 });
  });
  it('merges different tags', () => {
    expect.assertions(1);
    expect(extendTaste({ 'Post-Hardcore': 1 }, { Hardcore: 1 })).toStrictEqual({
      Hardcore: 1,
      'Post-Hardcore': 1,
    });
  });
  it('merges same tags', () => {
    expect.assertions(1);
    expect(extendTaste({ Hardcore: 1 }, { Hardcore: 1 })).toStrictEqual({
      Hardcore: 2,
    });
  });
  it('merges same tags with multiplyBy', () => {
    expect.assertions(1);
    expect(extendTaste({ Hardcore: 1 }, { Hardcore: 1 }, 2)).toStrictEqual({
      Hardcore: 3,
    });
  });
  it('works with reduce', () => {
    expect.assertions(1);
    expect(
      reduce(
        [{ Metalcore: 1, Hardcore: 2 }],
        (taste, tastePortion) => extendTaste(taste, tastePortion),
        {},
      ),
    ).toStrictEqual({ Hardcore: 2, Metalcore: 1 });
  });
});
