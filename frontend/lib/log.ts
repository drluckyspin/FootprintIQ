/**
 * Server-side logging for Route Handlers (level from SQFT_LOG_LEVEL in root .env).
 */

const LEVELS = { DEBUG: 0, INFO: 1, WARNING: 2, ERROR: 3 } as const;

function configuredLevel(): number {
  const raw = (process.env.SQFT_LOG_LEVEL ?? "INFO").toUpperCase();
  return LEVELS[raw as keyof typeof LEVELS] ?? LEVELS.INFO;
}

function shouldLog(level: keyof typeof LEVELS): boolean {
  return LEVELS[level] >= configuredLevel();
}

function prefix(scope: string): string {
  const ts = new Date().toISOString().slice(11, 19);
  return `${ts} [sqft.${scope}]`;
}

export const sqftLog = {
  debug(scope: string, message: string, extra?: unknown) {
    if (!shouldLog("DEBUG")) return;
    if (extra !== undefined) {
      console.debug(prefix(scope), message, extra);
    } else {
      console.debug(prefix(scope), message);
    }
  },
  info(scope: string, message: string, extra?: unknown) {
    if (!shouldLog("INFO")) return;
    if (extra !== undefined) {
      console.info(prefix(scope), message, extra);
    } else {
      console.info(prefix(scope), message);
    }
  },
  warn(scope: string, message: string, extra?: unknown) {
    if (!shouldLog("WARNING")) return;
    console.warn(prefix(scope), message, extra ?? "");
  },
};
