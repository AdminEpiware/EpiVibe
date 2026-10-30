import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { landingConfig } from '../config/landing.config';

export function LandingCTA() {
  return (
    <Link className="epivibe-landing__cta" to={landingConfig.hero.ctaPath}>
      <span>{landingConfig.hero.ctaLabel}</span>
      <ArrowRight aria-hidden="true" size={29} strokeWidth={2.2} />
    </Link>
  );
}
