#!/bin/sh
# LaunchAgent Installer — curl -fsSL https://launchagent.dev/install | sh
set -e

REPO="jiamingwang1/reddit-pain-radar"
INSTALL_DIR="/usr/local/lib/launchagent"
BIN="/usr/local/bin/launchagent"

echo "🚀 Installing LaunchAgent..."
echo ""

# Check dependencies
for cmd in docker node npm; do
  if ! command -v $cmd >/dev/null 2>&1; then
    echo "❌ $cmd is required but not installed."
    case $cmd in
      docker) echo "   Install: curl -fsSL https://get.docker.com | sh" ;;
      node|npm) echo "   Install: curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt install -y nodejs" ;;
    esac
    exit 1
  fi
done

# Check Docker is running
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker is not running. Start it with: systemctl start docker"
  exit 1
fi

echo "✅ Dependencies OK (docker, node, npm)"

# Download
echo "📦 Downloading LaunchAgent..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

if command -v git >/dev/null 2>&1; then
  git clone --depth 1 "https://github.com/$REPO.git" /tmp/launchagent-install 2>/dev/null
  cp -r /tmp/launchagent-install/launchagent/* "$INSTALL_DIR/"
  rm -rf /tmp/launchagent-install
else
  curl -fsSL "https://github.com/$REPO/archive/main.tar.gz" | tar xz -C /tmp
  cp -r /tmp/reddit-pain-radar-main/launchagent/* "$INSTALL_DIR/"
  rm -rf /tmp/reddit-pain-radar-main
fi

# Install Node dependencies
cd "$INSTALL_DIR"
if [ -f package.json ]; then
  npm install --production 2>/dev/null || true
fi

# Create bin symlink
cat > "$BIN" << 'WRAPPER'
#!/bin/sh
exec node /usr/local/lib/launchagent/src/cli.js "$@"
WRAPPER
chmod +x "$BIN"

echo ""
echo "✅ LaunchAgent installed!"
echo ""
echo "   launchagent deploy openclaw    # Deploy OpenClaw AI Agent"
echo "   launchagent deploy n8n         # Deploy n8n Automation"
echo "   launchagent status             # Check running agents"
echo "   launchagent logs <agent>       # View agent logs"
echo ""
echo "🚀 Get started: launchagent deploy openclaw"
