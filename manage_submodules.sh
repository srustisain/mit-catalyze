#!/bin/bash
# Submodule management script for mit-catalyze

set -e

echo "🔧 ChEMBL MCP Server Submodule Management"
echo "=========================================="

case "${1:-help}" in
    "init")
        echo "📥 Initializing submodules..."
        git submodule init
        git submodule update
        echo "✅ Submodules initialized"
        ;;
    "update")
        echo "🔄 Updating submodules..."
        git submodule update --remote --merge
        echo "✅ Submodules updated"
        ;;
    "install")
        echo "📦 Installing Node.js dependencies..."
        cd mcp_servers/chembl-mcp-server
        npm install
        npm run build
        cd ../..
        echo "✅ Dependencies installed and built"
        ;;
    "status")
        echo "📊 Submodule status:"
        git submodule status
        ;;
    "clean")
        echo "🧹 Cleaning submodule..."
        git submodule deinit -f mcp_servers/chembl-mcp-server
        rm -rf .git/modules/mcp_servers/chembl-mcp-server
        git rm -f mcp_servers/chembl-mcp-server
        echo "✅ Submodule removed"
        ;;
    "help"|*)
        echo "Usage: $0 {init|update|install|status|clean}"
        echo ""
        echo "Commands:"
        echo "  init     - Initialize submodules for the first time"
        echo "  update   - Update submodules to latest versions"
        echo "  install  - Install Node.js dependencies and build"
        echo "  status   - Show submodule status"
        echo "  clean    - Remove submodule completely"
        echo "  help     - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 init     # First time setup"
        echo "  $0 install  # After cloning the repo"
        echo "  $0 update   # Get latest ChEMBL MCP Server"
        ;;
esac
