FROM dunglas/frankenphp:1-php8.5-alpine

# Install system dependencies and composer
RUN apk add --no-cache \
    git \
    unzip

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /app

# Copy composer files
COPY composer.json composer.lock symfony.lock ./

# Install composer dependencies (production)
RUN composer install --no-dev --no-scripts --no-interaction --optimize-autoloader

# Copy application code
COPY . .

# Run post-install scripts
RUN composer dump-autoload --optimize

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set proper permissions
RUN chown -R www-data:www-data /app/var

# Environment variables for production
ENV APP_ENV=prod
ENV APP_DEBUG=0
ENV SERVER_NAME=:80
ENV FRANKENPHP_CONFIG="worker ./public/index.php"

RUN echo "APP_ENV=prod" >> .env \
    && echo "APP_DEBUG=0" >> .env

# Expose HTTP port
EXPOSE 80

# Use entrypoint and CMD like Parraindex
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
