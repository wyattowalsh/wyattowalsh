import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 py-24 px-4 text-center">
      <h1 className="text-5xl font-bold tracking-tight">
        wyattowalsh / wyattowalsh
      </h1>
      <p className="max-w-2xl text-lg text-fd-muted-foreground">
        Developer documentation for the GitHub profile README generator —
        SVG banners, generative art, word clouds, QR codes, metrics, and more.
      </p>
      <div className="flex gap-4">
        <Link
          href="/docs"
          className="rounded-md bg-fd-primary px-5 py-2.5 text-sm font-medium text-fd-primary-foreground transition-colors hover:bg-fd-primary/90"
        >
          Read the Docs
        </Link>
        <Link
          href="https://github.com/wyattowalsh/wyattowalsh"
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md border border-fd-border px-5 py-2.5 text-sm font-medium transition-colors hover:bg-fd-accent"
        >
          GitHub
        </Link>
      </div>
    </main>
  );
}
