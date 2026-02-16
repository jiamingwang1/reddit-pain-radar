/**
 * Agent Registry — available frameworks and their configs
 */

export const AGENTS = {
  openclaw: {
    name: 'OpenClaw',
    description: 'AI Employee / Personal Assistant',
    version: 'latest',
    defaultPort: 3000,
    compose: 'templates/openclaw/docker-compose.yml',
    env: 'templates/openclaw/.env.template',
    requiredEnv: ['ANTHROPIC_API_KEY'],
    optionalEnv: ['DISCORD_TOKEN', 'TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY'],
    healthCheck: '/health',
    docs: 'https://docs.openclaw.ai',
  },
  n8n: {
    name: 'n8n',
    description: 'Workflow Automation Platform',
    version: '1.70.0',
    defaultPort: 5678,
    compose: null, // TODO
    requiredEnv: [],
    optionalEnv: ['N8N_BASIC_AUTH_USER', 'N8N_BASIC_AUTH_PASSWORD'],
    healthCheck: '/healthz',
    docs: 'https://docs.n8n.io',
    status: 'planned',
  },
  dify: {
    name: 'Dify',
    description: 'AI Application Platform',
    version: 'latest',
    defaultPort: 3000,
    compose: null,
    requiredEnv: [],
    healthCheck: '/health',
    docs: 'https://docs.dify.ai',
    status: 'planned',
  },
  lobechat: {
    name: 'LobeChat',
    description: 'AI Chat Application',
    version: 'latest',
    defaultPort: 3210,
    compose: null,
    requiredEnv: [],
    healthCheck: '/',
    docs: 'https://lobehub.com/docs',
    status: 'planned',
  },
};

export async function list() {
  console.log('\n📦 Available AI Agents:\n');
  for (const [key, agent] of Object.entries(AGENTS)) {
    const st = agent.status === 'planned' ? '🟡 planned' : '🟢 ready';
    console.log(`  ${key.padEnd(12)} ${agent.name.padEnd(15)} ${agent.description}  [${st}]`);
  }
  console.log('\nUse: launchagent deploy <agent>\n');
}
