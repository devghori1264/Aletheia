#!/bin/bash
# =============================================================================
# Aletheia - Production Health Check Script
# =============================================================================
# This script verifies all production services are running correctly.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Header
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🛡️  ALETHEIA - Production Health Check                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check functions
check_docker() {
    echo -e "${YELLOW}[1/7] Checking Docker...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}    ✗ Docker not installed${NC}"
        return 1
    fi
    echo -e "${GREEN}    ✓ Docker installed${NC}"
}

check_postgres() {
    echo -e "${YELLOW}[2/7] Checking PostgreSQL container...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "aletheia-postgres"; then
        STATUS=$(docker inspect -f '{{.State.Health.Status}}' aletheia-postgres 2>/dev/null || echo "unknown")
        if [ "$STATUS" = "healthy" ]; then
            echo -e "${GREEN}    ✓ PostgreSQL is running and healthy${NC}"
        else
            echo -e "${YELLOW}    ⚠ PostgreSQL is running but status: $STATUS${NC}"
        fi
    else
        echo -e "${RED}    ✗ PostgreSQL container not running${NC}"
        echo -e "    Run: docker-compose up -d postgres"
        return 1
    fi
}

check_redis() {
    echo -e "${YELLOW}[3/7] Checking Redis container...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "aletheia-redis"; then
        STATUS=$(docker inspect -f '{{.State.Health.Status}}' aletheia-redis 2>/dev/null || echo "unknown")
        if [ "$STATUS" = "healthy" ]; then
            echo -e "${GREEN}    ✓ Redis is running and healthy${NC}"
        else
            echo -e "${YELLOW}    ⚠ Redis is running but status: $STATUS${NC}"
        fi
    else
        echo -e "${RED}    ✗ Redis container not running${NC}"
        echo -e "    Run: docker-compose up -d redis"
        return 1
    fi
}

check_env_file() {
    echo -e "${YELLOW}[4/7] Checking environment configuration...${NC}"
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo -e "${RED}    ✗ .env file not found${NC}"
        return 1
    fi
    
    ENV_MODE=$(grep "ALETHEIA_ENVIRONMENT=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)
    DEBUG_MODE=$(grep "^DEBUG=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)
    DB_URL=$(grep "^DATABASE_URL=" "$PROJECT_ROOT/.env" | cut -d'=' -f2)
    
    echo -e "${GREEN}    ✓ .env file found${NC}"
    echo -e "      Mode: $ENV_MODE"
    echo -e "      Debug: $DEBUG_MODE"
    
    if [ "$ENV_MODE" = "production" ] && [ "$DEBUG_MODE" != "false" ]; then
        echo -e "${RED}    ✗ Production mode should have DEBUG=false${NC}"
        return 1
    fi
}

check_database_connection() {
    echo -e "${YELLOW}[5/7] Checking database connectivity...${NC}"
    cd "$PROJECT_ROOT/src"
    
    # Try to run a simple Django command that requires DB
    if python manage.py showmigrations --plan &> /dev/null; then
        echo -e "${GREEN}    ✓ Database connection successful${NC}"
    else
        echo -e "${RED}    ✗ Cannot connect to database${NC}"
        echo -e "    Check DATABASE_URL in .env matches docker-compose.yml"
        return 1
    fi
}

check_migrations() {
    echo -e "${YELLOW}[6/7] Checking database migrations...${NC}"
    cd "$PROJECT_ROOT/src"
    
    UNAPPLIED=$(python manage.py showmigrations --plan 2>/dev/null | grep "\[ \]" | wc -l | tr -d ' ')
    
    if [ "$UNAPPLIED" -eq 0 ]; then
        echo -e "${GREEN}    ✓ All migrations applied${NC}"
    else
        echo -e "${YELLOW}    ⚠ $UNAPPLIED unapplied migrations found${NC}"
        echo -e "    Run: cd src && python manage.py migrate"
    fi
}

check_static_files() {
    echo -e "${YELLOW}[7/7] Checking static files...${NC}"
    if [ -d "$PROJECT_ROOT/staticfiles" ] && [ "$(ls -A $PROJECT_ROOT/staticfiles 2>/dev/null)" ]; then
        echo -e "${GREEN}    ✓ Static files collected${NC}"
    else
        echo -e "${YELLOW}    ⚠ Static files not collected${NC}"
        echo -e "    Run: cd src && python manage.py collectstatic --noinput"
    fi
}

# Run all checks
FAILED=0

check_docker || FAILED=1
check_postgres || FAILED=1
check_redis || FAILED=1
check_env_file || FAILED=1
check_database_connection || FAILED=1
check_migrations || FAILED=1
check_static_files || FAILED=1

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════════════${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Production environment is ready.${NC}"
    echo ""
    echo -e "Start the server with:"
    echo -e "  ${BLUE}cd src && python manage.py runserver 0.0.0.0:8000${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi
