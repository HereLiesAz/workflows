// Lets Node import src/index.js, which imports the Workers-only "cloudflare:workers".
export async function resolve(specifier, context, nextResolve) {
  if (specifier === "cloudflare:workers") {
    return { url: "data:text/javascript,export class WorkerEntrypoint {}", shortCircuit: true };
  }
  return nextResolve(specifier, context);
}
