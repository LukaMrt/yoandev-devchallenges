#!/bin/sh
set -e

echo "🚀 Starting AI Idea Generator..."

# Clear and warm up cache with runtime environment
echo "🔥 Warming up Symfony cache..."
php bin/console cache:clear --no-warmup
php bin/console cache:warmup

echo "✅ Cache ready!"
echo "🎉 Starting FrankenPHP..."

# Execute FrankenPHP with CMD arguments (like Parraindex)
exec docker-php-entrypoint "$@"
