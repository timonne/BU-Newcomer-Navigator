"""
Import every model module here so that `Base.metadata` (used by Alembic
autogenerate and by `Base.metadata.create_all` in tests) knows about all
tables. Nothing else should need to import individual model modules by
path -- `from app.models import User, Question, ...` is enough.
"""
from app.database import Base  # noqa: F401

from app.models.user import User, AccountType, VerificationStatus, AccountStatus  # noqa: F401
from app.models.category import Category, Tag, CategoryType, question_tags  # noqa: F401
from app.models.question import Question, QuestionStatus  # noqa: F401
from app.models.answer import Answer, AnswerStatus  # noqa: F401
from app.models.vote import Vote, VoteTargetType  # noqa: F401
from app.models.verification import EmailVerificationToken, PasswordResetToken  # noqa: F401
from app.models.knowledge import KnowledgeBaseEntry  # noqa: F401
from app.models.chat import Conversation, Message  # noqa: F401

__all__ = [
    "Base",
    "User",
    "AccountType",
    "VerificationStatus",
    "AccountStatus",
    "Category",
    "Tag",
    "CategoryType",
    "question_tags",
    "Question",
    "QuestionStatus",
    "Answer",
    "AnswerStatus",
    "Vote",
    "VoteTargetType",
    "EmailVerificationToken",
    "PasswordResetToken",
    "KnowledgeBaseEntry",
    "Conversation",
    "Message",
]