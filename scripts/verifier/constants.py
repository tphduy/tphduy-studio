"""Shared patterns and fixed values that define this repository's conventions."""

import re

NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
NUMBER = r"(?:0|[1-9]\d*)"
PRERELEASE = rf"(?:{NUMBER}|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
VERSION = re.compile(rf"{NUMBER}\.{NUMBER}\.{NUMBER}(?:-{PRERELEASE}(?:\.{PRERELEASE})*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?")
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.S)
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^\n)]*)\)")

MAX_NAME_LENGTH = 64
CODEX = "codex"
CLAUDE = "claude"
CATALOGS = {
    CODEX: ".agents/plugins/marketplace.json",
    CLAUDE: ".claude-plugin/marketplace.json",
}
MANIFESTS = {
    CODEX: "plugin.json",
    CLAUDE: ".claude-plugin/plugin.json",
}
PORTABLE_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PORTABLE_FORBIDDEN_KEYS = ("skills", "mcpServers", "apps", "interface")
INSTALLATION_POLICIES = {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}
AUTHENTICATION_POLICIES = {"ON_INSTALL", "ON_USE"}
SHARED_MANIFEST_FIELDS = ("name", "description", "author", "version", "license")
AUTHORING_PLUGIN = "plugin-dev@claude-plugins-official"
NATIVE_TIMEOUT_SECONDS = 60
