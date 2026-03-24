import Link from 'next/link';
import Image from 'next/image';

const features = [
  {
    title: 'SVG Banners',
    description: 'Procedural chaos-attractor banners with Lorenz, Aizawa, and flow-field patterns',
    icon: '~',
  },
  {
    title: 'Living Art',
    description: 'Ink gardens, topographic maps, and cosmic genesis — grown from your GitHub data',
    icon: '\u2727',
  },
  {
    title: 'Generative Art',
    description: 'Deterministic SVG art seeded from GitHub metrics via numpy RNG',
    icon: '\u25CA',
  },
  {
    title: 'Word Clouds',
    description: 'OKLCH-palettized word clouds from starred-repo topics and languages',
    icon: '\u2601',
  },
  {
    title: 'QR Codes',
    description: 'Styled QR codes with embedded SVG backgrounds and custom palettes',
    icon: '\u25A3',
  },
  {
    title: 'GitHub Metrics',
    description: 'GraphQL API fetching, commit history, and daily CI pipeline automation',
    icon: '\u25B3',
  },
];

const artPieces = [
  {
    src: '/showcase/inkgarden-growth.gif',
    title: 'Ink Garden',
    description: 'Each tree is a repository — blooms appear as stars accumulate',
  },
  {
    src: '/showcase/topo-growth.gif',
    title: 'Topography',
    description: 'Terrain contours and rivers emerge with activity',
  },
  {
    src: '/showcase/animated-community.gif',
    title: 'Cosmic Genesis',
    description: 'Clifford attractor density field revealed as community grows',
  },
  {
    src: '/showcase/animated-activity.gif',
    title: 'Unfurling Spiral',
    description: 'Phyllotaxis spiral grows from a single seed as contributions build',
  },
];

export default function HomePage() {
  return (
    <>
      {/* Hero Section */}
      <section className="relative flex flex-col items-center justify-center gap-8 py-32 px-4 text-center overflow-hidden">
        <div className="hero-gradient" aria-hidden="true" />

        {/* Banner */}
        <div className="relative z-10 w-full max-w-4xl">
          <picture>
            <source media="(prefers-color-scheme: dark)" srcSet="/showcase/banner-dark.svg" />
            <Image
              src="/showcase/banner.svg"
              alt="wyattowalsh profile banner"
              width={1200}
              height={300}
              className="w-full h-auto rounded-xl"
              priority
            />
          </picture>
        </div>

        <div className="relative z-10 flex flex-col items-center gap-6">
          <h1 className="hero-title text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight">
            wyattowalsh
          </h1>
          <p className="max-w-2xl text-lg sm:text-xl text-fd-muted-foreground leading-relaxed">
            A fully dynamic GitHub profile README generator — SVG banners,
            generative art, word clouds, QR codes, living art, and metrics —
            all driven by a Python CLI running daily on GitHub Actions.
          </p>
          <div className="flex gap-4 mt-2">
            <Link
              href="/docs"
              className="rounded-lg bg-fd-primary px-6 py-3 text-sm font-medium text-fd-primary-foreground transition-all hover:bg-fd-primary/90 hover:shadow-lg hover:shadow-fd-primary/20"
            >
              Read the Docs
            </Link>
            <Link
              href="https://github.com/wyattowalsh/wyattowalsh"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-fd-border px-6 py-3 text-sm font-medium transition-all hover:bg-fd-accent hover:border-fd-accent-foreground/20"
            >
              GitHub
            </Link>
          </div>
        </div>
      </section>

      {/* Living Art Gallery */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="hero-title text-3xl sm:text-4xl font-bold tracking-tight text-center mb-2">
            Living Art
          </h2>
          <p className="text-fd-muted-foreground text-center mb-10 max-w-xl mx-auto">
            Artwork driven by real GitHub data — watch it grow from bare soil to full bloom
          </p>
          <div className="art-gallery">
            {artPieces.map((piece) => (
              <div key={piece.title} className="relative group">
                <Image
                  src={piece.src}
                  alt={piece.title}
                  width={500}
                  height={350}
                  className="w-full h-auto"
                  unoptimized
                />
                <div className="absolute inset-x-0 bottom-0 bg-linear-to-t from-black/70 to-transparent p-4">
                  <h3 className="text-white font-semibold text-lg">{piece.title}</h3>
                  <p className="text-white/80 text-sm">{piece.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="hero-title text-3xl sm:text-4xl font-bold tracking-tight text-center mb-2">
            What It Does
          </h2>
          <p className="text-fd-muted-foreground text-center mb-10 max-w-xl mx-auto">
            Every element of the profile README is generated programmatically
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <div key={feature.title} className="feature-card">
                <div className="text-3xl mb-3">{feature.icon}</div>
                <h3 className="font-semibold text-lg mb-2 text-fd-foreground">
                  {feature.title}
                </h3>
                <p className="text-fd-muted-foreground text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Generative Art Showcase */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="hero-title text-3xl sm:text-4xl font-bold tracking-tight mb-2">
            Generative Art
          </h2>
          <p className="text-fd-muted-foreground mb-10 max-w-xl mx-auto">
            Deterministic SVG art — same metrics, same output, every time
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="feature-card overflow-hidden p-0">
              <Image
                src="/showcase/generative-activity.svg"
                alt="Activity-seeded generative art"
                width={600}
                height={400}
                className="w-full h-auto"
              />
              <div className="p-4">
                <h3 className="font-semibold text-fd-foreground">Activity Art</h3>
                <p className="text-fd-muted-foreground text-sm">Seeded from contribution data</p>
              </div>
            </div>
            <div className="feature-card overflow-hidden p-0">
              <Image
                src="/showcase/wordcloud_metaheuristic-anim_by_topics.svg"
                alt="Animated word cloud of topics with one frame per metaheuristic solver"
                width={600}
                height={400}
                className="w-full h-auto"
              />
              <div className="p-4">
                <h3 className="font-semibold text-fd-foreground">Animated Word Cloud</h3>
                <p className="text-fd-muted-foreground text-sm">25 metaheuristic layouts sequenced into a single SVG</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Footer */}
      <section className="py-20 px-4 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-fd-foreground mb-4">
            Ready to build your own?
          </h2>
          <p className="text-fd-muted-foreground mb-8">
            Fork the repo, customize the config, and let GitHub Actions handle the rest.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/docs/getting-started"
              className="rounded-lg bg-fd-primary px-6 py-3 text-sm font-medium text-fd-primary-foreground transition-all hover:bg-fd-primary/90 hover:shadow-lg hover:shadow-fd-primary/20"
            >
              Get Started
            </Link>
            <Link
              href="/docs/getting-started/fork-and-repurpose"
              className="rounded-lg border border-fd-border px-6 py-3 text-sm font-medium transition-all hover:bg-fd-accent hover:border-fd-accent-foreground/20"
            >
              Fork & Repurpose
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
