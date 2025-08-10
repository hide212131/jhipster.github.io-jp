"""Manifest manager for translation meta branch."""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from git_utils import GitUtils
from config import config


class ManifestManager:
    """Manager for translation manifest.json in meta branch."""
    
    def __init__(self, git_utils: Optional[GitUtils] = None):
        """Initialize manifest manager."""
        self.git_utils = git_utils or GitUtils()
        self.meta_branch = config.meta_branch
        self.manifest_file = "manifest.json"
    
    def read_manifest(self) -> Dict[str, Any]:
        """Read manifest from translation-meta branch."""
        try:
            # Try to get manifest content from meta branch
            manifest_content = self.git_utils.get_file_content(
                self.manifest_file, 
                ref=self.meta_branch
            )
            
            if manifest_content:
                return json.loads(manifest_content)
            else:
                # Return empty manifest if file doesn't exist
                return self._create_empty_manifest()
        except Exception as e:
            print(f"Warning: Could not read manifest from {self.meta_branch}: {e}")
            return self._create_empty_manifest()
    
    def write_manifest(self, manifest: Dict[str, Any]) -> bool:
        """Write manifest to translation-meta branch."""
        try:
            # Ensure meta branch exists
            if not self._ensure_meta_branch():
                return False
            
            # Update timestamp
            manifest["last_updated"] = datetime.now().isoformat()
            
            # Convert to JSON string
            manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
            
            # Write to meta branch
            return self.git_utils.write_file_to_branch(
                self.manifest_file,
                manifest_json,
                self.meta_branch,
                "Update translation manifest"
            )
        except Exception as e:
            print(f"Error writing manifest: {e}")
            return False
    
    def update_file_entry(self, file_path: str, upstream_sha: str, strategy: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update or add entry for a specific file."""
        manifest = self.read_manifest()
        
        # Ensure files section exists
        if "files" not in manifest:
            manifest["files"] = {}
        
        # Create/update file entry
        file_entry = {
            "upstream_sha": upstream_sha,
            "strategy": strategy,
            "last_translated": datetime.now().isoformat(),
        }
        
        if metadata:
            file_entry.update(metadata)
        
        manifest["files"][file_path] = file_entry
        
        return self.write_manifest(manifest)
    
    def get_file_upstream_sha(self, file_path: str) -> Optional[str]:
        """Get the upstream SHA for a specific file."""
        manifest = self.read_manifest()
        
        if "files" in manifest and file_path in manifest["files"]:
            return manifest["files"][file_path].get("upstream_sha")
        
        return None
    
    def get_file_strategy(self, file_path: str) -> Optional[str]:
        """Get the translation strategy for a specific file."""
        manifest = self.read_manifest()
        
        if "files" in manifest and file_path in manifest["files"]:
            return manifest["files"][file_path].get("strategy")
        
        return None
    
    def remove_file_entry(self, file_path: str) -> bool:
        """Remove entry for a specific file."""
        manifest = self.read_manifest()
        
        if "files" in manifest and file_path in manifest["files"]:
            del manifest["files"][file_path]
            return self.write_manifest(manifest)
        
        return True  # File not in manifest, nothing to remove
    
    def list_tracked_files(self) -> List[str]:
        """Get list of all tracked files in manifest."""
        manifest = self.read_manifest()
        
        if "files" in manifest:
            return list(manifest["files"].keys())
        
        return []
    
    def get_manifest_summary(self) -> Dict[str, Any]:
        """Get summary information about the manifest."""
        manifest = self.read_manifest()
        
        summary = {
            "version": manifest.get("version", "1.0"),
            "last_updated": manifest.get("last_updated"),
            "total_files": 0,
            "strategies": {}
        }
        
        if "files" in manifest:
            summary["total_files"] = len(manifest["files"])
            
            # Count strategies
            for file_data in manifest["files"].values():
                strategy = file_data.get("strategy", "unknown")
                summary["strategies"][strategy] = summary["strategies"].get(strategy, 0) + 1
        
        return summary
    
    def _create_empty_manifest(self) -> Dict[str, Any]:
        """Create an empty manifest structure."""
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "upstream_repo": config.upstream_repo,
            "meta_branch": self.meta_branch,
            "files": {}
        }
    
    def _ensure_meta_branch(self) -> bool:
        """Ensure translation-meta branch exists."""
        try:
            # Check if branch exists
            if not self.git_utils.branch_exists(self.meta_branch):
                # Create orphan branch for meta data
                return self.git_utils.create_orphan_branch(self.meta_branch)
            return True
        except Exception as e:
            print(f"Error ensuring meta branch: {e}")
            return False