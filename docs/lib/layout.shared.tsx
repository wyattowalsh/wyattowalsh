import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: 'wyattowalsh docs',
      url: '/',
    },
    links: [
      {
        text: 'GitHub',
        url: 'https://github.com/wyattowalsh/wyattowalsh',
        external: true,
      },
    ],
  };
}
