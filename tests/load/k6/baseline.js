/**
 * k6 Load Test - Baseline Performance Test
 *
 * This script establishes baseline performance metrics for optimal_build API.
 * Run with: k6 run tests/load/k6/baseline.js
 *
 * Metrics collected:
 * - Response times (p50, p90, p95, p99)
 * - Throughput (requests/second)
 * - Error rates
 * - Concurrent user handling
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// Custom metrics
const errorRate = new Rate('errors');
const healthCheckDuration = new Trend('health_check_duration');
const apiLatency = new Trend('api_latency');
const buildableLatency = new Trend('buildable_screening_latency');
const authLatency = new Trend('auth_latency');
const dbQueryCount = new Counter('db_queries');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v1`;

// Test scenarios
export const options = {
  scenarios: {
    // Smoke test - verify system works
    smoke: {
      executor: 'constant-vus',
      vus: 1,
      duration: '30s',
      startTime: '0s',
      tags: { test_type: 'smoke' },
    },
    // Load test - normal expected load
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },  // Ramp up to 50 users
        { duration: '5m', target: 50 },  // Stay at 50 users
        { duration: '2m', target: 0 },   // Ramp down
      ],
      startTime: '30s',
      tags: { test_type: 'load' },
    },
    // Stress test - find breaking point
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '3m', target: 100 },
        { duration: '2m', target: 200 },
        { duration: '3m', target: 200 },
        { duration: '2m', target: 0 },
      ],
      startTime: '10m',
      tags: { test_type: 'stress' },
    },
    // Spike test - sudden traffic surge
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 200 },  // Spike to 200 users
        { duration: '1m', target: 200 },   // Hold
        { duration: '10s', target: 0 },    // Drop
      ],
      startTime: '23m',
      tags: { test_type: 'spike' },
    },
  },
  thresholds: {
    // SLO: 99% of requests should be under 500ms
    http_req_duration: ['p(99)<500'],
    // SLO: Error rate should be under 1%
    errors: ['rate<0.01'],
    // SLO: Health checks should be fast
    health_check_duration: ['p(95)<100'],
    // Custom latency thresholds
    api_latency: ['p(95)<300'],
    buildable_screening_latency: ['p(95)<2000'],
  },
};

// Test data
const testAddresses = [
  '123 Orchard Road, Singapore 238867',
  '1 Raffles Place, Singapore 048616',
  '10 Marina Boulevard, Singapore 018983',
  '50 Collyer Quay, Singapore 049321',
  '8 Shenton Way, Singapore 068811',
];

const testUsers = [
  { email: 'test1@example.com', password: 'TestPass123!' },
  { email: 'test2@example.com', password: 'TestPass123!' },
  { email: 'test3@example.com', password: 'TestPass123!' },
];

// Helper functions
function getRandomAddress() {
  return testAddresses[randomIntBetween(0, testAddresses.length - 1)];
}

function getHeaders(token = null) {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// Setup - runs once at the start
export function setup() {
  console.log(`Running load tests against: ${BASE_URL}`);

  // Verify system is up
  const healthRes = http.get(`${BASE_URL}/health`);
  if (healthRes.status !== 200) {
    throw new Error(`Health check failed: ${healthRes.status}`);
  }

  return {
    startTime: new Date().toISOString(),
  };
}

// Main test function
export default function (data) {
  group('Health Checks', function () {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/health`);
    healthCheckDuration.add(Date.now() - start);

    check(res, {
      'health check returns 200': (r) => r.status === 200,
      'health check has status': (r) => {
        const body = JSON.parse(r.body);
        return body.status === 'healthy';
      },
    }) || errorRate.add(1);
  });

  group('API Endpoints', function () {
    // Test root endpoint
    const rootRes = http.get(BASE_URL);
    check(rootRes, {
      'root returns 200': (r) => r.status === 200,
    });

    // Test API version endpoint
    const start = Date.now();
    const testRes = http.get(`${API_BASE}/test`, {
      headers: getHeaders(),
    });
    apiLatency.add(Date.now() - start);

    // Accept 401 (unauthenticated) or 200 (authenticated)
    check(testRes, {
      'test endpoint responds': (r) => r.status === 200 || r.status === 401,
    }) || errorRate.add(1);
  });

  group('Buildable Screening', function () {
    const payload = JSON.stringify({
      address: getRandomAddress(),
      typ_floor_to_floor_m: 3.4 + Math.random() * 0.6,
      efficiency_ratio: 0.75 + Math.random() * 0.1,
    });

    const start = Date.now();
    const res = http.post(`${API_BASE}/screen/buildable`, payload, {
      headers: getHeaders(),
    });
    buildableLatency.add(Date.now() - start);

    check(res, {
      'buildable returns 200': (r) => r.status === 200,
      'buildable has zone_code': (r) => {
        if (r.status !== 200) return true; // Skip for auth failures
        const body = JSON.parse(r.body);
        return body.zone_code !== undefined;
      },
      'buildable has metrics': (r) => {
        if (r.status !== 200) return true;
        const body = JSON.parse(r.body);
        return body.metrics !== undefined;
      },
    }) || errorRate.add(1);

    dbQueryCount.add(1);
  });

  group('Rules Endpoint', function () {
    const res = http.get(`${API_BASE}/rules/count`, {
      headers: getHeaders(),
    });

    check(res, {
      'rules count responds': (r) => r.status === 200 || r.status === 401,
    });
  });

  // Random sleep between 1-3 seconds to simulate real user behavior
  sleep(randomIntBetween(1, 3));
}

// Teardown - runs once at the end
export function teardown(data) {
  console.log(`Load test completed. Started at: ${data.startTime}`);
}

// Handle summary
export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    metrics: {
      http_reqs: data.metrics.http_reqs?.values?.count || 0,
      http_req_duration_p95: data.metrics.http_req_duration?.values?.['p(95)'] || 0,
      http_req_duration_p99: data.metrics.http_req_duration?.values?.['p(99)'] || 0,
      error_rate: data.metrics.errors?.values?.rate || 0,
      health_check_p95: data.metrics.health_check_duration?.values?.['p(95)'] || 0,
      api_latency_p95: data.metrics.api_latency?.values?.['p(95)'] || 0,
      buildable_latency_p95: data.metrics.buildable_screening_latency?.values?.['p(95)'] || 0,
    },
    thresholds_passed: Object.keys(data.metrics)
      .filter(k => data.metrics[k].thresholds)
      .every(k => Object.values(data.metrics[k].thresholds).every(t => t.ok)),
  };

  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'tests/load/results/summary.json': JSON.stringify(summary, null, 2),
  };
}

// Text summary helper
function textSummary(data, options) {
  const lines = [
    '\n=== Load Test Summary ===\n',
    `Total Requests: ${data.metrics.http_reqs?.values?.count || 0}`,
    `Request Rate: ${(data.metrics.http_reqs?.values?.rate || 0).toFixed(2)}/s`,
    `\nResponse Times:`,
    `  p50: ${(data.metrics.http_req_duration?.values?.['p(50)'] || 0).toFixed(2)}ms`,
    `  p90: ${(data.metrics.http_req_duration?.values?.['p(90)'] || 0).toFixed(2)}ms`,
    `  p95: ${(data.metrics.http_req_duration?.values?.['p(95)'] || 0).toFixed(2)}ms`,
    `  p99: ${(data.metrics.http_req_duration?.values?.['p(99)'] || 0).toFixed(2)}ms`,
    `\nError Rate: ${((data.metrics.errors?.values?.rate || 0) * 100).toFixed(2)}%`,
    '\n========================\n',
  ];
  return lines.join('\n');
}
