#!/bin/bash
# Test script for cfmm2tar argument parsing
# This script verifies that the cfmm2tar script handles arguments correctly

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CFMM2TAR="${SCRIPT_DIR}/../cfmm2tar"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

echo "=========================================="
echo "cfmm2tar Argument Parsing Tests"
echo "=========================================="
echo ""

# Setup test environment
TEST_DIR=$(mktemp -d)
trap "rm -rf ${TEST_DIR}" EXIT

# Create mock credentials
cat > ${TEST_DIR}/.credentials << EOF
testuser
testpass
EOF

# Create mock retrieve_cfmm_tar.py that just prints arguments
cat > ${TEST_DIR}/retrieve_cfmm_tar.py << 'EOF'
#!/usr/bin/env python
import sys
# Just exit successfully - we're testing argument parsing, not execution
sys.exit(0)
EOF
chmod +x ${TEST_DIR}/retrieve_cfmm_tar.py

# Create test version of cfmm2tar
cp ${CFMM2TAR} ${TEST_DIR}/cfmm2tar_test
# Point to our mock python script
sed -i "s|python \$execpath/retrieve_cfmm_tar.py|python ${TEST_DIR}/retrieve_cfmm_tar.py|" ${TEST_DIR}/cfmm2tar_test

# Set required environment variable
export DICOM_CONNECTION="TEST@localhost:11112"

# Test function
run_test() {
    local test_name="$1"
    shift
    local args="$@"
    
    echo "Test: ${test_name}"
    echo "  Command: cfmm2tar ${args}"
    
    OUTPUT_DIR="${TEST_DIR}/output_$$"
    mkdir -p "${OUTPUT_DIR}"
    
    # Run the command and capture output and exit code
    set +e
    ERROR_OUTPUT=$(bash ${TEST_DIR}/cfmm2tar_test -c ${TEST_DIR}/.credentials ${args} ${OUTPUT_DIR} 2>&1)
    EXIT_CODE=$?
    set -e
    
    # Check for the specific error
    if echo "${ERROR_OUTPUT}" | grep -q "False: not found"; then
        echo -e "  ${RED}✗ FAILED${NC}: 'False: not found' error detected"
        echo "  Output: ${ERROR_OUTPUT}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    elif [ ${EXIT_CODE} -ne 0 ] && echo "${ERROR_OUTPUT}" | grep -qE "(Error|error|ERROR)"; then
        # Check if it's an expected error (like missing DICOM connection)
        if echo "${ERROR_OUTPUT}" | grep -qE "(DICOM|connection|connect)"; then
            echo -e "  ${GREEN}✓ PASSED${NC} (expected connection error, not argument parsing error)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            echo -e "  ${RED}✗ FAILED${NC}: Unexpected error"
            echo "  Output: ${ERROR_OUTPUT}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        echo -e "  ${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    fi
}

# Run tests
echo "Running tests..."
echo ""

run_test "Basic usage without -U option" "-d '20250101'"
run_test "Date range" "-d '20250101-20251101'"
run_test "With -U option" "-U ${TEST_DIR}/uid_list.txt -d '20250101'"
run_test "With -l and -U options (list-only mode)" "-l -U ${TEST_DIR}/uid_list.tsv -p 'Khan^Project'"
run_test "With patient name search" "-n '*Patient*' -d '20250101'"
run_test "With project search" "-p 'Khan^Project' -d '20250101'"

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="
echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ ${TESTS_FAILED} -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
