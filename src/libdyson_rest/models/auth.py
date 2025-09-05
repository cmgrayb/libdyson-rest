"""
Authentication model classes for libdyson-rest.

These models represent the authentication data structures from the Dyson API.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict
from uuid import UUID

from ..types import (
    LoginChallengeResponseDict,
    LoginInformationResponseDict,
    UserStatusResponseDict,
)
from ..validation import safe_get_str, safe_parse_uuid, validate_json_response


class AccountStatus(Enum):
    """User account status enumeration."""

    ACTIVE = "ACTIVE"
    UNREGISTERED = "UNREGISTERED"


class AuthenticationMethod(Enum):
    """Authentication method enumeration."""

    EMAIL_PWD_2FA = (
        "EMAIL_PWD_2FA"  # nosec B105 - This is an enum identifier, not a password
    )


class TokenType(Enum):
    """Token type enumeration."""

    BEARER = "Bearer"


@dataclass
class UserStatus:
    """User account status information."""

    account_status: AccountStatus
    authentication_method: AuthenticationMethod

    @classmethod
    def from_dict(cls, data: UserStatusResponseDict) -> "UserStatus":
        """Create UserStatus instance from dictionary."""
        validated_data = validate_json_response(data, "UserStatus")
        return cls(
            account_status=AccountStatus(safe_get_str(validated_data, "accountStatus")),
            authentication_method=AuthenticationMethod(
                safe_get_str(validated_data, "authenticationMethod")
            ),
        )

    def to_dict(self) -> Dict[str, str]:
        """Convert UserStatus instance to dictionary."""
        return {
            "accountStatus": self.account_status.value,
            "authenticationMethod": self.authentication_method.value,
        }


@dataclass
class LoginChallenge:
    """Login challenge information."""

    challenge_id: UUID

    @classmethod
    def from_dict(cls, data: LoginChallengeResponseDict) -> "LoginChallenge":
        """Create LoginChallenge instance from dictionary."""
        validated_data = validate_json_response(data, "LoginChallenge")
        challenge_id_str = safe_get_str(validated_data, "challengeId")
        return cls(challenge_id=safe_parse_uuid(challenge_id_str, "challengeId"))

    def to_dict(self) -> Dict[str, str]:
        """Convert LoginChallenge instance to dictionary."""
        return {"challengeId": str(self.challenge_id)}


@dataclass
class LoginInformation:
    """Login response information."""

    account: UUID
    token: str
    token_type: TokenType

    @classmethod
    def from_dict(cls, data: LoginInformationResponseDict) -> "LoginInformation":
        """Create LoginInformation instance from dictionary."""
        validated_data = validate_json_response(data, "LoginInformation")
        account_str = safe_get_str(validated_data, "account")
        return cls(
            account=safe_parse_uuid(account_str, "account"),
            token=safe_get_str(validated_data, "token"),
            token_type=TokenType(safe_get_str(validated_data, "tokenType")),
        )

    def to_dict(self) -> Dict[str, str]:
        """Convert LoginInformation instance to dictionary."""
        return {
            "account": str(self.account),
            "token": self.token,
            "tokenType": self.token_type.value,
        }
