"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-11-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_active', sa.DateTime(), nullable=True),
        sa.Column('consent_given', sa.Boolean(), nullable=True),
        sa.Column('data_retention_days', sa.Integer(), nullable=True),
        sa.Column('total_conversations', sa.Integer(), nullable=True),
        sa.Column('total_messages', sa.Integer(), nullable=True),
        sa.Column('crisis_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=True)

    # Create user_metadata table
    op.create_table('user_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('preferred_name', sa.String(length=100), nullable=True),
        sa.Column('extracted_name', sa.String(length=100), nullable=True),
        sa.Column('age_range', sa.String(length=20), nullable=True),
        sa.Column('main_concerns', sa.JSON(), nullable=True),
        sa.Column('conversation_style', sa.String(length=20), nullable=True),
        sa.Column('preferred_language', sa.String(length=10), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('persona_id', sa.String(length=50), nullable=True),
        sa.Column('message_role', sa.String(length=20), nullable=False),
        sa.Column('message_content', sa.Text(), nullable=False),
        sa.Column('emotion_detected', sa.String(length=50), nullable=True),
        sa.Column('crisis_detected', sa.Boolean(), nullable=True),
        sa.Column('crisis_level', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_session_id'), 'conversations', ['session_id'], unique=False)
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)

    # Create assessments table
    op.create_table('assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('assessment_type', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('responses', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessments_user_id'), 'assessments', ['user_id'], unique=False)

    # Create persona_feedback table
    op.create_table('persona_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('persona_id', sa.String(length=50), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('helpful', sa.Boolean(), nullable=True),
        sa.Column('appropriate', sa.Boolean(), nullable=True),
        sa.Column('would_recommend', sa.Boolean(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('concern', sa.String(length=50), nullable=True),
        sa.Column('age_range', sa.String(length=20), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_persona_feedback_persona_id'), 'persona_feedback', ['persona_id'], unique=False)

    # Create persona_performance table
    op.create_table('persona_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('persona_id', sa.String(length=50), nullable=False),
        sa.Column('concern', sa.String(length=50), nullable=True),
        sa.Column('age_range', sa.String(length=20), nullable=True),
        sa.Column('total_sessions', sa.Integer(), nullable=True),
        sa.Column('total_feedback', sa.Integer(), nullable=True),
        sa.Column('avg_rating', sa.Float(), nullable=True),
        sa.Column('helpful_count', sa.Integer(), nullable=True),
        sa.Column('appropriate_count', sa.Integer(), nullable=True),
        sa.Column('recommend_count', sa.Integer(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_persona_performance_persona_id'), 'persona_performance', ['persona_id'], unique=False)

    # Create user_persona_preference table
    op.create_table('user_persona_preference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('persona_id', sa.String(length=50), nullable=False),
        sa.Column('preference_score', sa.Float(), nullable=True),
        sa.Column('interaction_count', sa.Integer(), nullable=True),
        sa.Column('total_duration', sa.Float(), nullable=True),
        sa.Column('last_interaction', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_persona_preference_user_id'), 'user_persona_preference', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_persona_preference_user_id'), table_name='user_persona_preference')
    op.drop_table('user_persona_preference')
    op.drop_index(op.f('ix_persona_performance_persona_id'), table_name='persona_performance')
    op.drop_table('persona_performance')
    op.drop_index(op.f('ix_persona_feedback_persona_id'), table_name='persona_feedback')
    op.drop_table('persona_feedback')
    op.drop_index(op.f('ix_assessments_user_id'), table_name='assessments')
    op.drop_table('assessments')
    op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_session_id'), table_name='conversations')
    op.drop_table('conversations')
    op.drop_table('user_metadata')
    op.drop_index(op.f('ix_users_user_id'), table_name='users')
    op.drop_table('users')
