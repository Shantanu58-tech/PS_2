// SATYA-NET keep-alive: free Hugging Face Spaces sleep after long inactivity.
// A Cloudflare cron trigger pings the health endpoint every 10 minutes.
const TARGET = "https://zoroxjodd-satyanet.hf.space/healthz";

async function ping() {
  const started = Date.now();
  try {
    const res = await fetch(TARGET, { headers: { "User-Agent": "satyanet-keepalive/1.0" } });
    return { ok: res.ok, status: res.status, ms: Date.now() - started };
  } catch (err) {
    return { ok: false, status: 0, ms: Date.now() - started, error: String(err) };
  }
}

export default {
  async scheduled(_event, _env, ctx) {
    ctx.waitUntil(ping().then((r) => console.log("keepalive", JSON.stringify(r))));
  },
  async fetch() {
    const r = await ping();
    return new Response(JSON.stringify({ target: TARGET, ...r }, null, 2), {
      headers: { "content-type": "application/json" },
      status: r.ok ? 200 : 502,
    });
  },
};
