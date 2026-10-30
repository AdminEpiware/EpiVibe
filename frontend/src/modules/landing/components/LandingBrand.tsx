import { landingConfig } from '../config/landing.config';

/** Brand mark is CSS/SVG so it stays crisp on every screen size. */
export function LandingBrand() {
  return (
    <div className="epivibe-landing__brand" aria-label="EpiVibe — AI Event Strategist">
      <svg className="epivibe-landing__mark" viewBox="0 0 92 48" fill="none" aria-hidden="true">
        <defs>
          <linearGradient id="epivibe-mark-gradient" x1="0" y1="48" x2="92" y2="0" gradientUnits="userSpaceOnUse">
            <stop stopColor="#FFCE58" />
            <stop offset="0.48" stopColor="#E04CF8" />
            <stop offset="1" stopColor="#805DFF" />
          </linearGradient>
        </defs>
        <path d="M7 35C20 44 27 8 42 11C54 13 55 37 67 29C76 23 77 9 86 13" stroke="url(#epivibe-mark-gradient)" strokeWidth="10" strokeLinecap="round" />
      </svg>
      <div className="epivibe-landing__brand-copy">
        <span className="epivibe-landing__brand-name">{landingConfig.brand.name}<sup>®</sup></span>
        <span className="epivibe-landing__brand-tagline">{landingConfig.brand.tagline}</span>
      </div>
    </div>
  );
}
