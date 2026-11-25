'use client';

import { useEffect, useRef, useState } from 'react';

/**
 * La main, rejouée avec les 21 points que MediaPipe repère sur la webcam :
 * 0 poignet, 1-4 pouce, 5-8 index, 9-12 majeur, 13-16 annulaire, 17-20 auriculaire.
 * Elle enchaîne les gestes de l'app, et la pastille dit ce que l'app comprend,
 * comme le témoin à l'écran. Coordonnées dans une boîte 100 × 100.
 */
type Point = [number, number];

const OUVERTE: Point[] = [
  [50, 90], [38, 82], [29, 73], [23, 64], [18, 56], [40, 58], [37, 44], [35, 35], [34, 27],
  [50, 56], [50, 40], [50, 30], [50, 21], [59, 58], [61, 44], [62, 35], [63, 28],
  [67, 63], [71, 52], [73, 45], [75, 38]
];
const REPLIE: Record<number, Point[]> = {
  5: [[40, 58], [39, 49], [42, 55], [43, 61]],
  9: [[50, 56], [50, 47], [51, 54], [51, 60]],
  13: [[59, 58], [60, 50], [59, 56], [58, 61]],
  17: [[67, 63], [68, 56], [66, 61], [64, 64]]
};
const POUCE_RENTRE: Point[] = [[38, 82], [33, 74], [36, 66], [42, 63]];

function forme(tendus: number[], pouce?: Point[], retouches: Record<number, Point> = {}): Point[] {
  const p = OUVERTE.map((v) => [...v] as Point);
  for (const base of [5, 9, 13, 17]) {
    if (!tendus.includes(base)) REPLIE[base].forEach((v, i) => (p[base + i] = [...v] as Point));
  }
  pouce?.forEach((v, i) => (p[1 + i] = [...v] as Point));
  for (const [i, v] of Object.entries(retouches)) p[Number(i)] = v;
  return p;
}

// Dans l'ordre de `scene.poses` du contenu.
const POSES: { p: Point[]; dx?: number; dy?: number; ton?: 'arme' }[] = [
  { p: OUVERTE, ton: 'arme' },
  { p: forme([9, 13, 17], [[38, 82], [31, 74], [28, 63], [31, 51]], { 6: [36, 46], 7: [33, 44], 8: [31, 49] }), dy: -14 },
  { p: forme([], POUCE_RENTRE) },
  { p: forme([5], POUCE_RENTRE), dx: 10, dy: -4 },
  { p: forme([5, 9], POUCE_RENTRE), dy: 10 }
];

const LIAISONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [5, 9], [9, 10], [10, 11],
  [11, 12], [9, 13], [13, 14], [14, 15], [15, 16], [13, 17], [17, 18], [18, 19], [19, 20], [0, 17]
];
const BOUTS = new Set([4, 8, 12, 16, 20]);

export function Main({ poses, volume, webcam }: { poses: string[]; volume: string; webcam: string }) {
  const svg = useRef<SVGSVGElement>(null);
  const [pose, setPose] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const racine = svg.current;
    if (!racine) return;
    const lignes = [...racine.querySelectorAll('line')];
    const ronds = [...racine.querySelectorAll('circle')];
    const calme = matchMedia('(prefers-reduced-motion: reduce)').matches;
    let actuel = OUVERTE.map((v) => [...v] as Point);
    let cible = 0;
    let debut = performance.now();
    let image = 0;

    const dessiner = (t: number) => {
      const p = POSES[cible];
      const age = (t - debut) / 1000;
      // le mouvement du geste (monter, glisser) vient après l'arrivée sur la forme
      const m = Math.min(Math.max((age - 0.6) / 1.2, 0), 1);
      const doux = m < 0.5 ? 2 * m * m : 1 - Math.pow(-2 * m + 2, 2) / 2;
      const flotte = calme ? 0 : Math.sin(t / 900) * 0.8;
      const dx = (p.dx ?? 0) * doux;
      const dy = (p.dy ?? 0) * doux + flotte;
      actuel = actuel.map((v, i) => [
        v[0] + (p.p[i][0] + dx - v[0]) * 0.12,
        v[1] + (p.p[i][1] + dy - v[1]) * 0.12
      ]);
      LIAISONS.forEach(([a, b], k) => {
        lignes[k].setAttribute('x1', String(actuel[a][0]));
        lignes[k].setAttribute('y1', String(actuel[a][1]));
        lignes[k].setAttribute('x2', String(actuel[b][0]));
        lignes[k].setAttribute('y2', String(actuel[b][1]));
      });
      ronds.forEach((c, i) => {
        c.setAttribute('cx', String(actuel[i][0]));
        c.setAttribute('cy', String(actuel[i][1]));
      });
      if (age > 2.8) {
        cible = (cible + 1) % POSES.length;
        debut = t;
        setVisible(false);
        window.setTimeout(() => {
          setPose(cible);
          setVisible(true);
        }, 250);
      }
      image = requestAnimationFrame(dessiner);
    };
    image = requestAnimationFrame(dessiner);
    return () => cancelAnimationFrame(image);
  }, []);

  const arme = POSES[pose].ton === 'arme';

  return (
    <div className="relative aspect-square w-full overflow-hidden rounded-[28px] border border-line bg-[radial-gradient(circle_at_50%_40%,#1d2026,#14161a_70%)] shadow-[0_40px_120px_-40px_rgba(0,0,0,0.9)]">
      <div className="grille absolute inset-0" />
      <div className="absolute left-5 top-5 flex items-center gap-2 text-xs text-ink-soft">
        <span className="clignote size-2 rounded-full bg-[#ef4444]" />
        {webcam} · 30 i/s
      </div>

      <svg ref={svg} viewBox="0 0 100 100" className="absolute inset-x-[6%] top-[5%] h-[80%] w-[88%]" aria-hidden>
        {LIAISONS.map((_, k) => (
          <line key={k} stroke="rgba(246,247,248,0.85)" strokeWidth={1.1} strokeLinecap="round" />
        ))}
        {OUVERTE.map((v, i) => (
          <circle key={i} cx={v[0]} cy={v[1]} r={BOUTS.has(i) ? 1.9 : 1.3} fill={BOUTS.has(i) ? '#f6f7f8' : 'var(--color-geste)'} />
        ))}
      </svg>

      <div
        className={`absolute bottom-6 left-1/2 flex -translate-x-1/2 items-center gap-2.5 whitespace-nowrap rounded-full border border-line bg-card/90 py-2 pl-2 pr-4 text-sm font-medium backdrop-blur transition duration-300 ${visible ? 'opacity-100' : 'translate-y-1.5 opacity-0'}`}
        aria-live="polite"
      >
        <span className={`flex size-7 items-center justify-center rounded-full ${arme ? 'bg-arme/25 text-arme' : 'bg-geste/20 text-geste'}`}>
          <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            {arme ? (
              <>
                <path d="M18 11V6a2 2 0 0 0-4 0v5M14 10V4a2 2 0 0 0-4 0v6M10 10.5V6a2 2 0 0 0-4 0v8" />
                <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15" />
              </>
            ) : (
              <path d="M20 6 9 17l-5-5" />
            )}
          </svg>
        </span>
        {poses[pose]}
        {pose === 1 && <span className="font-normal text-ink-soft">{volume}</span>}
      </div>
    </div>
  );
}

/** Pictogrammes des gestes (traits Lucide), pour les cartes. */
export function Pictogramme({ nom }: { nom: string }) {
  const chemins: Record<string, React.ReactNode> = {
    pince: <path d="M2 10v3M6 6v11M10 3v18M14 8v7M18 5v13M22 10v3" />,
    poing: (
      <>
        <path d="M12.04 6.06A2 2 0 0 1 16 7v3M8 10V7a2 2 0 0 1 4 0v3M16 10a2 2 0 0 1 4 0v4a8 8 0 0 1-8 8h-2a6 6 0 0 1-6-6v-2a2 2 0 0 1 2-2h4" />
        <path d="M8 14h1a2 2 0 0 0 0-4H6" />
      </>
    ),
    index: (
      <>
        <path d="M22 14a8 8 0 0 1-8 8M18 11v-1a2 2 0 0 0-4 0M14 10V9a2 2 0 0 0-4 0v1M10 9.5V4a2 2 0 0 0-4 0v10" />
        <path d="M18 11a2 2 0 1 1 4 0v3a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15" />
      </>
    ),
    deux: <path d="m7 15 5 5 5-5M7 9l5-5 5 5" />,
    balayage: <path d="m18 8 4 4-4 4M2 12h20M6 8l-4 4 4 4" />,
    pouce: (
      <>
        <path d="M7 10v12" />
        <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z" />
      </>
    )
  };
  return (
    <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      {chemins[nom]}
    </svg>
  );
}
