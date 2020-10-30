import hashtagize from './hashtagize';

describe('hashtagize', () => {
  it('outputs properly with simple tags', () => {
    expect.assertions(1);
    expect(hashtagize('Hardcore')).toBe('#hardcore');
  });
  it('outputs properly with spaced tags', () => {
    expect.assertions(1);
    expect(hashtagize('Black Metal')).toBe('#black_metal');
  });
  it('outputs properly with dashed tags', () => {
    expect.assertions(1);
    expect(hashtagize('Post-Rock')).toBe('#post_rock');
  });
});
