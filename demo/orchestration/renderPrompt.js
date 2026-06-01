const VAR_RE = /\{\{\s*([A-Za-z0-9_]+)\s*\}\}/g;

export function renderPrompt(spec, promptId, vars = {}) {
  const prompt = spec?.prompts?.[promptId];
  if (!prompt) throw new Error(`renderPrompt: no prompt "${promptId}" in spec "${spec?.id}"`);

  const subst = (s) =>
    typeof s === "string" ? s.replace(VAR_RE, (_, name) => (vars[name] ?? "")) : s;

  return {
    system: subst(prompt.system),
    user: subst(prompt.user),
  };
}
