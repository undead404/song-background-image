import normalizeTagName from './normalize-tag-name';

describe('normalizeTagName', () => {
  it('outputs properly with simple tags', () => {
    expect.assertions(1);
    expect(normalizeTagName('Hardcore')).toBe('hardcore');
  });
  it('outputs properly with spaced tags', () => {
    expect.assertions(1);
    expect(normalizeTagName('Black Metal')).toBe('black metal');
  });
  it('outputs properly with dashed tags', () => {
    expect.assertions(1);
    expect(normalizeTagName('Post-Rock')).toBe('post-rock');
  });
});
