import Image from 'next/image';
import { BasculeLangue } from './bascule-langue';
import { Main, Pictogramme } from './main';
import { Reveal } from './reveal';
import type { Contenu, Langue } from './content';
import { getReleases, getTelechargements, PAGE_VERSIONS, type Telechargements } from './releases';

const DEPOT = 'https://github.com/Luth-infinity/gestes';
const SUITE = 'https://luth-apps.vercel.app';

// Les deux langues restent dans cet ordre quelle que soit la page.
const LANGUES: { code: Langue; libelle: string; href: string }[] = [
  { code: 'fr', libelle: 'FR', href: '/fr' },
  { code: 'en', libelle: 'EN', href: '/' }
];

/** Dans l'ordre de la page : on retombe dans l'autre langue sur celle qu'on lisait. */
const SECTIONS = ['gestes', 'fonctionnement', 'details', 'telecharger', 'versions'];

function Logo({ className = 'size-6' }: { className?: string }) {
  return <Image src="/icon.png" alt="" width={64} height={64} className={className} />;
}

function Telecharger({ t, dl }: { t: Contenu; dl: Telechargements }) {
  const principal =
    'inline-flex items-center justify-center gap-2 rounded-full bg-ink px-6 py-3 text-[15px] font-medium text-page shadow-[0_8px_30px_-8px_var(--color-geste)] transition hover:opacity-90';
  const second = 'text-sm text-ink-soft underline-offset-4 hover:underline';

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="flex flex-wrap items-center justify-center gap-3">
        <a data-cta="win" href={dl.win ?? PAGE_VERSIONS} className={principal}>
          {t.telecharger.windows}
        </a>
        <a data-cta="mac" href={dl.macArm ?? PAGE_VERSIONS} className={principal}>
          {t.telecharger.mac}
        </a>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-center">
        {dl.version && (
          <span className="text-sm text-ink-soft">
            {t.telecharger.version} {dl.version}
          </span>
        )}
        <a data-cta="mac" href={dl.macIntel ?? PAGE_VERSIONS} className={second}>
          {t.telecharger.macIntel}
        </a>
        <a data-cta="win" href={PAGE_VERSIONS} className={second}>
          {t.telecharger.toutes}
        </a>
      </div>
    </div>
  );
}

export default async function Vitrine({ t, locale }: { t: Contenu; locale: Langue }) {
  const [dl, releases] = await Promise.all([getTelechargements(), getReleases(locale)]);

  return (
    <>
      <Reveal />

      <header className="sticky top-0 z-10 border-b border-line/70 bg-page/80 backdrop-blur">
        <nav className="mx-auto flex max-w-5xl items-center gap-4 px-4 py-3">
          <span className="flex items-center gap-2 font-medium tracking-tight">
            <Logo />
            Gestes
          </span>
          <span className="flex-1" />
          <a href="#gestes" className="hidden text-sm text-ink-soft hover:text-ink sm:block">
            {t.nav.gestes}
          </a>
          <a href="#versions" className="hidden text-sm text-ink-soft hover:text-ink sm:block">
            {t.nav.versions}
          </a>
          <BasculeLangue
            langues={LANGUES}
            locale={locale}
            label={t.nav.langue}
            sections={SECTIONS}
            fond="bg-canvas ring-1 ring-line/60"
            pastille="bg-card ring-1 ring-line"
          />
          <a href="#telecharger" className="text-sm font-medium hover:opacity-80">
            {t.nav.telecharger}
          </a>
        </nav>
      </header>

      <main>
        {/* Hero */}
        <section className="halo-hero px-4 pb-16 pt-16 sm:pt-24">
          <div className="mx-auto grid max-w-5xl items-center gap-12 lg:grid-cols-[1.1fr_1fr]">
            <div className="text-center lg:text-left">
              <h1 className="reveal headline text-[12vw] sm:text-[68px] lg:text-[76px]">
                {t.hero.titre[0]} <span className="degrade">{t.hero.titre[1]}</span>
              </h1>
              <p className="reveal mx-auto mt-7 max-w-[46ch] text-[17px] leading-relaxed text-ink-soft lg:mx-0">
                {t.hero.texte}
              </p>
              <div className="reveal mt-10 lg:[&>div]:items-start lg:[&>div>div]:justify-start">
                <Telecharger t={t} dl={dl} />
              </div>
              <p className="reveal mt-6 text-sm text-ink-soft">{t.hero.mention}</p>
            </div>
            <div className="reveal mx-auto w-full max-w-[460px]">
              <Main poses={t.scene.poses} volume={t.scene.volume} webcam={t.scene.webcam} />
            </div>
          </div>
        </section>

        {/* Gestes */}
        <section id="gestes" className="px-4 py-16">
          <div className="mx-auto max-w-5xl">
            <h2 className="reveal headline max-w-[16ch] text-[40px] sm:text-[54px]">{t.gestes.titre}</h2>
            <p className="reveal mt-5 max-w-[56ch] text-[15px] leading-relaxed text-ink-soft">{t.gestes.texte}</p>
            <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {t.gestes.items.map((g) => (
                <li key={g.nom} className="reveal rounded-2xl border border-line bg-card p-6 transition hover:border-geste/50">
                  <span className="flex size-10 items-center justify-center rounded-xl bg-canvas text-ink ring-1 ring-line">
                    <Pictogramme nom={g.icone} />
                  </span>
                  <h3 className="mt-5 text-[17px] font-semibold tracking-tight">{g.nom}</h3>
                  <p className="mt-1 text-[13px] font-medium text-geste">{g.action}</p>
                  <p className="mt-3 text-sm leading-relaxed text-ink-soft">{g.texte}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Trois temps */}
        <section id="fonctionnement" className="px-4 py-16">
          <div className="mx-auto max-w-5xl">
            <h2 className="reveal headline max-w-[16ch] text-[40px] sm:text-[54px]">{t.etapes.titre}</h2>
            <p className="reveal mt-5 max-w-[56ch] text-[15px] leading-relaxed text-ink-soft">{t.etapes.texte}</p>
            <ol className="mt-12 grid gap-4 sm:grid-cols-3">
              {t.etapes.items.map(([titre, texte], i) => (
                <li key={titre} className="reveal rounded-2xl border border-line bg-card p-6">
                  <span className={`headline text-[28px] ${i === 0 ? 'text-arme' : 'text-ink-soft'}`}>{i + 1}</span>
                  <h3 className="mt-3 text-[17px] font-semibold tracking-tight">{titre}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink-soft">{texte}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Aperçu de l'app */}
        <section className="px-4 py-16">
          <figure className="reveal mx-auto max-w-5xl">
            <div className="overflow-hidden rounded-2xl border border-line shadow-[0_50px_140px_-50px_rgba(99,115,255,0.45)]">
              <Image src="/app.png" alt="" width={1232} height={803} className="block h-auto w-full" />
            </div>
            <figcaption className="mt-4 text-center text-sm text-ink-soft">{t.apercu.legende}</figcaption>
          </figure>
        </section>

        {/* Détails */}
        <section id="details" className="px-4 py-16">
          <div className="mx-auto grid max-w-5xl gap-4 sm:grid-cols-2">
            {t.details.map(([titre, texte]) => (
              <div key={titre} className="reveal rounded-2xl border border-line bg-card p-6">
                <h3 className="text-[17px] font-semibold tracking-tight">{titre}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-soft">{texte}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Téléchargement */}
        <section id="telecharger" className="px-4 py-24">
          <div className="reveal mx-auto max-w-3xl rounded-3xl border border-line bg-canvas px-6 py-16 text-center">
            <Logo className="mx-auto size-12" />
            <h2 className="headline mt-6 text-[40px] sm:text-[52px]">{t.telecharger.titre}</h2>
            <p className="mx-auto mt-5 max-w-[44ch] text-[15px] leading-relaxed text-ink-soft">{t.telecharger.texte}</p>
            <div className="mt-10">
              <Telecharger t={t} dl={dl} />
            </div>
            <p className="mt-6 text-sm text-ink-soft">{t.telecharger.configuration}</p>
            <p className="mx-auto mt-8 max-w-[52ch] text-xs leading-relaxed text-ink-soft">{t.telecharger.signature}</p>
          </div>
        </section>

        {/* Versions */}
        {releases.length > 0 && (
          <section id="versions" className="px-4 py-8">
            <div className="mx-auto max-w-5xl">
              <h2 className="reveal headline text-[40px] sm:text-[54px]">{t.changelog.titre}</h2>
              <ul className="mt-12 grid gap-4">
                {releases.map((release) => (
                  <li
                    key={release.version}
                    className="reveal grid gap-4 rounded-2xl border border-line bg-card p-6 sm:grid-cols-[10rem_1fr]"
                  >
                    <div>
                      <a href={release.page} className="headline text-[24px] hover:opacity-80" target="_blank" rel="noreferrer">
                        {release.version}
                      </a>
                      <p className="mt-1 text-xs text-ink-soft">{release.date}</p>
                    </div>
                    <ul className="grid gap-2">
                      {release.points.map((point) => (
                        <li key={point} className="text-sm leading-relaxed text-ink-soft">
                          {point}
                        </li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}
      </main>

      <footer className="mt-16 border-t border-line px-4 py-12">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-3">
          <span className="flex items-center gap-2 text-sm">
            <Logo className="size-5" />
            Gestes
          </span>
          <span className="flex-1" />
          <a href={SUITE} className="text-sm text-ink-soft hover:text-ink">
            {t.pied.suite}
          </a>
          <a href={DEPOT} className="text-sm text-ink-soft hover:text-ink">
            {t.pied.code}
          </a>
          <a href={PAGE_VERSIONS} className="text-sm text-ink-soft hover:text-ink">
            {t.pied.versions}
          </a>
        </div>
      </footer>
    </>
  );
}
