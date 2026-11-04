ARG RESOURCE_IMAGE
FROM ${RESOURCE_IMAGE}
COPY ResourceReferenceTest.php /opt/harness/reference/ResourceReferenceTest.php
COPY profile.json /opt/harness/reference-profile.json
COPY phpunit.xml /opt/harness/phpunit-evaluation.xml
COPY entrypoint.php /opt/critic-resource-reference-entrypoint.php
ARG SUITE_SHA256
LABEL org.critic.reference-suite-sha256="${SUITE_SHA256}"
ENTRYPOINT ["php", "/opt/critic-resource-reference-entrypoint.php"]
CMD ["evaluation-reference"]
