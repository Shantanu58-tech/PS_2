export type Provenance = "LIVE" | "REPLAY" | "IMPORT" | "SYNTHETIC";

const PROVENANCE_STYLES: Record<Provenance, string> = {
  LIVE: "border-live/50 text-live",
  REPLAY: "border-replay/50 text-replay",
  IMPORT: "border-import/50 text-import",
  SYNTHETIC: "border-synthetic/50 text-synthetic",
};

const PROVENANCE_TITLES: Record<Provenance, string> = {
  LIVE: "Collected live from an official platform API",
  REPLAY: "Streamed from a historical dataset through the same pipeline",
  IMPORT: "Imported from a file supplied by an analyst",
  SYNTHETIC: "Injected test campaign with known ground truth",
};

export function ProvenanceBadge({ provenance }: { provenance: Provenance }) {
  return (
    <span
      title={PROVENANCE_TITLES[provenance]}
      className={`inline-flex items-center rounded-sm border px-1.5 py-0.5 font-mono text-[10px] tracking-widest ${PROVENANCE_STYLES[provenance]}`}
    >
      {provenance}
    </span>
  );
}
