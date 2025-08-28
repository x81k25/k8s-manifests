#!/bin/bash

# OSRM Server API Endpoints Test Suite
# Tests all available OSRM HTTP API endpoints

set +e

# Configuration
OSRM_HOST="localhost"
OSRM_PORT="5000"
BASE_URL="http://${OSRM_HOST}:${OSRM_PORT}"
PROFILE="driving"
API_VERSION="v1"

# Test coordinates (San Francisco area)
SF_COORDS="-122.4194,37.7749"
OAKLAND_COORDS="-122.2711,37.8044"
SAN_JOSE_COORDS="-121.8863,37.3382"
BERKELEY_COORDS="-122.2585,37.8716"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_test() {
    echo -e "${YELLOW}Testing: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

test_endpoint() {
    local endpoint="$1"
    local description="$2"
    local expected_code="${3:-200}"
    
    print_test "$description"
    echo "URL: $endpoint"
    
    # Make request and capture response
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$endpoint" 2>/dev/null)
    http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]*$//')
    
    if [ "$http_code" -eq "$expected_code" ]; then
        print_success "HTTP $http_code - Success"
        echo "Response preview: $(echo "$body" | head -c 150)..."
        echo
    else
        print_error "HTTP $http_code - Expected $expected_code"
        echo "Response: $body"
        echo
        return 1
    fi
}

# Check if server is running
print_header "Server Health Check"
if ! curl -s "$BASE_URL" >/dev/null 2>&1; then
    print_error "OSRM server is not responding at $BASE_URL"
    echo "Make sure the server is running with: docker-compose -f docker-compose.server.yml up -d"
    exit 1
fi
print_success "Server is responding"

# Test Route Service
print_header "Route Service Tests"

test_endpoint \
    "$BASE_URL/route/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS" \
    "Basic route from SF to Oakland"

test_endpoint \
    "$BASE_URL/route/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS?overview=false" \
    "Route without geometry overview"

test_endpoint \
    "$BASE_URL/route/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS?steps=true" \
    "Route with turn-by-turn steps"

test_endpoint \
    "$BASE_URL/route/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS?alternatives=true" \
    "Route with alternatives"

test_endpoint \
    "$BASE_URL/route/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS;$SAN_JOSE_COORDS" \
    "Multi-waypoint route (SF -> Oakland -> San Jose)"

# Test Nearest Service
print_header "Nearest Service Tests"

test_endpoint \
    "$BASE_URL/nearest/$API_VERSION/$PROFILE/$SF_COORDS" \
    "Find nearest road point to SF coordinates"

test_endpoint \
    "$BASE_URL/nearest/$API_VERSION/$PROFILE/$SF_COORDS?number=3" \
    "Find 3 nearest road points"

# Test Table Service
print_header "Table Service Tests"

test_endpoint \
    "$BASE_URL/table/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS;$SAN_JOSE_COORDS" \
    "Distance/duration matrix for 3 points"

test_endpoint \
    "$BASE_URL/table/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS;$SAN_JOSE_COORDS?sources=0" \
    "Distance matrix with specific source"

test_endpoint \
    "$BASE_URL/table/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS?annotations=distance,duration" \
    "Table with distance and duration annotations"

# Test Match Service
print_header "Match Service Tests"

# GPS trace coordinates (slightly noisy path)
GPS_TRACE="$SF_COORDS;-122.4190,37.7750;-122.4185,37.7751;$OAKLAND_COORDS"

test_endpoint \
    "$BASE_URL/match/$API_VERSION/$PROFILE/$GPS_TRACE" \
    "GPS trace matching"

test_endpoint \
    "$BASE_URL/match/$API_VERSION/$PROFILE/$GPS_TRACE?overview=full&steps=true" \
    "GPS trace matching with full overview and steps"

# Test Trip Service (Traveling Salesman Problem)
print_header "Trip Service Tests"

test_endpoint \
    "$BASE_URL/trip/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS;$SAN_JOSE_COORDS;$BERKELEY_COORDS" \
    "Trip optimization for 4 cities"

test_endpoint \
    "$BASE_URL/trip/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS;$SAN_JOSE_COORDS?source=first&destination=last" \
    "Trip with fixed start and end points"

test_endpoint \
    "$BASE_URL/trip/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS;$SAN_JOSE_COORDS?roundtrip=false" \
    "One-way trip (no return to start)"

# Test Tile Service
print_header "Tile Service Tests"

test_endpoint \
    "$BASE_URL/tile/$API_VERSION/$PROFILE/10/163/395.mvt" \
    "Vector tile request (SF area, zoom 10)"

# Error condition tests
print_header "Error Condition Tests"

test_endpoint \
    "$BASE_URL/route/$API_VERSION/$PROFILE/invalid,coords" \
    "Invalid coordinates should return 400" \
    400

test_endpoint \
    "$BASE_URL/route/$API_VERSION/invalid_profile/$SF_COORDS;$OAKLAND_COORDS" \
    "Invalid profile should return 400" \
    400

# Summary
print_header "Test Summary"
echo -e "${GREEN}All endpoint tests completed!${NC}"
echo -e "${BLUE}Server: $BASE_URL${NC}"
echo -e "${BLUE}Profile: $PROFILE${NC}"
echo -e "${BLUE}Test coordinates covered SF Bay Area${NC}"
echo
echo "For more detailed API documentation, visit:"
echo "https://project-osrm.org/docs/v5.24.0/api/"
echo
echo "To view the full response data, run individual curl commands:"
echo "curl \"$BASE_URL/route/$API_VERSION/$PROFILE/$SF_COORDS;$OAKLAND_COORDS?steps=true\" | jq ."