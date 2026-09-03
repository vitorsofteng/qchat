// Configuracao de ambiente, resolvida em tempo de execucao.
//   localhost  -> backend de desenvolvimento em :8000
//   producao   -> proxy reverso nginx na mesma origem (/api e /ws)
const host = typeof location !== 'undefined' ? location.hostname : '';
const isLocal = host === 'localhost' || host === '127.0.0.1' || host === '';

export const environment = {
  production: !isLocal,
  apiBaseUrl: isLocal ? 'http://localhost:8000' : '/api',
  // Vazio em producao: o WebSocketService deriva wss://<host> da pagina.
  wsBaseUrl: isLocal ? 'ws://localhost:8000' : '',
};
