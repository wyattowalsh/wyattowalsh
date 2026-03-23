import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import Image from 'next/image';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: (
        <>
          <Image src="/icon.svg" alt="" width={24} height={24} />
          wyattowalsh docs
        </>
      ),
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
