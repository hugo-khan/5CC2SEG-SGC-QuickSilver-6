#!/bin/bash
# Script to run test coverage

cd /Users/ameytripathi/5CC2SEG-SGC-QuickSilver-6
source venv/bin/activate

# Run coverage
coverage run --source='.' manage.py test --keepdb
coverage report
coverage html

echo ""
echo "Coverage report generated. Open htmlcov/index.html in your browser to view detailed coverage."

