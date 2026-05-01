from platforms.benben.auth import BenbenAuthManager


class LoginManager(BenbenAuthManager):
    """Backward-compatible alias for benben auth manager."""


__all__ = ["LoginManager", "BenbenAuthManager"]
