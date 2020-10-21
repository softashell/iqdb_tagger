#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""config for pytest."""


def pytest_configure(config):
    """Configure pytest."""
    plugin = config.pluginmanager.getplugin('mypy')
    plugin.mypy_argv.append('--ignore-missing-imports')
