# Changelog

All notable changes to the DeepSeek Orchestrator project will be documented in this file.

## [1.0.0-production] - 2026-02-14

### Added
- **Multi-Model Support**: Support for DeepSeek, Llama, and Qwen models via `model_interface.py`.
- **Hot-Swap Configuration**: Orchestrator now reloads configuration and models without restarting.
- **Self-Healing Watchdog**: Added `watchdog` command to `service_manager.sh` to automatically restore crashed services.
- **Production API**: Enhanced `web_api.py` with rate limiting, API key auth, and metrics.
- **AlienPC Ω Mesh Integration**: Added `alienpc_integration.py` for P2P mesh and council governance.
- **Unified Dashboard**: Real-time HTML dashboard for monitoring system health and audit logs.
- **Log Rotation**: Automated log cleanup and archiving via `log_rotation.sh`.
- **Unified Installer**: `install.sh` for one-command setup.

### Fixed
- Improved command extraction from LLM responses.
- Fixed tmux session handling in service manager.

### Security
- Enforced X-API-Key authentication.
- Added Flask-Limiter for API protection.
- Enhanced command validation with dangerous pattern detection.
