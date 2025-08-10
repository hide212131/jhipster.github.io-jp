#!/usr/bin/env python3
"""
Tests for run_sync.py module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.run_sync import SyncRunner
from tools.discover_changes import FileChange


class TestSyncRunner:
    """Test cases for SyncRunner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = SyncRunner(dry_run=True, debug=False)
    
    @patch('tools.run_sync.GitUtils')
    def test_validate_environment_success(self, mock_git_utils):
        """Test successful environment validation."""
        # Mock git repository check
        mock_git_utils.return_value.is_git_repo.return_value = True
        self.runner.git_utils = mock_git_utils.return_value
        
        # Mock dev filter validation
        self.runner.dev_filter.validate_environment = Mock(return_value={
            'git_repo': True,
            'python_version': True,
            'required_packages': True,
            'write_permissions': True
        })
        
        result = self.runner._validate_environment()
        assert result is True
    
    @patch('tools.run_sync.GitUtils')
    def test_validate_environment_not_git_repo(self, mock_git_utils):
        """Test environment validation failure when not in git repo."""
        mock_git_utils.return_value.is_git_repo.return_value = False
        self.runner.git_utils = mock_git_utils.return_value
        
        result = self.runner._validate_environment()
        assert result is False
    
    def test_discover_changes_empty(self):
        """Test change discovery with no changes."""
        self.runner.change_discoverer.discover_changes = Mock(return_value=[])
        
        changes = self.runner._discover_changes('main', 'HEAD')
        assert changes == []
    
    def test_discover_changes_with_files(self):
        """Test change discovery with translatable files."""
        mock_changes = [
            FileChange('docs/test.md', 'modified', 'old content', 'new content'),
            FileChange('src/test.js', 'modified', 'old code', 'new code'),  # Should be filtered out
        ]
        
        self.runner.change_discoverer.discover_changes = Mock(return_value=mock_changes)
        
        changes = self.runner._discover_changes('main', 'HEAD')
        
        # Only the markdown file should be included
        assert len(changes) == 1
        assert changes[0].file_path == 'docs/test.md'
    
    def test_process_translations_success(self):
        """Test successful translation processing."""
        mock_changes = [
            FileChange('docs/test.md', 'modified', 'old', 'Hello world'),
        ]
        
        self.runner.translator.translate_file_content = Mock(return_value='こんにちは世界')
        
        translations = self.runner._process_translations(mock_changes)
        
        assert len(translations) == 1
        assert translations[0] == 'こんにちは世界'
    
    def test_process_translations_deleted_file(self):
        """Test translation processing for deleted files."""
        mock_changes = [
            FileChange('docs/test.md', 'deleted', 'old content', None),
        ]
        
        translations = self.runner._process_translations(mock_changes)
        
        assert len(translations) == 1
        assert translations[0] == ""
    
    def test_perform_dry_run(self):
        """Test dry run functionality."""
        mock_changes = [
            FileChange('docs/test.md', 'modified', 'old', 'new content'),
        ]
        translations = ['translated content']
        
        self.runner.change_applicator.dry_run_changes = Mock(return_value={
            'docs/test.md': {
                'change_type': 'modified',
                'would_write': 18,
                'preview': 'translated content'
            }
        })
        
        # Should not raise any exceptions
        self.runner._perform_dry_run(mock_changes, translations)
        
        # Verify dry_run_changes was called
        self.runner.change_applicator.dry_run_changes.assert_called_once()
    
    def test_apply_changes_validation_error(self):
        """Test change application with validation errors."""
        mock_changes = [
            FileChange('../unsafe/path.md', 'modified', 'old', 'new'),
        ]
        translations = ['translated']
        
        self.runner.change_applicator.validate_changes = Mock(return_value=[
            'Unsafe file path: ../unsafe/path.md'
        ])
        
        result = self.runner._apply_changes(mock_changes, translations)
        assert result is False
    
    def test_apply_changes_success(self):
        """Test successful change application."""
        mock_changes = [
            FileChange('docs/test.md', 'modified', 'old', 'new'),
        ]
        translations = ['translated']
        
        self.runner.change_applicator.validate_changes = Mock(return_value=[])
        self.runner.change_applicator.apply_multiple_changes = Mock(return_value={
            'docs/test.md': True
        })
        
        result = self.runner._apply_changes(mock_changes, translations)
        assert result is True
    
    def test_generate_pr_info(self):
        """Test PR information generation."""
        mock_changes = [
            FileChange('docs/test.md', 'modified', 'old', 'new'),
        ]
        
        self.runner.change_discoverer.get_change_summary = Mock(return_value={
            'modified': 1, 'added': 0, 'deleted': 0
        })
        
        # Mock all PR generator methods
        self.runner.pr_generator.generate_pr_title = Mock(return_value='Test Title')
        self.runner.pr_generator.generate_pr_body = Mock(return_value='Test Body')
        self.runner.pr_generator.generate_commit_message = Mock(return_value='Test Commit')
        self.runner.pr_generator.generate_branch_name = Mock(return_value='test-branch')
        
        # Should not raise any exceptions
        self.runner._generate_pr_info(mock_changes)
        
        # Verify all generator methods were called
        self.runner.pr_generator.generate_pr_title.assert_called_once()
        self.runner.pr_generator.generate_pr_body.assert_called_once()
        self.runner.pr_generator.generate_commit_message.assert_called_once()
        self.runner.pr_generator.generate_branch_name.assert_called_once()


class TestSyncRunnerIntegration:
    """Integration tests for SyncRunner."""
    
    def test_run_sync_dry_run_success(self):
        """Test complete dry run workflow."""
        runner = SyncRunner(dry_run=True, debug=False)
        
        # Mock all dependencies
        runner._validate_environment = Mock(return_value=True)
        runner._discover_changes = Mock(return_value=[
            FileChange('docs/test.md', 'modified', 'old', 'new')
        ])
        runner._process_translations = Mock(return_value=['translated'])
        runner._verify_translations = Mock(return_value={})
        runner._perform_dry_run = Mock()
        runner._generate_pr_info = Mock()
        
        result = runner.run_sync()
        
        assert result is True
        runner._perform_dry_run.assert_called_once()
    
    def test_run_sync_no_changes(self):
        """Test sync with no changes found."""
        runner = SyncRunner(dry_run=True, debug=False)
        
        runner._validate_environment = Mock(return_value=True)
        runner._discover_changes = Mock(return_value=[])
        
        result = runner.run_sync()
        
        assert result is True