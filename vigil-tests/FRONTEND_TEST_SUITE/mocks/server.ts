/**
 * MSW Server Setup
 * Creates and exports the mock service worker server for tests
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);

/**
 * Reset handlers to defaults
 */
export const resetHandlers = () => {
  server.resetHandlers();
  server.use(...handlers);
};

/**
 * Add temporary handlers for specific test scenarios
 */
export const addHandlers = (...newHandlers: Parameters<typeof server.use>) => {
  server.use(...newHandlers);
};
