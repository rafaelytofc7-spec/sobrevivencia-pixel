// Service worker mínimo: deixa o jogo "instalável" no Android (Adicionar à tela inicial).
// Não guarda nada em cache: sempre baixa a versão mais nova.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", () => {});
