import type { ReactNode } from 'react';

type Props = { title: string; description?: string; children?: ReactNode };
/** Page-level content wrapper, reused by feature modules. */
export default function AppPageTemplate({ title, description, children }: Props) {
  return (
    <section className="epi-page">
      <header className="epi-page-header">
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </header>
      {children}
    </section>
  );
}
