#!/bin/bash


set -e

# 预处理

# 启动Celery
# -l logging 日志级别
# -c 并发能力
celery -A app.worker worker  -l info