"""Seed database with admin user, sample team, and sample repository."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.repository import Repository, RepositoryProvider
from app.models.team import Team, TeamMember, TeamMemberRole
from app.models.user import User, UserRole


def seed() -> None:
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@cra.local").first()
        if not admin:
            admin = User(
                email="admin@cra.local",
                username="admin",
                hashed_password=hash_password("admin12345"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
            )
            db.add(admin)
            db.flush()
            print("Created admin user: admin@cra.local / admin12345")

        demo_user = db.query(User).filter(User.email == "demo@cra.local").first()
        if not demo_user:
            demo_user = User(
                email="demo@cra.local",
                username="demo",
                hashed_password=hash_password("demo12345"),
                full_name="Demo User",
                role=UserRole.USER,
            )
            db.add(demo_user)
            db.flush()
            print("Created demo user: demo@cra.local / demo12345")

        team = db.query(Team).filter(Team.name == "Engineering").first()
        if not team:
            team = Team(name="Engineering", description="Default engineering team")
            db.add(team)
            db.flush()
            db.add(TeamMember(team_id=team.id, user_id=admin.id, role=TeamMemberRole.OWNER))
            db.add(TeamMember(team_id=team.id, user_id=demo_user.id, role=TeamMemberRole.MEMBER))
            print("Created team: Engineering")

        repo = db.query(Repository).filter(Repository.name == "sample-app").first()
        if not repo:
            repo = Repository(
                team_id=team.id,
                name="sample-app",
                url="https://github.com/example/sample-app",
                provider=RepositoryProvider.MANUAL,
                default_branch="main",
                description="Sample repository for testing static analysis",
            )
            db.add(repo)
            print("Created sample repository: sample-app")

        db.commit()
        print("Seed completed successfully.")
    except Exception as exc:
        db.rollback()
        print(f"Seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
