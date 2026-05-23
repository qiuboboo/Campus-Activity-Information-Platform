/**
 * GET /api/health
 */

export default {
  method: 'GET',
  path: '/api/health',
  handler: async () => ({
    status: 'ok',
    service: 'campus-activity-frontend-mock',
    timestamp: new Date().toISOString(),
  }),
}
