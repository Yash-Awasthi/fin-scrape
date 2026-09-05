import dotenv from 'dotenv';
dotenv.config();

import express from 'express';
import cors from 'cors';
import { router } from './routes/api';
import { rateLimiter } from './middleware/rateLimiter';
import { createWSServer } from './websocket/server';

const PORT = parseInt(process.env.PORT || '3001', 10);
const WS_PORT = parseInt(process.env.WS_PORT || '3002', 10);

const app = express();

app.use(cors());
app.use(express.json());
app.use(rateLimiter);
app.use('/api', router);

const server = app.listen(PORT, () => {
  console.log(`[Server] HTTP server running on port ${PORT}`);
  console.log(`[Server] API available at http://localhost:${PORT}/api`);
});

const wsServer = createWSServer(WS_PORT);
console.log(`[Server] WebSocket server running on port ${WS_PORT}`);

function shutdown() {
  console.log('\n[Server] Shutting down...');
  wsServer.shutdown();
  server.close(() => {
    console.log('[Server] HTTP server closed');
    process.exit(0);
  });
  setTimeout(() => process.exit(1), 5000);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
