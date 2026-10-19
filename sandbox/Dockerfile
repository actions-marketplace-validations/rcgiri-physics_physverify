# Image for running other people's physics code under physverify. See README.md in this folder.
# Pinned by digest so every run in the study uses the same base.
FROM python@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

# Common scientific stack, so most repositories need no extra installs.
RUN pip install --no-cache-dir numpy==2.3.3 scipy==1.16.2 sympy==1.14.0 matplotlib==3.10.6 pytest==8.4.2

# physverify itself, from the build context (the repository root).
COPY pyproject.toml README.md LICENSE /opt/physverify/
COPY src /opt/physverify/src
RUN pip install --no-cache-dir --no-deps /opt/physverify && rm -rf /opt/physverify

# Unprivileged user with no home to write to; everything writable is a tmpfs or /out.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin runner
ENV MPLBACKEND=Agg PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp \
    PYTHONPATH=/deps
USER runner
WORKDIR /tmp
