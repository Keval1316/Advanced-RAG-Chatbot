import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.models.document import Document
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message

# Use an in-memory SQLite database with foreign keys for unit testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_create_user(db):
    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password="fakehashedpassword123",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.email == "testuser@example.com"
    assert user.username == "testuser"
    assert user.is_active is True
    assert user.is_superuser is False


def test_create_knowledge_base_relationship(db):
    user = User(
        email="kb_user@example.com",
        username="kb_user",
        hashed_password="fakehashedpassword123"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    kb = KnowledgeBase(
        name="Enterprise Docs",
        description="Engineering documentation",
        user_id=user.id
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)

    assert kb.id is not None
    assert kb.name == "Enterprise Docs"
    assert kb.user_id == user.id
    assert kb.user.username == "kb_user"
    assert len(user.knowledge_bases) == 1
    assert user.knowledge_bases[0].name == "Enterprise Docs"


def test_create_document_and_cascade(db):
    user = User(
        email="doc_user@example.com",
        username="doc_user",
        hashed_password="fakehashedpassword123"
    )
    db.add(user)
    db.commit()

    kb = KnowledgeBase(
        name="Security Policies",
        user_id=user.id
    )
    db.add(kb)
    db.commit()

    doc = Document(
        filename="security_handbook_v1.pdf",
        original_filename="security_handbook.pdf",
        content_type="application/pdf",
        file_size=102400,
        status="ready",
        chunk_count=15,
        knowledge_base_id=kb.id,
        user_id=user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    assert doc.id is not None
    assert doc.chunk_count == 15
    assert doc.status == "ready"
    assert doc.knowledge_base.name == "Security Policies"

    # Test cascade delete: deleting KB should delete doc
    db.delete(kb)
    db.commit()

    remaining_docs = db.query(Document).filter(Document.id == doc.id).first()
    assert remaining_docs is None


def test_conversation_and_messages_with_citations(db):
    user = User(
        email="chat_user@example.com",
        username="chat_user",
        hashed_password="fakehashedpassword123"
    )
    db.add(user)
    db.commit()

    kb = KnowledgeBase(
        name="Chat KB",
        user_id=user.id
    )
    db.add(kb)
    db.commit()

    conv = Conversation(
        title="Q1 Architecture Discussion",
        user_id=user.id,
        knowledge_base_id=kb.id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    # Add user query message
    msg1 = Message(
        conversation_id=conv.id,
        role="user",
        content="What is the token expiration time?"
    )
    # Add assistant response with citations
    citations = [
        {
            "document_id": str(uuid.uuid4()),
            "document_name": "security_guide.pdf",
            "page_number": 3,
            "chunk_id": "chunk_0"
        }
    ]
    msg2 = Message(
        conversation_id=conv.id,
        role="assistant",
        content="The token expiration time is 24 hours.",
        citations=citations,
        msg_metadata={"route": "direct_qa", "retrieval_attempts": 1}
    )
    db.add_all([msg1, msg2])
    db.commit()

    db.refresh(conv)
    assert len(conv.messages) == 2
    assert conv.messages[0].role == "user"
    assert conv.messages[1].role == "assistant"
    assert len(conv.messages[1].citations) == 1
    assert conv.messages[1].citations[0]["document_name"] == "security_guide.pdf"
    assert conv.messages[1].msg_metadata["route"] == "direct_qa"
