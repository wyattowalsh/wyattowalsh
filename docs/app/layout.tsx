import { RootProvider } from 'fumadocs-ui/provider/next';
import { Inter, Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import { Suspense, type ReactNode } from 'react';
import type { Metadata } from 'next';
import { TelemetryProvider } from '@/components/telemetry-provider';
import {
  getDocsServerConfig,
  getTelemetryStorageDescription,
} from '@/lib/server/config';
import './global.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-space-grotesk',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
});

export const metadata: Metadata = {
  title: {
    default: 'wyattowalsh docs',
    template: '%s | wyattowalsh docs',
  },
  description:
    'Developer documentation for the GitHub profile README generator — SVG banners, generative art, word clouds, QR codes, and more.',
};

export default function Layout({ children }: { children: ReactNode }) {
  const telemetryConfig = getDocsServerConfig();
  const telemetryEnabled =
    getTelemetryStorageDescription(telemetryConfig).availability === 'available';

  return (
    <html
      lang="en"
      className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <body className="flex flex-col min-h-screen">
        <RootProvider>
          {telemetryEnabled ? (
            <Suspense fallback={null}>
              <TelemetryProvider enabled={telemetryEnabled} />
            </Suspense>
          ) : null}
          {children}
        </RootProvider>
      </body>
    </html>
  );
}
