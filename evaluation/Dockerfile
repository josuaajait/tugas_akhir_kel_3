ARG HARNESS_IMAGE=critic-laravel:dev
FROM ${HARNESS_IMAGE}
ARG SUITE_SHA256
LABEL org.critic.reference-suite-sha256="${SUITE_SHA256}"
COPY phpunit-evaluation.xml /opt/harness/phpunit-evaluation.xml
COPY reference-tests/ /opt/harness/evaluation/
COPY entrypoint.php /opt/critic-evaluation-entrypoint.php
COPY runtime.php /opt/critic-runtime.php
ENTRYPOINT ["php", "/opt/critic-evaluation-entrypoint.php"]
CMD ["evaluation-reference"]
