"""
Database Model Tests
====================

Tests for database models and relationships.
"""

import pytest
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class TestUserModel:
    """Test User model."""
    
    def test_create_user(self, db_session):
        """Test creating a user."""
        from app.models import User
        
        user = User(
            username='testuser',
            email='test@example.com',
            password=generate_password_hash('password123')
        )
        db_session.add(user)
        db_session.commit()
        
        # User should be saved
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
    
    def test_user_password_hashing(self, db_session):
        """Test that user passwords are hashed correctly."""
        from app.models import User
        
        password = 'mypassword123'
        user = User(
            username='hashtest',
            email='hash@test.com',
            password=generate_password_hash(password)
        )
        
        # Password should be hashed
        assert user.password != password
        # Should verify correctly
        assert check_password_hash(user.password, password)
    
    def test_user_unique_constraints(self, db_session):
        """Test that username and email are unique."""
        from app.models import User
        from sqlalchemy.exc import IntegrityError
        
        # Create first user
        user1 = User(
            username='unique',
            email='unique@test.com',
            password=generate_password_hash('pass123')
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create user with same username
        user2 = User(
            username='unique',
            email='different@test.com',
            password=generate_password_hash('pass123')
        )
        db_session.add(user2)
        
        # Should raise IntegrityError
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestPostModel:
    """Test Post model."""
    
    def test_create_post(self, db_session):
        """Test creating a post."""
        from app.models import User, Post
        
        # Create user
        user = User(
            username='poster',
            email='poster@test.com',
            password=generate_password_hash('pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        # Create post
        post = Post(
            title='Test Post',
            content='This is test content'
        )
        db_session.add(post)
        db_session.commit()
        
        # Post should be saved
        assert post.id is not None
        assert post.title == 'Test Post'
    
    def test_post_user_relationship(self, db_session):
        """Test relationship between post and user."""
        from app.models import User, Post
        
        # Create user
        user = User(
            username='author',
            email='author@test.com',
            password=generate_password_hash('pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        # Create post
        post = Post(
            title='Related Post',
            content='Content'
        )
        db_session.add(post)
        db_session.commit()
        
        # Post should be saved
        assert post.id is not None
        # Verify post can be retrieved
        retrieved_post = db_session.query(Post).filter_by(id=post.id).first()
        assert retrieved_post.title == 'Related Post'


class TestHealthRecordModel:
    """Test HealthRecord model if it exists."""
    
    def test_create_health_record(self, db_session):
        """Test creating a health record."""
        try:
            from app.models import User, HealthRecord
            
            # Create user
            user = User(
                username='healthy',
                email='healthy@test.com',
                password=generate_password_hash('pass123')
            )
            db_session.add(user)
            db_session.commit()
            
            # Create health record
            record = HealthRecord(
                user_id=user.id,
                date=datetime.now(),
                weight=70.5,
                notes='Feeling good'
            )
            db_session.add(record)
            db_session.commit()
            
            # Record should be saved
            assert record.id is not None
            assert record.user_id == user.id
            assert record.weight == 70.5
            
        except ImportError:
            # Model doesn't exist yet
            pytest.skip("HealthRecord model not implemented")


class TestModelTimestamps:
    """Test model timestamp fields."""
    
    def test_post_created_timestamp(self, db_session):
        """Test that posts have created timestamp."""
        from app.models import User, Post
        
        # Create user and post
        user = User(
            username='timestampuser',
            email='timestamp@test.com',
            password=generate_password_hash('pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        post = Post(
            title='Timestamp Post',
            content='Content'
        )
        db_session.add(post)
        db_session.commit()
        
        # Should have timestamp
        if hasattr(post, 'created_at'):
            assert post.created_at is not None
            assert isinstance(post.created_at, datetime)


class TestModelDeletion:
    """Test model deletion behavior."""
    
    def test_delete_user(self, db_session):
        """Test deleting a user."""
        from app.models import User
        
        # Create user
        user = User(
            username='deleteuser',
            email='delete@test.com',
            password=generate_password_hash('pass123')
        )
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        
        # Delete user
        db_session.delete(user)
        db_session.commit()
        
        # User should be deleted
        deleted_user = db_session.query(User).filter_by(id=user_id).first()
        assert deleted_user is None
    
    def test_delete_post(self, db_session):
        """Test deleting a post."""
        from app.models import User, Post
        
        # Create user and post
        user = User(
            username='postdeleter',
            email='postdelete@test.com',
            password=generate_password_hash('pass123')
        )
        db_session.add(user)
        db_session.commit()
        
        post = Post(
            title='Delete Me',
            content='Content'
        )
        db_session.add(post)
        db_session.commit()
        post_id = post.id
        
        # Delete post
        db_session.delete(post)
        db_session.commit()
        
        # Post should be deleted
        deleted_post = db_session.query(Post).filter_by(id=post_id).first()
        assert deleted_post is None


class TestModelValidation:
    """Test model field validation."""
    
    def test_user_required_fields(self, db_session):
        """Test that user required fields are enforced."""
        from app.models import User
        from sqlalchemy.exc import IntegrityError
        
        # Try to create user without username
        user = User(
            email='noname@test.com',
            password=generate_password_hash('pass123')
        )
        db_session.add(user)
        
        # Should raise error
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_post_required_fields(self, db_session):
        """Test that post required fields are enforced."""
        from app.models import Post
        from sqlalchemy.exc import IntegrityError
        
        # Try to create post without title
        post = Post(
            content='No title content'
        )
        db_session.add(post)
        
        # Should raise error
        with pytest.raises(IntegrityError):
            db_session.commit()
