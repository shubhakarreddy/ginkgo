#!/bin/bash
celery -A ginkgo worker -l info &
