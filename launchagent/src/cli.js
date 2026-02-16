#!/usr/bin/env node
/**
 * LaunchAgent CLI — Deploy AI Agents in One Command
 */

import { parseArgs } from 'node:util';
import { deploy } from './deploy.js';
import { status } from './status.js';
import { logs } from './logs.js';
import { stop } from './stop.js';
import { list } from './registry.js';

const HELP = `
LaunchAgent 🚀 — Deploy AI Agents in One Command

Usage:
  launchagent deploy <agent>   Deploy an AI agent (openclaw, n8n, dify, ...)
  launchagent status [agent]   Show running agent status
  launchagent logs <agent>     Tail agent logs
  launchagent stop <agent>     Stop a running agent
  launchagent list             List available agents
  launchagent help             Show this help

Options:
  --port <port>       Override default port
  --domain <domain>   Set domain for SSL
  --data <dir>        Data directory (default: ~/.launchagent)
  --no-ssl            Disable auto SSL

Examples:
  launchagent deploy openclaw
  launchagent deploy n8n --port 5678 --domain n8n.example.com
  launchagent status
`;

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  const target = args[1];

  const opts = {};
  for (let i = 2; i < args.length; i++) {
    if (args[i] === '--port') opts.port = parseInt(args[++i]);
    else if (args[i] === '--domain') opts.domain = args[++i];
    else if (args[i] === '--data') opts.dataDir = args[++i];
    else if (args[i] === '--no-ssl') opts.ssl = false;
  }

  switch (command) {
    case 'deploy':
      if (!target) { console.error('Usage: launchagent deploy <agent>'); process.exit(1); }
      await deploy(target, opts);
      break;
    case 'status':
      await status(target);
      break;
    case 'logs':
      if (!target) { console.error('Usage: launchagent logs <agent>'); process.exit(1); }
      await logs(target, opts);
      break;
    case 'stop':
      if (!target) { console.error('Usage: launchagent stop <agent>'); process.exit(1); }
      await stop(target, opts);
      break;
    case 'list':
      await list();
      break;
    case 'help':
    case '--help':
    case '-h':
    case undefined:
      console.log(HELP);
      break;
    default:
      console.error(`Unknown command: ${command}\n`);
      console.log(HELP);
      process.exit(1);
  }
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
