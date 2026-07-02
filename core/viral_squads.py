"""
JobHunt Pro v13 - Viral Squads (Pinduoduo Model)
Implements Chinese-style e-commerce viral growth loops for B2B SaaS.
Users unlock the "$0 AI Video Pitcher" by inviting 3 friends to their squad.
"""

import logging
import uuid

logger = logging.getLogger(__name__)


class ViralSquadManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_squad(self, owner_id: str) -> str:
        """Create a new squad for the user."""
        squad_id = f"squad_{uuid.uuid4().hex[:8]}"
        try:
            self.db.execute(
                "INSERT INTO job_squads (squad_id, owner_id) VALUES (?, ?)",
                (squad_id, owner_id),
            )
            # Update user
            self.db.execute(
                "UPDATE users SET squad_id=? WHERE user_id=?", (squad_id, owner_id)
            )
            self.db.commit()
            return squad_id
        except Exception as e:
            logger.error(f"Failed to create squad: {e}")
            return None

    def join_squad(self, user_id: str, squad_id: str) -> bool:
        """Add a referred user to a squad."""
        try:
            # Check if squad exists and isn't full (e.g. max 4 members)
            squad = self.db.execute(
                "SELECT member_count FROM job_squads WHERE squad_id=?", (squad_id,)
            ).fetchone()
            if not squad:
                return False

            current_count = squad["member_count"]
            if current_count >= 4:
                return False  # Squad full

            # Update member count
            new_count = current_count + 1
            is_complete = new_count >= 4

            self.db.execute(
                "UPDATE job_squads SET member_count=?, is_complete=? WHERE squad_id=?",
                (new_count, is_complete, squad_id),
            )

            # Add user to squad
            self.db.execute(
                "UPDATE users SET squad_id=? WHERE user_id=?", (squad_id, user_id)
            )

            self.db.commit()

            if is_complete:
                logger.info(
                    f"Squad {squad_id} is now complete! Video Pitcher Unlocked for members."
                )

            return True
        except Exception as e:
            logger.error(f"Failed to join squad: {e}")
            return False

    def check_video_pitcher_access(self, user_id: str) -> bool:
        """Check if user has unlocked the AI Video Pitcher via Viral Squad."""
        try:
            user = self.db.execute(
                "SELECT squad_id, subscription_status FROM users WHERE user_id=?",
                (user_id,),
            ).fetchone()
            if not user:
                return False

            if user["subscription_status"] == "premium":
                return True  # Paid users automatically get it

            if user["squad_id"]:
                squad = self.db.execute(
                    "SELECT is_complete FROM job_squads WHERE squad_id=?",
                    (user["squad_id"],),
                ).fetchone()
                if squad and squad["is_complete"]:
                    return True  # Unlocked via viral growth

            return False
        except Exception as e:
            logger.error(f"Error checking access: {e}")
            return False

    def generate_invite_link(
        self, squad_id: str, base_url: str = "https://t.me/JobHuntProBot"
    ) -> str:
        """Generate a Telegram deep link to join the squad."""
        return f"{base_url}?start=squad_{squad_id}"


# Global instance will be injected with db at runtime if needed
