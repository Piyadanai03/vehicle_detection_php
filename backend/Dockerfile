FROM php:8.2-cli

RUN apt-get update && apt-get install -y unzip && \
    docker-php-ext-install pdo pdo_mysql

WORKDIR /app
COPY . .

EXPOSE 8000
CMD ["php", "-S", "0.0.0.0:8000", "index.php"]