import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal, engine, Base
from app.auth.security import hash_password
from app.models.entities import User, Organization, Case, CaseAssignment
from app.models.enums import Role, Department

DEMO_USERS = [
    {
        "email": "lead@police.gov",
        "password": "leadpass123",
        "full_name": "Lead Investigator Roy",
        "role": Role.LEAD_INVESTIGATOR,
        "department": Department.INVESTIGATION,
    },
    {
        "email": "forensic@police.gov",
        "password": "forensicpass123",
        "full_name": "Forensic Officer Chen",
        "role": Role.FORENSIC_OFFICER,
        "department": Department.FORENSIC,
    },
    {
        "email": "financial@police.gov",
        "password": "finpass123",
        "full_name": "Financial Analyst David",
        "role": Role.FINANCIAL_ANALYST,
        "department": Department.FINANCIAL,
    },
    {
        "email": "investigator@police.gov",
        "password": "invpass123",
        "full_name": "Detective Sarah",
        "role": Role.INVESTIGATOR,
        "department": Department.INVESTIGATION,
    },
    {
        "email": "legal@police.gov",
        "password": "legalpass123",
        "full_name": "Hon. Marcus Vance (Legal Reviewer)",
        "role": Role.PROSECUTOR_JUDGE,
        "department": Department.LEGAL,
    },
    {
        "email": "admin@police.gov",
        "password": "adminpass123",
        "full_name": "Chief System Admin",
        "role": Role.ADMIN,
        "department": Department.ADMIN,
    },
]

async def seed_users():
    async with AsyncSessionLocal() as session:
        # 1. Ensure Organization
        res = await session.execute(select(Organization))
        org = res.scalars().first()
        if not org:
            org = Organization(name="Metropolitan Police Department")
            session.add(org)
            await session.flush()
        
        # 2. Add / Update Users
        seeded_users = []
        for u_data in DEMO_USERS:
            stmt = select(User).where(User.email == u_data["email"])
            res = await session.execute(stmt)
            user = res.scalars().first()
            if not user:
                user = User(
                    email=u_data["email"],
                    hashed_password=hash_password(u_data["password"]),
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    department=u_data["department"],
                    organization_id=org.id,
                    is_active=True
                )
                session.add(user)
                await session.flush()
                print(f"Created demo user: {user.email} [{user.role}]")
            else:
                user.hashed_password = hash_password(u_data["password"])
                user.role = u_data["role"]
                user.department = u_data["department"]
                user.is_active = True
                print(f"Updated demo user: {user.email} [{user.role}]")
            seeded_users.append(user)
        
        # 3. Assign all users to all existing cases
        cases_res = await session.execute(select(Case))
        cases = cases_res.scalars().all()
        for case in cases:
            for user in seeded_users:
                # Check existing assignment
                assign_stmt = select(CaseAssignment).where(
                    CaseAssignment.case_id == case.id,
                    CaseAssignment.user_id == user.id
                )
                assign_res = await session.execute(assign_stmt)
                existing_assign = assign_res.scalars().first()
                if not existing_assign:
                    assignment = CaseAssignment(
                        case_id=case.id,
                        user_id=user.id,
                        department=user.department if user.department != Department.ADMIN else Department.INVESTIGATION,
                        assigned_by=user.id,
                        is_active=True
                    )
                    session.add(assignment)
        
        await session.commit()
        print(f"Seeding completed successfully! Seeded {len(seeded_users)} users across {len(cases)} cases.")

if __name__ == "__main__":
    asyncio.run(seed_users())
