#!/bin/bash
echo "=== raw banner ==="
curl -s -o /dev/null -w "%{http_code} %{content_type} %{size_download}B\n" "https://raw.githubusercontent.com/Moseyuh333/Moseyuh333/main/assets/banner.svg"
echo "=== raw divider ==="
curl -s -o /dev/null -w "%{http_code} %{content_type}\n" "https://raw.githubusercontent.com/Moseyuh333/Moseyuh333/main/assets/divider.svg"
echo "=== profile page README text present? ==="
curl -s "https://github.com/Moseyuh333" -o /tmp/profile.html && grep -c "Network Security là chính" /tmp/profile.html
echo "=== camo-proxied images ==="
grep -o 'camo\.githubusercontent\.com[^"]*' /tmp/profile.html | head -3
