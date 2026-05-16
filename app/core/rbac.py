"""Role-based access control for NoviKash staff."""

from typing import Set

# Permission keys used across admin API and Next.js admin app
PERMISSIONS = {
    "dashboard.view",
    "users.read",
    "users.write",
    "users.roles",  # change roles (SUPERADMIN only in practice)
    "wallets.read",
    "wallets.credit",
    "wallets.debit",
    "transactions.read",
    "loans.read",
    "loans.manage",
    "loans.novi_verify",
    "kyc.read",
    "kyc.verify",
    "payment_methods.manage",
    "config.manage",
    "notifications.send",
}

ROLE_PERMISSIONS: dict[str, Set[str]] = {
    "SUPERADMIN": PERMISSIONS.copy(),
    "ADMIN": {
        "dashboard.view",
        "users.read",
        "users.write",
        "wallets.read",
        "wallets.credit",
        "wallets.debit",
        "transactions.read",
        "loans.read",
        "loans.manage",
        "loans.novi_verify",
        "kyc.read",
        "kyc.verify",
        "payment_methods.manage",
        "notifications.send",
    },
    "SUPPORT": {
        "dashboard.view",
        "users.read",
        "wallets.read",
        "transactions.read",
        "loans.read",
        "kyc.read",
        "kyc.verify",
    },
    "AUDITOR": {
        "dashboard.view",
        "users.read",
        "wallets.read",
        "transactions.read",
        "loans.read",
        "kyc.read",
    },
}

STAFF_ROLES = frozenset({"SUPERADMIN", "ADMIN", "SUPPORT", "AUDITOR"})


def get_permissions(role: str) -> Set[str]:
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: str, permission: str) -> bool:
    return permission in get_permissions(role)
