export function saveRememberedConfig(key: string, value: unknown, remember: boolean): void {
  if (typeof window === "undefined") return;
  if (remember) {
    window.localStorage.setItem(key, JSON.stringify(value));
  } else {
    window.localStorage.removeItem(key);
  }
}
