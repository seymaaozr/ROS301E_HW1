#!/usr/bin/env bash
# Builds ROS301E_HW1_Report.pdf from report.html using headless Chrome.
set -e
cd "$(dirname "$0")"

python3 - <<'EOF'
import os, re
html = open('report.html', encoding='utf-8').read()
if os.path.exists('img/v4_cancel.png'):
    fig = ('<figure>\n  <img src="img/v4_cancel.png" alt="action cancel">\n'
           '  <figcaption>Figure 7. Cancellation with Ctrl+C: client output (CANCELED, completion_code 1) '
           'and task_manager log ("Return to Dock").</figcaption>\n</figure>')
    html = re.sub(r'<!--V4_CANCEL_START-->.*?<!--V4_CANCEL_END-->', fig, html, flags=re.S)
open('.build.html', 'w', encoding='utf-8').write(html)
EOF

google-chrome --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/ROS301E_HW1_Report.pdf" "file://$PWD/.build.html" 2>/dev/null
rm -f .build.html
echo "Created: $PWD/ROS301E_HW1_Report.pdf"
