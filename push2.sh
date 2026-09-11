#!/bin/bash
cd ~/moseyuh333-profile
echo "=== XML validity check ==="
for f in assets/banner.svg assets/divider.svg assets/langs.svg assets/signal.svg assets/now-playing.svg; do
  python -c "import xml.dom.minidom,sys; xml.dom.minidom.parse('$f'); print('OK  $f')" 2>&1
done
echo
echo "=== commit + push ==="
git add -A
git -c user.name=Moseyuh333 -c user.email=23162046@student.hcmute.edu.vn commit -m "redesign: fix broken stats links, de-slop copy, hand-drawn signal/langs boards, now-playing VOSZA widget" 2>&1 | tail -2
git push 2>&1 | tail -2
