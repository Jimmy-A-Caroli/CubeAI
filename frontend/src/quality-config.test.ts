import axe from 'axe-core';
import { createElement } from 'react';
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

describe('frontend quality configuration', () => {
  it('accepts descriptive image alternatives and rejects missing alternatives', async () => {
    const validImage = render(createElement('img', { alt: 'Cube artwork' }));
    const validResult = await axe.run(validImage.container, {
      runOnly: { type: 'rule', values: ['image-alt'] },
    });
    validImage.unmount();

    const invalidImage = render(createElement('img'));
    const invalidResult = await axe.run(invalidImage.container, {
      runOnly: { type: 'rule', values: ['image-alt'] },
    });

    expect(validResult.violations).toEqual([]);
    expect(invalidResult.violations.map(({ id }) => id)).toEqual(['image-alt']);
  });
});
