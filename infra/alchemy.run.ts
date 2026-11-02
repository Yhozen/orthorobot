import * as Alchemy from "alchemy";
import * as Cloudflare from "@alchemy.run/cloudflare";
import * as Effect from "effect/Effect";

export default Alchemy.Stack(
  "orthorobot",
  {
    providers: Cloudflare.providers(),
    state: Cloudflare.state({ name: "orthorobot" }),
  },
  Effect.gen(function* () {
    const site = yield* Cloudflare.Worker("Website", {
      assets: { directory: "../dist" },
      domain: "orthorobot.rccpr.tech",
    });
    return { url: site.url };
  }),
);
