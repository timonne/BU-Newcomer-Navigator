"""
Database seeding for local development.

    python seed.py            # create tables if needed, then seed
    python seed.py --reset    # drop everything first, then seed

WHAT IS AND IS NOT OFFICIAL
───────────────────────────
Categories, programmes and tags use exactly the ids the existing frontend
already has in `figma uiux/src/data/categories.ts`, so the backend accepts
and stores the same vocabulary the UI renders.

Everything else here is DEMO CONTENT:
  - demo users have `is_demo=True` and full names prefixed "DEMO"
  - demo questions/answers are ordinary forum posts written for testing
  - knowledge-base entries have `is_demo=True` and their answer text begins
    with an explicit "DEMO DATA — NOT OFFICIAL UNIVERSITY INFORMATION" line

The knowledge-base entries below are deliberately *procedural and generic*:
they describe the general shape of how a university process usually works,
and tell the reader to confirm with the university. They do NOT state
Bennett-specific fees, dates, deadlines, room numbers, phone numbers, email
addresses or policies, because none of that has been verified for this
project. Replace them with real documentation via `POST /api/knowledge`
(or by editing this file) once you have it.

All demo accounts share the password below. It is a well-known development
credential, not a secret, and seeding refuses to run unless
ENVIRONMENT=development.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, SessionLocal, engine

# Importing the models package registers EVERY table on Base.metadata and
# resolves all relationship() targets. Importing only the model modules used
# below would leave conversations/messages out of create_all and break
# User.conversations mapper configuration.
from app import models  # noqa: F401
from app.models.answer import Answer, AnswerStatus
from app.models.category import Category, CategoryType, Tag
from app.models.knowledge import KnowledgeBaseEntry
from app.models.mixins import utcnow
from app.models.question import Question, QuestionStatus
from app.models.user import AccountStatus, AccountType, User, VerificationStatus
from app.models.vote import Vote, VoteTargetType
from app.services.security import hash_password
from app.services.username_service import generate_username

DEMO_PASSWORD = "DemoPassword123"

DEMO_LABEL = "DEMO DATA — NOT OFFICIAL UNIVERSITY INFORMATION"

# ── Categories / programmes / tags ──────────────────────────────────────
# Mirrors figma uiux/src/data/categories.ts. This is a starting list for a
# student project, NOT a claim to be the complete official Bennett University
# programme list — add, rename or remove rows freely.
CATEGORIES = [
    ("btech", "B.Tech", CategoryType.academic, ["CSE", "ECE", "ME", "CE", "EE"]),
    ("bca", "BCA", CategoryType.academic, None),
    ("bsc", "B.Sc", CategoryType.academic, ["Physics", "Chemistry", "Mathematics"]),
    ("bcom", "B.Com", CategoryType.academic, None),
    ("bba", "BBA", CategoryType.academic, None),
    ("mass-comm", "Mass Communication", CategoryType.academic, ["Journalism", "Film & TV", "Advertising"]),
    ("mtech", "M.Tech", CategoryType.academic, ["CSE", "ECE", "ME"]),
    ("mba", "MBA", CategoryType.academic, None),
    ("mca", "MCA", CategoryType.academic, None),
    ("msc", "M.Sc", CategoryType.academic, None),
    ("phd", "PhD", CategoryType.academic, None),
    ("law", "LLB / Law", CategoryType.academic, None),
    ("hostel", "Hostel", CategoryType.non_academic, None),
    ("campus-life", "Campus Life", CategoryType.non_academic, None),
    ("sports", "Sports", CategoryType.non_academic, None),
    ("clubs", "Clubs & Societies", CategoryType.non_academic, None),
    ("events", "Events", CategoryType.non_academic, None),
    ("transport", "Transport", CategoryType.non_academic, None),
    ("food", "Food & Cafeteria", CategoryType.non_academic, None),
    ("facilities", "Facilities", CategoryType.non_academic, None),
    ("general", "General", CategoryType.non_academic, None),
]

TAGS = [
    ("admission", "Admission", "#1E3A8A"),
    ("hostel", "Hostel", "#7C3AED"),
    ("fees", "Fees", "#DC2626"),
    ("library", "Library", "#059669"),
    ("placement", "Placement", "#D97706"),
    ("exam", "Exam", "#DB2777"),
    ("sports", "Sports", "#0891B2"),
    ("coding", "Coding", "#4F46E5"),
    ("clubs", "Clubs", "#65A30D"),
    ("wifi", "Wi-Fi", "#EA580C"),
    ("transport", "Transport", "#0F766E"),
    ("events", "Events", "#9333EA"),
    ("mess", "Mess", "#B45309"),
    ("scholarship", "Scholarship", "#16A34A"),
    ("internship", "Internship", "#1D4ED8"),
    ("faculty", "Faculty", "#BE185D"),
]

# ── Demo users ──────────────────────────────────────────────────────────
DEMO_USERS = [
    # (full_name, email, phone, account_type, verification, course, department, bio, colour)
    (
        "DEMO Timonne Choudhury",
        "timonne.demo@example.com",
        "+91 90000 00001",
        AccountType.student,
        VerificationStatus.verified,
        "B.Tech",
        "CSE",
        "Second-year CSE student. Demo account for local testing.",
        "#1E3A8A",
    ),
    (
        "DEMO Sneha Gupta",
        "sneha.demo@example.com",
        "+91 90000 00002",
        AccountType.student,
        VerificationStatus.pending,
        "MBA",
        None,
        "MBA first year. Demo account for local testing.",
        "#EA580C",
    ),
    (
        "DEMO Arjun Mehta",
        "arjun.demo@example.com",
        "+91 90000 00003",
        AccountType.student,
        VerificationStatus.verified,
        "Mass Communication",
        "Journalism",
        "Final-year Mass Comm student. Demo account for local testing.",
        "#7C3AED",
    ),
    (
        "DEMO Priya Raman",
        "priya.demo@example.com",
        "+91 90000 00004",
        AccountType.staff,
        VerificationStatus.verified,
        None,
        "Student Affairs",
        "Staff demo account — can edit the knowledge base via /api/knowledge.",
        "#059669",
    ),
    (
        "DEMO Rahul Verma",
        "rahul.demo@example.com",
        "+91 90000 00005",
        AccountType.other,
        VerificationStatus.unverified,
        None,
        None,
        "Prospective applicant. Demo account for local testing.",
        "#DB2777",
    ),
]

# ── Demo forum content ──────────────────────────────────────────────────
# (title, body, category_id, tag_ids, author_index, days_ago)
DEMO_QUESTIONS = [
    (
        "How does hostel room allotment usually work for first-year students?",
        "I'm joining this year and I've been assigned hostel accommodation, but I don't "
        "understand the process for getting an actual room. Is it random, is it by "
        "preference, and when do we find out? Any advice from people who went through "
        "it last year would really help.",
        "hostel",
        ["hostel"],
        1,
        9,
    ),
    (
        "What's the best way to get campus Wi-Fi working on a laptop?",
        "I can connect on my phone but my laptop keeps dropping the connection or asking "
        "me to log in again every hour. Is there a setting I'm missing, or is this normal? "
        "Would prefer a fix that survives a reboot.",
        "facilities",
        ["wifi"],
        0,
        7,
    ),
    (
        "Which coding clubs are worth joining as a first-year CSE student?",
        "I want to get into competitive programming and eventually open source. There seem "
        "to be several technical clubs and I can't tell which ones actually meet regularly "
        "versus which are just a WhatsApp group. Honest opinions welcome.",
        "clubs",
        ["clubs", "coding"],
        2,
        5,
    ),
    (
        "How do people usually commute to campus from Delhi on weekends?",
        "My family is in South Delhi and I'd like to go home some weekends. What do people "
        "actually use — the metro plus an auto, a cab, or is there a shuttle? Mainly trying "
        "to understand how long to budget for the trip.",
        "transport",
        ["transport"],
        1,
        4,
    ),
    (
        "Any tips for managing the mess food if you're vegetarian?",
        "I'm a strict vegetarian and slightly worried about variety over a whole semester. "
        "How have other vegetarian students handled this — is there enough choice in the "
        "mess, or do people end up cooking or ordering in a lot?",
        "food",
        ["mess"],
        4,
        3,
    ),
    (
        "When should I start preparing for internship applications?",
        "I'm in my second year and people keep telling me different things about when "
        "placement prep should begin. Is second year too early to start building a resume "
        "and doing projects?",
        "btech",
        ["internship", "placement"],
        0,
        2,
    ),
    (
        "Is there a quiet place to study on campus late in the evening?",
        "The hostel common room gets loud after dinner and I focus much better somewhere "
        "quiet. Looking for suggestions for study spots that are actually usable in the "
        "evening.",
        "campus-life",
        ["library"],
        2,
        1,
    ),
    (
        "How do intra-college sports teams pick players?",
        "I played district-level football in school and would like to continue. Are there "
        "open trials, or do you need to be spotted at inter-house matches first?",
        "sports",
        ["sports"],
        1,
        1,
    ),
]

# (question_index, author_index, body, upvoter_indices, downvoter_indices, is_accepted)
DEMO_ANSWERS = [
    (
        0,
        3,
        "Speaking generally about how these processes tend to run: allotment is usually "
        "handled centrally by the hostel/student affairs office rather than by individual "
        "wardens, and you're normally notified by email or through the student portal "
        "before you arrive. Preferences (like a particular block or a roommate request) are "
        "often collected in advance but not guaranteed.\n\n"
        "Please confirm the current year's exact procedure and timeline with the hostel "
        "office directly — it does change between intakes.",
        [0, 1, 2, 4],
        [],
        True,
    ),
    (
        0,
        0,
        "From my own experience last year: fill in whatever preference form you get as early "
        "as you can, and don't panic if your first allotment isn't ideal — room changes were "
        "possible in the first few weeks once people had settled in.",
        [1, 2],
        [],
        False,
    ),
    (
        1,
        0,
        "The hourly re-login usually means you're on a captive-portal network. Two things "
        "that helped me: save the network as a known/trusted connection rather than "
        "connecting fresh each time, and turn off the 'randomised MAC address' privacy "
        "setting for that specific network — with randomisation on, the portal sees a new "
        "device each time and makes you authenticate again.\n\n"
        "If it still drops, the campus IT helpdesk can register your laptop's MAC address, "
        "which fixes it properly.",
        [1, 2, 4],
        [],
        True,
    ),
    (
        2,
        2,
        "Go to the first two or three meetings of each club before committing to any of them "
        "— attendance at the second meeting tells you far more than the recruitment pitch "
        "does. For competitive programming specifically, look for the group that runs "
        "regular practice contests rather than the one with the biggest membership number.",
        [0, 1],
        [4],
        False,
    ),
    (
        3,
        1,
        "Metro to the nearest station on the line, then an auto or cab for the last stretch, "
        "is what most people I know do. Budget noticeably more time on Friday evenings and "
        "Sunday nights — that's when everyone else is travelling too. Sharing a cab with "
        "others going the same way works out cheaper and is common.",
        [0, 2, 4],
        [],
        True,
    ),
    (
        4,
        4,
        "Vegetarian food is generally the default rather than the exception in most Indian "
        "campus messes, so variety is usually less of a problem than people expect. What "
        "helped me was keeping a kettle and some basics in my room for late nights, and "
        "giving the mess committee actual feedback — they do act on it when enough people "
        "raise the same thing.",
        [0, 1],
        [],
        False,
    ),
    (
        5,
        0,
        "Second year is a good time to start, and not too early at all. Build two or three "
        "projects you can actually explain in depth rather than ten you half-finished, keep "
        "a running list of what you did each semester so resume-writing isn't archaeology "
        "later, and start practising data structures consistently rather than in bursts.",
        [1, 2, 4],
        [],
        True,
    ),
    (
        6,
        2,
        "The library is the obvious answer but it does close — check its actual hours for "
        "this semester. Beyond that, empty classrooms in the academic blocks and the quieter "
        "corners of the cafeteria after peak hours both work well. Ask your block's warden "
        "whether there's a designated late-night study room; several hostels have one.",
        [0, 1],
        [],
        False,
    ),
]

# ── Demo knowledge base ─────────────────────────────────────────────────
# Procedural/generic guidance only. No invented Bennett-specific facts.
DEMO_KB = [
    (
        "How do I get my student ID card?",
        "Student ID cards are normally issued by the administrative or student services "
        "office after enrolment is confirmed and your documents have been verified. You will "
        "usually need a recent photograph and your admission or enrolment reference. If a "
        "card is lost, there is typically a re-issue process through the same office, "
        "sometimes with a replacement fee.\n\n"
        "Check the exact process, location and any fee with the student services office at "
        "Bennett University, Greater Noida.",
        ["id", "card", "identity", "student id", "issue", "replacement", "lost"],
        "Administration",
    ),
    (
        "What is the general process for hostel accommodation?",
        "Hostel accommodation is usually applied for separately from academic admission, "
        "often during or shortly after the admission process. Allotment is typically handled "
        "centrally, with room and block assignments communicated by email or through the "
        "student portal before the term begins. Preference forms (roommate or block "
        "requests) are common but are not always guaranteed.\n\n"
        "Confirm the current year's application window, charges and allotment procedure with "
        "the hostel office at Bennett University, Greater Noida.",
        ["hostel", "accommodation", "room", "allotment", "residence", "warden", "block"],
        "Hostel",
    ),
    (
        "How do I connect to the campus Wi-Fi?",
        "Campus networks are usually accessed with your institutional account credentials "
        "through a captive-portal login. Common problems and their usual causes: repeated "
        "re-login prompts often come from randomised MAC address privacy settings on the "
        "device; complete failure to authenticate often means the account has not been "
        "activated yet. The campus IT helpdesk can register a device or reset network "
        "access.\n\n"
        "For the current network names and helpdesk location, check with campus IT at "
        "Bennett University, Greater Noida.",
        ["wifi", "wi-fi", "internet", "network", "connect", "login", "password", "it"],
        "Facilities",
    ),
    (
        "How does library borrowing usually work?",
        "University libraries generally issue books against your student ID, with a set "
        "number of items and a loan period that differs for undergraduates, postgraduates "
        "and research students. Renewals are often possible online unless another user has "
        "reserved the item, and overdue items usually attract a daily fine. Reference and "
        "reserve collections are commonly library-use-only.\n\n"
        "Confirm borrowing limits, loan periods, opening hours and fine rates with the "
        "library at Bennett University, Greater Noida.",
        ["library", "book", "borrow", "issue", "return", "renew", "fine", "reading"],
        "Library",
    ),
    (
        "Who do I contact about fee payment questions?",
        "Fee questions — payment schedules, accepted payment methods, instalment options, "
        "receipts, refunds and late-payment consequences — are handled by the accounts or "
        "finance office rather than by academic departments. Scholarship and financial-aid "
        "queries are usually handled separately from regular fee collection.\n\n"
        "This system holds no verified fee amounts, deadlines or account details. Contact "
        "the accounts office at Bennett University, Greater Noida for anything authoritative.",
        ["fee", "fees", "payment", "pay", "tuition", "instalment", "refund", "receipt", "accounts"],
        "Fees",
    ),
    (
        "How do students usually join clubs and societies?",
        "Most universities run a recruitment or orientation period near the start of the "
        "academic year, where clubs present themselves and take sign-ups. Technical, "
        "cultural, sports and service clubs typically recruit separately. Some have an "
        "application or audition step; many simply take names and invite you to the first "
        "few meetings.\n\n"
        "For the list of active clubs and their current recruitment timelines, check with "
        "the student activities office at Bennett University, Greater Noida.",
        ["club", "clubs", "society", "societies", "join", "extracurricular", "activities"],
        "Campus Life",
    ),
    (
        "What academic support is usually available if I'm struggling?",
        "Common sources of academic support are faculty office hours, teaching assistants, "
        "peer tutoring or mentoring schemes, and the academic advising office. If difficulty "
        "is related to health or personal circumstances, student counselling services and "
        "the academic office can usually advise on formal options such as deadline "
        "extensions or course adjustments.\n\n"
        "Speak to your academic advisor or the student services office at Bennett "
        "University, Greater Noida to find out what is available to you specifically.",
        ["academic", "support", "help", "struggling", "tutor", "advisor", "failing", "grades"],
        "Academics",
    ),
]


def seed_categories(db: Session) -> None:
    for cid, name, ctype, subs in CATEGORIES:
        if db.query(Category).filter(Category.id == cid).first() is None:
            db.add(Category(id=cid, name=name, type=ctype, subcategories=subs))
    for tid, name, color in TAGS:
        if db.query(Tag).filter(Tag.id == tid).first() is None:
            db.add(Tag(id=tid, name=name, color=color))
    db.commit()
    print(f"  categories: {len(CATEGORIES)}, tags: {len(TAGS)}")


def seed_users(db: Session) -> list[User]:
    users: list[User] = []
    password_hash = hash_password(DEMO_PASSWORD)

    for i, (full_name, email, phone, atype, vstatus, course, dept, bio, color) in enumerate(DEMO_USERS):
        existing = db.query(User).filter(User.email == email).first()
        if existing is not None:
            users.append(existing)
            continue
        user = User(
            full_name=full_name,
            username=generate_username(db, full_name),
            email=email,
            phone=phone,
            account_type=atype,
            verification_status=vstatus,
            account_status=AccountStatus.active,
            password_hash=password_hash,
            course=course,
            department=dept,
            bio=bio,
            avatar_color=color,
            joined_at=date.today() - timedelta(days=200 - i * 20),
            is_demo=True,
        )
        db.add(user)
        db.flush()
        users.append(user)

    db.commit()
    print(f"  demo users: {len(users)} (password for all: {DEMO_PASSWORD})")
    return users


def seed_forum(db: Session, users: list[User]) -> None:
    if db.query(Question).count() > 0:
        print("  forum content already present — skipping")
        return

    questions: list[Question] = []
    for title, body, category_id, tag_ids, author_idx, days_ago in DEMO_QUESTIONS:
        author = users[author_idx]
        q = Question(
            author_id=author.id,
            title=title,
            body=body,
            category_id=category_id,
            course=author.course,
            status=QuestionStatus.open,
            views=17 + days_ago * 6,
            created_at=utcnow() - timedelta(days=days_ago),
            updated_at=utcnow() - timedelta(days=days_ago),
        )
        q.tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        db.add(q)
        db.flush()
        questions.append(q)

    answers: list[Answer] = []
    for q_idx, author_idx, body, upvoters, downvoters, accepted in DEMO_ANSWERS:
        a = Answer(
            question_id=questions[q_idx].id,
            author_id=users[author_idx].id,
            body=body,
            status=AnswerStatus.visible,
            is_accepted=accepted,
        )
        db.add(a)
        db.flush()
        answers.append(a)

        for u in upvoters:
            if users[u].id != a.author_id:
                db.add(
                    Vote(
                        user_id=users[u].id,
                        target_type=VoteTargetType.answer,
                        target_id=a.id,
                        value=1,
                    )
                )
        for u in downvoters:
            if users[u].id != a.author_id:
                db.add(
                    Vote(
                        user_id=users[u].id,
                        target_type=VoteTargetType.answer,
                        target_id=a.id,
                        value=-1,
                    )
                )

    # A few question-level votes so the forum's "most upvoted" sort is
    # visibly different from "latest" straight after seeding.
    for offset, q in enumerate(questions[:5]):
        for u_idx in range(min(4 - (offset % 3), len(users))):
            if users[u_idx].id != q.author_id:
                db.add(
                    Vote(
                        user_id=users[u_idx].id,
                        target_type=VoteTargetType.question,
                        target_id=q.id,
                        value=1,
                    )
                )

    db.commit()
    print(f"  demo questions: {len(questions)}, demo answers: {len(answers)}, votes added")


def seed_knowledge_base(db: Session) -> None:
    added = 0
    for question, answer, keywords, category in DEMO_KB:
        if db.query(KnowledgeBaseEntry).filter(KnowledgeBaseEntry.question == question).first():
            continue
        db.add(
            KnowledgeBaseEntry(
                question=question,
                # The label is part of the stored text so it travels with the
                # content wherever it is displayed, including in chatbot replies.
                answer=f"{DEMO_LABEL}\n\n{answer}",
                keywords=keywords,
                category=category,
                source_type="university",
                is_demo=True,
            )
        )
        added += 1
    db.commit()
    print(f"  knowledge base entries: {added} (all flagged is_demo=True)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Newcomer Navigation database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables before seeding (destroys existing data).",
    )
    args = parser.parse_args()

    settings = get_settings()
    if settings.environment != "development":
        sys.exit(
            f"Refusing to seed: ENVIRONMENT is '{settings.environment}', not 'development'.\n"
            "Seeding inserts demo accounts with a shared, publicly-known password."
        )

    if args.reset:
        confirm = input("This will DELETE all data in the database. Type 'yes' to continue: ")
        if confirm.strip().lower() != "yes":
            sys.exit("Aborted.")
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)

    print("Ensuring tables exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Seeding:")
        seed_categories(db)
        users = seed_users(db)
        seed_forum(db, users)
        seed_knowledge_base(db)
    finally:
        db.close()

    print(
        "\nDone. Sign in with any demo email (e.g. timonne.demo@example.com) or the\n"
        f"generated username (e.g. demo.timonne.choudhury) and password: {DEMO_PASSWORD}\n"
        "\nAll seeded university knowledge-base content is DEMO DATA, not official\n"
        "Bennett University information."
    )


if __name__ == "__main__":
    main()
