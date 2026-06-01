"""
Pytest configuration and fixtures for integration tests
"""
import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "e2e: end-to-end tests that require the Docker-backed database",
    )
