import { ProvenanceBadge, type Provenance } from "@/components/ProvenanceBadge";
import { SectionPlaceholder } from "@/components/SectionPlaceholder";

const PROVENANCE_LEGEND: Provenance[] = ["LIVE", "REPLAY", "IMPORT", "SYNTHETIC"];

export default function OverviewPage() {
  return (
    <div className="flex flex-col gap-8">
      <SectionPlaceholder href="/" />
      <section className="flex flex-col gap-3">
        <h2 className="font-mono text-[11px] tracking-[0.2em] text-ink-faint">PROVENANCE LEGEND</h2>
        <div className="flex flex-wrap gap-2">
          {PROVENANCE_LEGEND.map((provenance) => (
            <ProvenanceBadge key={provenance} provenance={provenance} />
          ))}
        </div>
      </section>
    </div>
  );
}
