import { LandingBrand } from './LandingBrand';
import { LandingCTA } from './LandingCTA';
import { landingConfig } from '../config/landing.config';

export function LandingHero() {
  const { hero } = landingConfig;

  return (
    <main
      className="epivibe-landing"
      style={{ '--epivibe-hero-image': `url("${hero.backgroundImage}")` } as React.CSSProperties}
    >
      <div className="epivibe-landing__backdrop" aria-hidden="true" />
      <div className="epivibe-landing__shade" aria-hidden="true" />
      <header className="epivibe-landing__header">
        <LandingBrand />
      </header>
      <section className="epivibe-landing__content" aria-labelledby="epivibe-landing-title">
        <h1 className="epivibe-landing__headline" id="epivibe-landing-title">
          <span>{hero.headlineStart}</span>
          <span>{hero.headlineEnd} <em>{hero.highlightedWord}</em></span>
        </h1>
        <LandingCTA />
      </section>
    </main>
  );
}
