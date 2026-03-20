// @ts-check
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './e2e',
  timeout: 15000,
  use: {
    baseURL: 'http://localhost:8082',
    headless: true,
  },
  webServer: {
    command: 'python3 -m http.server 8082 --directory ..',
    url: 'http://localhost:8082',
    reuseExistingServer: false,
    timeout: 10000,
  },
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
});
