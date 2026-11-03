FROM php:8.3-cli-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-dev libonig-dev libxml2-dev unzip \
    && docker-php-ext-install pdo_sqlite mbstring dom xml xmlwriter \
    && rm -rf /var/lib/apt/lists/*
COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer
WORKDIR /opt/harness
COPY laravel/composer.json laravel/composer.lock ./
RUN composer install --no-interaction --prefer-dist --no-scripts --no-plugins --no-progress
COPY laravel/ ./
RUN composer dump-autoload --no-scripts --no-plugins \
    && mkdir -p bootstrap/cache storage/framework/views storage/framework/sessions storage/logs \
    && chmod -R a+rX /opt/harness
COPY entrypoint.php /opt/critic-entrypoint.php
USER 10001:10001
ENTRYPOINT ["php", "/opt/critic-entrypoint.php"]
CMD ["reference"]
