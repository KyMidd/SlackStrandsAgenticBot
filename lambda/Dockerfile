# Use AWS Lambda Python runtime as base image for ARM64
FROM public.ecr.aws/lambda/python:3.12-arm64

# Ensure system packages needed to fetch/install uv are present (AL2023 uses dnf)
RUN dnf -y install ca-certificates tar gzip && dnf clean all

# Install uv (installs to /root/.local/bin by default)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh -s --

# Make uv readable and executable by all users
RUN install -m 0755 /root/.local/bin/uv  /usr/local/bin/uv \
    && install -m 0755 /root/.local/bin/uvx /usr/local/bin/uvx

# Put uv/uvx in PATH
ENV PATH="/root/.local/bin:${PATH}"

# Verify uv installation
RUN uvx --version

# Set environment variables
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}"

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    # Clean up to reduce image size
    && find /var/lang/lib/python3.12/site-packages -name "*.pyc" -delete \
    && find /var/lang/lib/python3.12/site-packages -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /var/lang/lib/python3.12/site-packages -name "test*" -exec rm -rf {} + 2>/dev/null || true

# Copy function code
COPY src/*.py ${LAMBDA_TASK_ROOT}/

# Copy PagerDuty MCP server and pre-install dependencies
COPY pagerduty-mcp-server /opt/pagerduty-mcp-server
RUN cd /opt/pagerduty-mcp-server && \
    uv sync --frozen && \
    chmod -R a+rX /opt/pagerduty-mcp-server

# Set the CMD to your handler
CMD ["worker.lambda_handler"]