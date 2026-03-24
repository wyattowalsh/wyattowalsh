import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import Image from 'next/image';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: (
        <>
          <Image src="/icon.svg" alt="" width={24} height={24} />
          <span className="font-semibold">wyattowalsh docs</span>
        </>
      ),
      url: '/',
      transparentMode: 'top',
    },
    githubUrl: 'https://github.com/wyattowalsh/wyattowalsh',
  };
}
