/**
 * Cross-platform port killer for port 5328.
 * Used as a prestart script to ensure the port is free before starting the app.
 */

const { execSync } = require('child_process');
const os = require('os');

const PORT = 5328;

try {
  if (os.platform() === 'win32') {
    // Windows: parse netstat output to find PIDs listening on the port
    try {
      const output = execSync(`netstat -ano`, { encoding: 'utf-8' });
      const lines = output.split('\n');
      const pids = new Set();

      for (const line of lines) {
        // Match lines that contain :5328 and LISTENING
        if (line.includes(`:${PORT}`) && line.includes('LISTENING')) {
          const parts = line.trim().split(/\s+/);
          const pid = parts[parts.length - 1];
          if (pid && pid !== '0') {
            pids.add(pid);
          }
        }
      }

      for (const pid of pids) {
        try {
          execSync(`taskkill /F /PID ${pid}`, { stdio: 'ignore' });
          console.log(`Killed process ${pid} on port ${PORT}`);
        } catch (e) {
          // Process may have already exited
        }
      }
    } catch (e) {
      // netstat command failed, ignore
    }
  } else {
    // Unix (macOS / Linux): use lsof to find and kill processes
    try {
      execSync(`lsof -ti:${PORT} | xargs kill -9`, { stdio: 'ignore' });
    } catch (e) {
      // No process on that port, or kill failed — that's fine
    }
  }
} catch (e) {
  // Silently fail — the port may already be free
}
