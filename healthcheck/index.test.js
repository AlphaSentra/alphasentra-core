const { sum, getHealth } = require('./index');
const axios = require('axios');
const cron = require('node-cron');

jest.mock('axios');
jest.mock('node-cron', () => ({
  schedule: jest.fn(() => ({
    start: jest.fn(),
    stop: jest.fn()
  }))
}));

let originalConsole;

beforeAll(() => {
  originalConsole = global.console;
  jest.useFakeTimers();
});

afterAll(() => {
  global.console = originalConsole;
  jest.useRealTimers();
});

beforeEach(() => {
  jest.clearAllMocks();
  cron.schedule.mockClear();
  jest.clearAllTimers();
});

afterEach(() => {
  jest.runAllTimers();
  jest.clearAllTimers();
  jest.resetAllMocks();
});

// Existing sum tests
test('adds 1 + 2 to equal 3', () => {
  expect(sum(1, 2)).toBe(3);
});

test('adds 0 + 0 to equal 0', () => {
  expect(sum(0, 0)).toBe(0);
});

test('adds negative numbers correctly', () => {
  expect(sum(-1, -2)).toBe(-3);
});

// New tests for URL pinging functionality
describe('getHealth', () => {
  const testURL = 'https://example.com';

  test('successfully pings URL', async () => {
    axios.get.mockResolvedValue({ data: 'pong' });
    const result = await getHealth(testURL);
    expect(axios.get).toHaveBeenCalledWith(testURL);
    expect(result).toBe('pong');
  });

  test('handles failed ping', async () => {
    const errorMessage = 'Network Error';
    axios.get.mockRejectedValue(new Error(errorMessage));
    const consoleSpy = jest.spyOn(console, 'log');

    await expect(getHealth(testURL)).rejects.toThrow(errorMessage);
    
    expect(axios.get).toHaveBeenCalledWith(testURL);
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('error:'),
      expect.objectContaining({ message: errorMessage })
    );
  });
});